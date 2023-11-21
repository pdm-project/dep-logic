import pytest
from packaging.version import Version

from dep_logic.specifiers import (
    RangeSpecifier,
    UnionSpecifier,
    parse_version_specifier,
)


@pytest.mark.parametrize(
    "spec,parsed",
    [
        (
            "!=1.2.3",
            UnionSpecifier(
                (
                    RangeSpecifier(max=Version("1.2.3")),
                    RangeSpecifier(min=Version("1.2.3")),
                )
            ),
        ),
        (
            "!=1.2.*",
            UnionSpecifier(
                (
                    RangeSpecifier(max=Version("1.2.0")),
                    RangeSpecifier(min=Version("1.3.0"), include_min=True),
                )
            ),
        ),
    ],
)
def test_parse_simple_union_specifier(spec: str, parsed: UnionSpecifier) -> None:
    value = parse_version_specifier(spec)
    assert value.is_simple()
    assert value == parsed
    assert str(value) == spec


@pytest.mark.parametrize(
    "spec,parsed",
    [
        (
            "<3.0||>=3.6",
            UnionSpecifier(
                (
                    RangeSpecifier(max=Version("3.0.0")),
                    RangeSpecifier(min=Version("3.6.0"), include_min=True),
                )
            ),
        ),
        (
            ">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*,!=3.6.*",
            UnionSpecifier(
                (
                    RangeSpecifier(
                        min=Version("2.7.0"), max=Version("3.0.0"), include_min=True
                    ),
                    RangeSpecifier(min=Version("3.7.0"), include_min=True),
                )
            ),
        ),
    ],
)
def test_parse_union_specifier(spec: str, parsed: UnionSpecifier) -> None:
    value = parse_version_specifier(spec)
    assert not value.is_simple()
    assert value == parsed


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("!=2.0", ">=1.0", "~=1.0||>2.0"),
        ("!=2.0", ">=2.0", ">2.0"),
        ("~=2.7||>=3.6", "==3.3", "<empty>"),
        ("~=2.7||>=3.6", "<3.0", "~=2.7"),
        ("~=2.7||==3.7.*", "<2.8||>=3.6", ">=2.7,<2.8||==3.7.*"),
    ],
)
def test_union_intesection(a: str, b: str, expected: str) -> None:
    assert str(parse_version_specifier(a) & parse_version_specifier(b)) == expected


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("!=2.0", ">=1.0", ""),
        ("~=2.7||>=3.6", ">=3.0,<3.3", ">=2.7,<3.3||>=3.6"),
        ("~=2.7||>=3.6", ">=3.1,<3.3", "~=2.7||>=3.1,<3.3||>=3.6"),
        ("~=2.7||>=3.6", ">=3.0,<3.3||==3.4.*", ">=2.7,<3.3||==3.4.*||>=3.6"),
        ("~=2.7||>=3.6", "<empty>", "~=2.7||>=3.6"),
        ("~=2.7||>=3.6", "", ""),
    ],
)
def test_union_union(a: str, b: str, expected: str) -> None:
    assert str(parse_version_specifier(a) | parse_version_specifier(b)) == expected
