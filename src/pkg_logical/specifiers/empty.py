import typing as t

from pkg_logical.specifiers.base import BaseSpecifier, UnparsedVersion


class EmptySpecifier(BaseSpecifier):
    def __invert__(self) -> BaseSpecifier:
        from pkg_logical.specifiers.range import RangeSpecifier

        return RangeSpecifier()

    def __and__(self, other: t.Any) -> BaseSpecifier:
        if not isinstance(other, BaseSpecifier):
            return NotImplemented
        return self

    __rand__ = __and__

    def __or__(self, other: t.Any) -> BaseSpecifier:
        if not isinstance(other, BaseSpecifier):
            return NotImplemented
        return other

    __ror__ = __or__

    def __str__(self) -> str:
        return "<empty>"

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseSpecifier):
            return NotImplemented
        return isinstance(other, EmptySpecifier)

    def contains(
        self, version: UnparsedVersion, prerelease: bool | None = None
    ) -> bool:
        return False

    def to_specifierset(self) -> t.Any:
        raise NotImplementedError("Cannot convert EmptySpecifier to SpecifierSet")
