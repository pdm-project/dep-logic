from __future__ import annotations

from dataclasses import dataclass
from platform import python_implementation, python_version
from typing import TYPE_CHECKING

from ..specifiers import InvalidSpecifier, VersionSpecifier, parse_version_specifier
from .platform import Platform

if TYPE_CHECKING:
    from typing import Literal, Self


def parse_wheel_tags(filename: str) -> tuple[list[str], list[str], list[str]]:
    if not filename.endswith(".whl"):
        raise InvalidWheelFilename(
            f"Invalid wheel filename (extension must be '.whl'): {filename}"
        )

    filename = filename[:-4]
    dashes = filename.count("-")
    if dashes not in (4, 5):
        raise InvalidWheelFilename(
            f"Invalid wheel filename (wrong number of parts): {filename}"
        )

    parts = filename.split("-")
    python, abi, platform = parts[-3:]
    return python.split("."), abi.split("."), platform.split(".")


def _ensure_version_specifier(spec: str) -> VersionSpecifier:
    parsed = parse_version_specifier(spec)
    if not isinstance(parsed, VersionSpecifier):
        raise InvalidSpecifier(f"Invalid version specifier {spec}")
    return parsed


class TagsError(Exception):
    pass


class InvalidWheelFilename(TagsError, ValueError):
    pass


class UnsupportedImplementation(TagsError, ValueError):
    pass


@dataclass(frozen=True)
class Implementation:
    name: Literal["cpython", "pypy", "pyston"]
    gil_disabled: bool = False

    @property
    def short(self) -> str:
        if self.name == "cpython":
            return "cp"
        elif self.name == "pypy":
            return "pp"
        else:
            return "pt"

    @classmethod
    def current(cls) -> Self:
        import sysconfig

        implementation = python_implementation()

        return cls.parse(
            implementation.lower(), sysconfig.get_config_var("Py_GIL_DISABLED") or False
        )

    @classmethod
    def parse(cls, name: str, gil_disabled: bool = False) -> Self:
        if gil_disabled and name != "cpython":
            raise UnsupportedImplementation("Only CPython supports GIL disabled mode")
        if name in ("cpython", "pypy", "pyston"):
            return cls(name, gil_disabled)
        else:
            raise UnsupportedImplementation(
                f"Unsupported implementation: {name}, expected cpython, pypy, or pyston"
            )


@dataclass(frozen=True)
class EnvSpec:
    requires_python: VersionSpecifier
    platform: Platform
    implementation: Implementation

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "requires_python": str(self.requires_python),
            "platform": str(self.platform),
            "implementation": self.implementation.name,
            "gil_disabled": self.implementation.gil_disabled,
        }

    @classmethod
    def from_spec(
        cls,
        requires_python: str,
        platform: str,
        implementation: str = "cpython",
        gil_disabled: bool = False,
    ) -> Self:
        return cls(
            _ensure_version_specifier(requires_python),
            Platform.parse(platform),
            Implementation.parse(implementation, gil_disabled=gil_disabled),
        )

    @classmethod
    def current(cls) -> Self:
        requires_python = _ensure_version_specifier(f"=={python_version()}")
        platform = Platform.current()
        implementation = Implementation.current()
        return cls(requires_python, platform, implementation)

    def _evaluate_python(
        self, python_tag: str, abi_tag: str
    ) -> tuple[int, int, int] | None:
        impl, major, minor = python_tag[:2], python_tag[2], python_tag[3:]
        if impl not in [self.implementation.short, "py"]:
            return None
        abi_impl = (
            abi_tag.split("_", 1)[0]
            .replace("pypy", "pp")
            .replace("pyston", "pt")
            .lower()
        )
        if impl == "cp" and abi_impl == "abi3":
            if (
                parse_version_specifier(f">={major}.{minor or 0}")
                & self.requires_python
            ).is_empty():
                return None
            return (int(major), int(minor or 0), 1)  # 1 for abi3
        # cp36-cp36m-*
        # cp312-cp312m-*
        # pp310-pypy310_pp75-*
        if abi_impl != "none" and not abi_impl.startswith(python_tag.lower()):
            return None
        if major and minor:
            wheel_range = parse_version_specifier(f"=={major}.{minor}.*")
        else:
            wheel_range = parse_version_specifier(f"=={major}.*")
        if (wheel_range & self.requires_python).is_empty():
            return None
        return (int(major), int(minor or 0), 0 if abi_impl == "none" else 2)

    def _evaluate_platform(self, platform_tag: str) -> int | None:
        platform_tags = [*self.platform.compatible_tags, "any"]
        if platform_tag not in platform_tags:
            return None
        return len(platform_tags) - platform_tags.index(platform_tag)

    def compatibility(
        self,
        wheel_python_tags: list[str],
        wheel_abi_tags: list[str],
        wheel_platform_tags: list[str],
    ) -> tuple[int, int, int, int] | None:
        python_abi_combinations = (
            (python_tag, abi_tag)
            for python_tag in wheel_python_tags
            for abi_tag in wheel_abi_tags
        )
        python_compat = max(
            filter(
                None, (self._evaluate_python(*comb) for comb in python_abi_combinations)
            ),
            default=None,
        )
        if python_compat is None:
            return None
        platform_compat = max(
            filter(None, map(self._evaluate_platform, wheel_platform_tags)),
            default=None,
        )
        if platform_compat is None:
            return None
        return (*python_compat, platform_compat)

    def wheel_compatibility(
        self, wheel_filename: str
    ) -> tuple[int, int, int, int] | None:
        wheel_python_tags, wheel_abi_tags, wheel_platform_tags = parse_wheel_tags(
            wheel_filename
        )
        return self.compatibility(
            wheel_python_tags, wheel_abi_tags, wheel_platform_tags
        )

    def markers(self) -> dict[str, str]:
        return {
            "implementation_name": self.implementation.name,
            **self.platform.markers(),
        }
