from __future__ import annotations

import itertools
import typing as t
from dataclasses import dataclass, field
from functools import cached_property

from packaging.specifiers import SpecifierSet

from pkg_logical.specifiers.base import BaseSpecifier, UnparsedVersion
from pkg_logical.specifiers.empty import EmptySpecifier
from pkg_logical.specifiers.range import RangeSpecifier
from pkg_logical.utils import first_different_index, pad_zeros


@dataclass(frozen=True, slots=True, unsafe_hash=True, repr=False)
class UnionSpecifier(BaseSpecifier):
    ranges: tuple[RangeSpecifier, ...]
    simplified: str | None = field(default=None, compare=False, hash=False)

    def to_specifierset(self) -> SpecifierSet:
        raise ValueError("Cannot convert UnionSpecifier to SpecifierSet")

    @cached_property
    def _simplified_form(self) -> str | None:
        if self.simplified is not None:
            return self.simplified
        # try to get a not-equals form(!=) if possible
        left, right, *rest = self.ranges
        if rest:
            return None
        match left, right:
            case RangeSpecifier(
                min=None, max=left_max, include_max=False
            ), RangeSpecifier(
                min=right_min, max=None, include_min=False
            ) if left_max == right_min and left_max is not None:
                return f"!={left_max}"
            case RangeSpecifier(
                min=None, max=left_max, include_max=False
            ), RangeSpecifier(
                min=right_min, max=None, include_min=True
            ) if left_max is not None and right_min is not None:
                if left_max.is_prerelease or right_min.is_prerelease:
                    return None
                left_stable = [left_max.epoch, *left_max.release]
                right_stable = [right_min.epoch, *right_min.release]
                max_length = max(len(left_stable), len(right_stable))
                left_stable = pad_zeros(left_stable, max_length)
                right_stable = pad_zeros(right_stable, max_length)
                first_different = first_different_index(left_stable, right_stable)
                if (
                    first_different > 0
                    and right_stable[first_different] - left_stable[first_different]
                    == 1
                    and set(
                        left_stable[first_different + 1 :]
                        + right_stable[first_different + 1 :]
                    )
                    == {0}
                ):
                    epoch = "" if left_max.epoch == 0 else f"{left_max.epoch}!"
                    version = (
                        ".".join(map(str, left_max.release[:first_different])) + ".*"
                    )
                    return f"!={epoch}{version}"
                return None
            case _:
                return None

    def __str__(self) -> str:
        if self._simplified_form is not None:
            return self._simplified_form
        return "||".join(map(str, self.ranges))

    @staticmethod
    def _from_ranges(ranges: t.Sequence[RangeSpecifier]) -> BaseSpecifier:
        match len(ranges):
            case 0:
                return EmptySpecifier()
            case 1:
                return ranges[0]
            case _:
                return UnionSpecifier(tuple(ranges))

    def is_simple(self) -> bool:
        return self._simplified_form is not None

    def contains(
        self, version: UnparsedVersion, prerelease: bool | None = None
    ) -> bool:
        return any(specifier.contains(version, prerelease) for specifier in self.ranges)

    def __invert__(self) -> BaseSpecifier:
        to_union: list[RangeSpecifier] = []
        if (first := self.ranges[0]).min is not None:
            to_union.append(
                RangeSpecifier(max=first.min, include_max=not first.include_min)
            )
        for a, b in zip(self.ranges, self.ranges[1:]):
            to_union.append(
                RangeSpecifier(
                    min=a.max,
                    include_min=not a.include_max,
                    max=b.min,
                    include_max=not b.include_min,
                )
            )
        if (last := self.ranges[-1]).max is not None:
            to_union.append(
                RangeSpecifier(min=last.max, include_min=not last.include_max)
            )
        return self._from_ranges(to_union)

    def __and__(self, other: t.Any) -> BaseSpecifier:
        if isinstance(other, RangeSpecifier):
            if other.is_any():
                return self
            to_intersect: list[RangeSpecifier] = [other]
        elif isinstance(other, UnionSpecifier):
            to_intersect = list(other.ranges)
        else:
            return NotImplemented
        # Expand the ranges to be intersected, and discard the empty ones
        #   (a | b) & (c | d) = (a & c) | (a & d) | (b & c) | (b & d)
        # Since each subrange doesn't overlap with each other and intersection
        # only makes it smaller, so the result is also guaranteed to be a set
        # of non-overlapping ranges, just build a new union from them.
        new_ranges = [
            range
            for (a, b) in itertools.product(self.ranges, to_intersect)
            if not isinstance(range := a & b, EmptySpecifier)
        ]
        return self._from_ranges(new_ranges)

    __rand__ = __and__

    def __or__(self, other: t.Any) -> BaseSpecifier:
        if isinstance(other, RangeSpecifier):
            if other.is_any():
                return other
            new_ranges: list[RangeSpecifier] = []
            ranges = iter(self.ranges)
            for range in ranges:
                if range.can_combine(other):
                    other = t.cast(RangeSpecifier, other | range)
                elif other.allows_lower(range):
                    # all following ranges are higher than the input, quit the loop
                    # and copy the rest ranges.
                    new_ranges.extend([other, range, *ranges])
                    break
                else:
                    # range is strictly lower than other, nothing to do here
                    new_ranges.append(range)
            else:
                # we have consumed all ranges or no range is merged,
                # just append to the last.
                new_ranges.append(other)
            return self._from_ranges(new_ranges)
        elif isinstance(other, UnionSpecifier):
            result = self
            for range in other.ranges:
                result = result | range
            return result
        else:
            return NotImplemented

    __ror__ = __or__
