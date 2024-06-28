from dataclasses import dataclass


class Os:
    def __str__(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True)
class Manylinux(Os):
    major: int
    minor: int


@dataclass(frozen=True)
class Musllinux(Os):
    major: int
    minor: int


@dataclass(frozen=True)
class Windows(Os):
    pass


@dataclass(frozen=True)
class Macos(Os):
    major: int
    minor: int


@dataclass(frozen=True)
class FreeBsd(Os):
    release: str


@dataclass(frozen=True)
class NetBsd(Os):
    release: str


@dataclass(frozen=True)
class OpenBsd(Os):
    release: str


@dataclass(frozen=True)
class Dragonfly(Os):
    release: str


@dataclass(frozen=True)
class Illumos(Os):
    release: str
    arch: str


@dataclass(frozen=True)
class Haiku(Os):
    release: str
