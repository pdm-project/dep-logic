from typing import cast

import pytest
from packaging.version import Version

from dep_logic.specifiers import RangeSpecifier, parse_version_specifier


@pytest.mark.parametrize(
    "value,parsed",
    [
        ("", RangeSpecifier()),
        (">2.0.0", RangeSpecifier(min=Version("2.0.0"), include_min=False)),
        (">=2.0.0", RangeSpecifier(min=Version("2.0.0"), include_min=True)),
        ("<2.0.0", RangeSpecifier(max=Version("2.0.0"), include_max=False)),
        ("<=2.0.0", RangeSpecifier(max=Version("2.0.0"), include_max=True)),
        (
            "==2.0.0",
            RangeSpecifier(
                min=Version("2.0.0"),
                max=Version("2.0.0"),
                include_min=True,
                include_max=True,
            ),
        ),
        (
            "==2.0.0a1",
            RangeSpecifier(
                min=Version("2.0.0a1"),
                max=Version("2.0.0a1"),
                include_min=True,
                include_max=True,
            ),
        ),
        (
            "==2.0.*",
            RangeSpecifier(
                min=Version("2.0.0"),
                max=Version("2.1.0"),
                include_min=True,
                include_max=False,
            ),
        ),
        (
            "~=2.0.1",
            RangeSpecifier(
                min=Version("2.0.1"),
                max=Version("2.1.0"),
                include_min=True,
                include_max=False,
            ),
        ),
        (
            "~=2.0.1dev2",
            RangeSpecifier(
                min=Version("2.0.1.dev2"),
                max=Version("2.1.0"),
                include_min=True,
                include_max=False,
            ),
        ),
    ],
)
def test_parse_simple_range(value: str, parsed: RangeSpecifier) -> None:
    spec = parse_version_specifier(value)
    assert spec == parsed
    assert str(spec) == value
    assert spec.is_simple()


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (">2.0.0", ">2.0.0", False),
        (">1.0.0", ">=1.0.1", True),
        ("", ">=2.0.0", True),
        (">=1.0.0", "", False),
        ("<1.0", ">=1.0", True),
        (">=1.0.0", ">1.0.0", True),
        (">1.0.0", ">=1.0.0", False),
        (">=1.0.0", ">=1.0.0", False),
    ],
)
def test_range_compare_lower(a: str, b: str, expected: bool) -> None:
    assert (
        cast(RangeSpecifier, parse_version_specifier(a)).allows_lower(
            cast(RangeSpecifier, parse_version_specifier(b))
        )
        is expected
    )


@pytest.mark.parametrize(
    "value,expected",
    [
        (RangeSpecifier(), ""),
        (RangeSpecifier(min=Version("1.0")), ">1.0"),
        (RangeSpecifier(min=Version("1.0"), include_min=True), ">=1.0"),
        (RangeSpecifier(max=Version("1.0")), "<1.0"),
        (RangeSpecifier(max=Version("1.0")), "<1.0"),
        (
            RangeSpecifier(
                min=Version("1.0"),
                max=Version("1.0"),
                include_min=True,
                include_max=True,
            ),
            "==1.0",
        ),
        (RangeSpecifier(min=Version("1.2"), max=Version("1.4")), ">1.2,<1.4"),
        (
            RangeSpecifier(min=Version("1.2a2"), max=Version("1.4"), include_min=True),
            ">=1.2a2,<1.4",
        ),
        (
            RangeSpecifier(
                min=Version("1.2"),
                max=Version("2"),
                include_min=True,
            ),
            "~=1.2",
        ),
        (
            RangeSpecifier(
                min=Version("1.2r3"),
                max=Version("2"),
                include_min=True,
            ),
            "~=1.2.post3",
        ),
        (
            RangeSpecifier(
                min=Version("1.2"),
                max=Version("2.0post1"),
                include_min=True,
            ),
            "~=1.2",
        ),
        (
            RangeSpecifier(
                min=Version("1.2"),
                max=Version("1!2"),
                include_min=True,
            ),
            ">=1.2,<1!2",
        ),
        (
            RangeSpecifier(
                min=Version("1.2"),
                max=Version("2"),
            ),
            ">1.2,<2",
        ),
        (
            RangeSpecifier(
                min=Version("1.2"),
                max=Version("2"),
                include_min=True,
                include_max=True,
            ),
            ">=1.2,<=2",
        ),
    ],
)
def test_range_str_normalization(value: RangeSpecifier, expected: str) -> None:
    assert str(value) == expected


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("<empty>", ">=1.0", "<empty>"),
        ("<1.0", "<empty>", "<empty>"),
        ("<1.0", ">=1.0", "<empty>"),
        (">=1.0", "<0.5", "<empty>"),
        (">=1.0,<1.5", ">1.5,<2", "<empty>"),
        (">=1.0", ">1.0", ">1.0"),
        (">=1.0,<2", ">=1.0", "~=1.0"),
        ("~=1.2", ">=1.3", "~=1.3"),
        (">=1.2,<1.8", "~=1.3", ">=1.3,<1.8"),
        (">=1.2", "<=1.2", "==1.2"),
    ],
)
def test_range_intersection(a: str, b: str, expected: str) -> None:
    assert str(parse_version_specifier(a) & parse_version_specifier(b)) == expected


@pytest.mark.parametrize(
    "value,inverted",
    [
        ("<empty>", ""),
        (">1.0", "<=1.0"),
        (">=1.0", "<1.0"),
        ("~=1.2", "<1.2||>=2.0"),
        ("==1.2", "!=1.2"),
        ("~=1.2.0", "!=1.2.*"),
        ("<2||>=2.2", ">=2,<2.2"),
        ("<2||>=2.2,<2.4||>=3.0", ">=2,<2.2||~=2.4"),
    ],
)
def test_range_invert(value: str, inverted: str) -> None:
    assert str(~parse_version_specifier(value)) == inverted
    assert str(~parse_version_specifier(inverted)) == value


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("<empty>", ">=1.0", ">=1.0"),
        (">1.0", "<empty>", ">1.0"),
        ("", "==1.0", ""),
        (">=1.0", "<0.6", "<0.6||>=1.0"),
        ("<2.0", "<=1.4", "<2.0"),
        ("==1.4", ">=1,<2", ">=1,<2"),
        (">=1.0,<2", ">=1.8,<2.2", ">=1.0,<2.2"),
        (">=1.0,<2.2", "==2.2", ">=1.0,<=2.2"),
        ("==1.2.*", "==1.4.4", "==1.2.*||==1.4.4"),
        (">=1.2.3", "<1.3", ""),
        ("<1.0", ">1.0", "!=1.0"),
    ],
)
def test_range_union(a: str, b: str, expected: str) -> None:
    assert str(parse_version_specifier(a) | parse_version_specifier(b)) == expected
