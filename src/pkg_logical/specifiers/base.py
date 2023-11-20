from __future__ import annotations

import abc
import typing as t

from packaging.specifiers import SpecifierSet
from packaging.version import Version

UnparsedVersion = t.Union[Version, str]


class BaseSpecifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __str__(self) -> str:
        """
        Returns the str representation of this Specifier-like object. This
        should be representative of the Specifier itself.
        """

    @abc.abstractmethod
    def __hash__(self) -> int:
        """
        Returns a hash value for this Specifier-like object.
        """

    @abc.abstractmethod
    def __eq__(self, other: object) -> bool:
        """
        Returns a boolean representing whether or not the two Specifier-like
        objects are equal.

        :param other: The other object to check against.
        """

    @abc.abstractmethod
    def __and__(self, other: t.Any) -> BaseSpecifier:
        raise NotImplementedError

    @abc.abstractmethod
    def __or__(self, other: t.Any) -> BaseSpecifier:
        raise NotImplementedError

    @abc.abstractmethod
    def __invert__(self) -> BaseSpecifier:
        raise NotImplementedError

    @abc.abstractmethod
    def contains(
        self, version: UnparsedVersion, prerelease: bool | None = None
    ) -> bool:
        raise NotImplementedError

    def __contains__(self, version: UnparsedVersion) -> bool:
        return self.contains(version)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self}>"

    @abc.abstractmethod
    def to_specifierset(self) -> SpecifierSet:
        """Convert to a packaging.specifiers.SpecifierSet object."""
        raise NotImplementedError

    def is_simple(self) -> bool:
        return False
