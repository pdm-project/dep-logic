# Abstractions for understanding the current platform (operating system and architecture).
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING

from . import os

if TYPE_CHECKING:
    from typing import Self


class PlatformError(Exception):
    pass


_platform_major_minor_re = re.compile(
    r"(?P<os>manylinux|macos|musllinux)_(?P<major>\d+?)_(?P<minor>\d+?)_(?P<arch>[a-z0-9_]+)$"
)


@dataclass(frozen=True)
class Platform:
    os: os.Os
    arch: Arch

    @classmethod
    def parse(cls, platform: str) -> Self:
        """Parse a platform string (e.g., `linux_x86_64`, `macosx_10_9_x86_64`, or `win_amd64`)

        Available operating systems:
        - `linux`: an alias for `manylinux_2_17_x86_64`
        - `windows`: an alias for `win_amd64`
        - `macos`: an alias for `macos_12_0_arm64`
        - `alpine`: an alias for `musllinux_1_2_x86_64`
        - `windows_amd64`
        - `windows_x86`
        - `windows_arm64`
        - `macos_arm64`: an alias for `macos_12_0_arm64`
        - `macos_x86_64`: an alias for `macos_12_0_x86_64`
        - `macos_X_Y_arm64`
        - `macos_X_Y_x86_64`
        - `manylinux_X_Y_x86_64`
        - `manylinux_X_Y_aarch64`
        - `musllinux_X_Y_x86_64`
        - `musllinux_X_Y_aarch64`
        """
        if platform == "linux":
            return cls(os.Manylinux(2, 17), Arch.X86_64)
        elif platform == "windows":
            return cls(os.Windows(), Arch.X86_64)
        elif platform == "macos":
            return cls(os.Macos(12, 0), Arch.Aarch64)
        elif platform == "alpine":
            return cls(os.Musllinux(1, 2), Arch.X86_64)
        elif platform.startswith("windows_"):
            return cls(os.Windows(), Arch.parse(platform.split("_", 1)[1]))
        elif platform == "macos_arm64":
            return cls(os.Macos(12, 0), Arch.Aarch64)
        elif platform == "macos_x86_64":
            return cls(os.Macos(12, 0), Arch.X86_64)
        elif (m := _platform_major_minor_re.match(platform)) is not None:
            os_name, major, minor, arch = m.groups()
            if os_name == "manylinux":
                return cls(os.Manylinux(int(major), int(minor)), Arch.parse(arch))
            elif os_name == "macos":
                return cls(os.Macos(int(major), int(minor)), Arch.parse(arch))
            else:  # os_name == "musllinux"
                return cls(os.Musllinux(int(major), int(minor)), Arch.parse(arch))
        else:
            raise PlatformError(
                f"Unsupported platform {platform}, expected one of {cls.choices()}"
            )

    def __str__(self) -> str:
        if isinstance(self.os, os.Windows) and self.arch == Arch.X86_64:
            return "windows_amd64"
        if isinstance(self.os, (os.Macos, os.Windows)) and self.arch == Arch.Aarch64:
            return f"{self.os}_arm64"
        return f"{self.os}_{self.arch}"

    @classmethod
    def current(cls) -> Self:
        """Return the current platform."""
        import platform

        system = platform.system()
        arch = Arch.parse(platform.machine())
        if system == "Linux":
            libc_ver = platform.libc_ver()[1]
            if libc_ver:
                parts = libc_ver.split(".")
                return cls(os.Manylinux(int(parts[0]), int(parts[1])), arch)
            else:  # musl
                from packaging._musllinux import _get_musl_version

                musl_version = _get_musl_version(sys.executable)
                if musl_version is None:
                    raise PlatformError(
                        "Failed to detect musl version or glibc version"
                    )
                return cls(os.Musllinux(musl_version.major, musl_version.minor), arch)
        elif system == "Windows":
            return cls(os.Windows(), arch)
        elif system == "Darwin":
            mac_ver = platform.mac_ver()[0].split(".")
            return cls(os.Macos(int(mac_ver[0]), int(mac_ver[1])), arch)
        else:
            raise PlatformError("Unsupported platform")

    @classmethod
    def choices(cls) -> list[str]:
        return [
            "linux",
            "windows",
            "macos",
            "alpine",
            "windows_amd64",
            "windows_x86",
            "windows_arm64",
            "macos_arm64",
            "macos_x86_64",
            "macos_X_Y_arm64",
            "macos_X_Y_x86_64",
            "manylinux_X_Y_x86_64",
            "manylinux_X_Y_aarch64",
            "musllinux_X_Y_x86_64",
            "musllinux_X_Y_aarch64",
        ]

    @cached_property
    def compatible_tags(self) -> list[str]:
        """Returns the compatible tags for the current [`Platform`] (e.g., `manylinux_2_17`,
        `macosx_11_0_arm64`, or `win_amd64`).

        We have two cases: Actual platform specific tags (including "merged" tags such as universal2)
        and "any".

        Bit of a mess, needs to be cleaned up.
        """
        os_ = self.os
        arch = self.arch
        platform_tags: list[str] = []
        if isinstance(os_, os.Manylinux):
            if (min_minor := arch.get_minimum_manylinux_minor()) is not None:
                for minor in range(os_.minor, min_minor - 1, -1):
                    platform_tags.append(f"manylinux_{os_.major}_{minor}_{arch}")
                    # Support legacy manylinux tags with lower priority
                    # <https://peps.python.org/pep-0600/#legacy-manylinux-tags>
                    if minor == 12:
                        platform_tags.append(f"manylinux2010_{arch}")
                    if minor == 17:
                        platform_tags.append(f"manylinux2014_{arch}")
                    if minor == 5:
                        platform_tags.append(f"manylinux1_{arch}")
            # Non-manylinux is lowest priority
            # <https://github.com/pypa/packaging/blob/fd4f11139d1c884a637be8aa26bb60a31fbc9411/packaging/tags.py#L444>
            platform_tags.append(f"linux_{arch}")
        elif isinstance(os_, os.Musllinux):
            platform_tags.append(f"linux_{arch}")
            for minor in range(1, os_.minor + 1):
                # musl 1.1 is the lowest supported version in musllinux
                platform_tags.append(f"musllinux_{os_.major}_{minor}_{arch}")
        elif isinstance(os_, os.Macos) and arch == Arch.X86_64:
            if os_.major == 10:
                for minor in range(os_.minor, 3, -1):
                    for binary_format in arch.get_mac_binary_formats():
                        platform_tags.append(f"macosx_10_{minor}_{binary_format}")
            elif isinstance(os_.major, int) and os_.major >= 11:
                # Starting with Mac OS 11, each yearly release bumps the major version number.
                # The minor versions are now the midyear updates.
                for major in range(os_.major, 10, -1):
                    for binary_format in arch.get_mac_binary_formats():
                        platform_tags.append(f"macosx_{major}_0_{binary_format}")
                # The "universal2" binary format can have a macOS version earlier than 11.0
                # when the x86_64 part of the binary supports that version of macOS.
                for minor in range(16, 3, -1):
                    for binary_format in arch.get_mac_binary_formats():
                        platform_tags.append(f"macosx_10_{minor}_{binary_format}")
            else:
                raise PlatformError(f"Unsupported macOS version {os_.major}")
        elif isinstance(os_, os.Macos) and arch == Arch.Aarch64:
            # Starting with Mac OS 11, each yearly release bumps the major version number.
            # The minor versions are now the midyear updates.
            for major in range(os_.major, 10, -1):
                for binary_format in arch.get_mac_binary_formats():
                    platform_tags.append(f"macosx_{major}_0_{binary_format}")
            # The "universal2" binary format can have a macOS version earlier than 11.0
            # when the x86_64 part of the binary supports that version of macOS.
            for minor in range(16, 3, -1):
                platform_tags.append(f"macosx_10_{minor}_universal2")
        elif isinstance(os_, os.Windows):
            if arch == Arch.X86:
                platform_tags.append("win32")
            elif arch == Arch.X86_64:
                platform_tags.append("win_amd64")
            elif arch == Arch.Aarch64:
                platform_tags.append("win_arm64")
            else:
                raise PlatformError(f"Unsupported Windows architecture {arch}")
        elif isinstance(
            os_, (os.FreeBsd, os.NetBsd, os.OpenBsd, os.Dragonfly, os.Haiku)
        ):
            release = os_.release.replace(".", "_").replace("-", "_")
            platform_tags.append(f"{str(os_).lower()}_{release}_{arch}")
        elif isinstance(os_, os.Illumos):
            # See https://github.com/python/cpython/blob/46c8d915715aa2bd4d697482aa051fe974d440e1/Lib/sysconfig.py#L722-L730
            try:
                major, other = os_.release.split("_", 1)
            except ValueError:
                platform_tags.append(f"{str(os_).lower()}_{os_.release}_{arch}")
            else:
                major_ver = int(major)
                if major_ver >= 5:
                    # SunOS 5 == Solaris 2
                    release = f"{major_ver - 3}_{other}"
                    arch = f"{arch}_64bit"
                    platform_tags.append(f"solaris_{release}_{arch}")
        else:
            raise PlatformError(
                f"Unsupported operating system and architecture combination: {os_} {arch}"
            )
        return platform_tags

    @cached_property
    def os_name(self) -> str:
        return "nt" if isinstance(self.os, os.Windows) else "posix"

    @cached_property
    def sys_platform(self) -> str:
        if isinstance(self.os, os.Windows):
            return "win32"
        elif isinstance(self.os, (os.Macos, os.Illumos)):
            return "darwin"
        else:
            return "linux"

    @cached_property
    def platform_machine(self) -> str:
        if isinstance(self.os, (os.Windows, os.Macos)) and self.arch == Arch.Aarch64:
            return "arm64"
        if isinstance(self.os, os.Windows) and self.arch == Arch.X86_64:
            return "AMD64"
        return str(self.arch)

    @cached_property
    def platform_release(self) -> str:
        return ""

    @cached_property
    def platform_version(self) -> str:
        return ""

    @cached_property
    def platform_system(self) -> str:
        if isinstance(self.os, os.Macos):
            return "Darwin"
        if isinstance(self.os, os.Windows):
            return "Windows"
        return "Linux"

    def is_current(self) -> bool:
        current = self.current()
        return isinstance(self.os, type(current.os)) and self.arch == current.arch

    def markers(self) -> dict[str, str]:
        if self.is_current():
            return {}
        return {
            "os_name": self.os_name,
            "platform_machine": self.platform_machine,
            "platform_release": self.platform_release,
            "platform_system": self.platform_system,
            "platform_version": self.platform_version,
            "sys_platform": self.sys_platform,
        }


class Arch(Enum):
    Aarch64 = "aarch64"
    Armv6L = "armv6l"
    Armv7L = "armv7l"
    Powerpc64Le = "ppc64le"
    Powerpc64 = "ppc64"
    X86 = "x86"
    X86_64 = "x86_64"
    S390X = "s390x"

    def __str__(self) -> str:
        return self.value

    def get_minimum_manylinux_minor(self) -> int | None:
        if self in [
            Arch.Aarch64,
            Arch.Armv7L,
            Arch.Powerpc64,
            Arch.Powerpc64Le,
            Arch.S390X,
        ]:
            return 17
        elif self in [Arch.X86, Arch.X86_64]:
            return 5
        else:
            return None

    def get_mac_binary_formats(self) -> list[str]:
        if self == Arch.Aarch64:
            formats = ["arm64"]
        else:
            formats = [self.value]

        if self == Arch.X86_64:
            formats.extend(["intel", "fat64", "fat32"])

        if self in [Arch.X86_64, Arch.Aarch64]:
            formats.append("universal2")

        if self == Arch.X86_64:
            formats.append("universal")

        return formats

    @classmethod
    def parse(cls, arch: str) -> Arch:
        if arch in ("i386", "i686"):
            return cls.X86
        if arch == "amd64":
            return cls.X86_64
        if arch == "arm64":
            return cls.Aarch64
        return cls(arch)
