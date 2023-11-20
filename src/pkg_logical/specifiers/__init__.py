from __future__ import annotations

import functools
import itertools
import operator

from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

from pkg_logical.specifiers.base import BaseSpecifier
from pkg_logical.specifiers.empty import EmptySpecifier
from pkg_logical.specifiers.range import RangeSpecifier
from pkg_logical.specifiers.union import UnionSpecifier
from pkg_logical.utils import is_not_suffix, version_split


def from_specifierset(spec: SpecifierSet) -> BaseSpecifier:
    """Convert from a packaging.specifiers.SpecifierSet object."""

    return functools.reduce(
        operator.and_, map(_from_pkg_specifier, spec), RangeSpecifier()
    )


def _from_pkg_specifier(spec: Specifier) -> BaseSpecifier:
    version = spec.version
    min: Version | None = None
    max: Version | None = None
    include_min = False
    include_max = False
    match spec.operator:
        case ">" | ">=":
            min = Version(version)
            include_min = spec.operator == ">="
        case "<" | "<=":
            max = Version(version)
            include_max = spec.operator == "<="
        case "==":
            if "*" not in version:
                min = Version(version)
                max = Version(version)
                include_min = True
                include_max = True
            else:
                version_parts = list(
                    itertools.takewhile(lambda x: x != "*", version_split(version))
                )
                min = Version(".".join([*version_parts, "0"]))
                version_parts[-1] = str(int(version_parts[-1]) + 1)
                max = Version(".".join([*version_parts, "0"]))
                include_min = True
                include_max = False
        case "~=":
            min = Version(version)
            version_parts = list(
                itertools.takewhile(is_not_suffix, version_split(version))
            )[:-1]
            version_parts[-1] = str(int(version_parts[-1]) + 1)
            max = Version(".".join([*version_parts, "0"]))
            include_min = True
            include_max = False
        case "!=":
            if "*" not in version:
                v = Version(version)
                return UnionSpecifier(
                    (
                        RangeSpecifier(max=v, include_max=False),
                        RangeSpecifier(min=v, include_min=False),
                    ),
                    simplified=str(spec),
                )
            else:
                version_parts = list(
                    itertools.takewhile(lambda x: x != "*", version_split(version))
                )
                left = Version(".".join([*version_parts, "0"]))
                version_parts[-1] = str(int(version_parts[-1]) + 1)
                right = Version(".".join([*version_parts, "0"]))
                return UnionSpecifier(
                    (
                        RangeSpecifier(max=left, include_max=False),
                        RangeSpecifier(min=right, include_min=True),
                    ),
                    simplified=str(spec),
                )
        case op:
            raise ValueError(f'Unsupported operator "{op}" in specifier "{spec}"')
    return RangeSpecifier(
        min=min,
        max=max,
        include_min=include_min,
        include_max=include_max,
        simplified=str(spec),
    )


def parse(spec: str) -> BaseSpecifier:
    """Parse a specifier string."""
    if spec == "<empty>":
        return EmptySpecifier()
    if "||" in spec:
        return functools.reduce(operator.or_, map(parse, spec.split("||")))
    return from_specifierset(SpecifierSet(spec))


__all__ = [
    "from_specifierset",
    "parse",
    "BaseSpecifier",
    "EmptySpecifier",
    "RangeSpecifier",
    "UnionSpecifier",
]
