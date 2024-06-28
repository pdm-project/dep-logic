import pytest

from dep_logic.specifiers import parse_version_specifier


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("===abc", "", "===abc"),
        ("", "===abc", "===abc"),
        ("===abc", "===abc", "===abc"),
        ("===abc", "===def", "<empty>"),
        ("===abc", "<empty>", "<empty>"),
        ("<empty>", "===abc", "<empty>"),
        ("===1.0.0", ">=1", "===1.0.0"),
        ("===1.0.0", "<1", "<empty>"),
    ],
)
def test_arbitrary_intersection(a: str, b: str, expected: str) -> None:
    assert str(parse_version_specifier(a) & parse_version_specifier(b)) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("===abc", "", ""),
        ("", "===abc", ""),
        ("===abc", "===abc", "===abc"),
        ("===abc", "<empty>", "===abc"),
        ("<empty>", "===abc", "===abc"),
        ("===1.0.0", ">=1", ">=1"),
    ],
)
def test_arbitrary_union(a: str, b: str, expected: str) -> None:
    assert str(parse_version_specifier(a) | parse_version_specifier(b)) == expected


@pytest.mark.parametrize(
    "a, b, operand",
    [("===abc", ">=1", "and"), ("===1.0.0", "<1", "or"), ("===abc", "==1.*", "or")],
)
def test_arbitrary_unsupported(a: str, b: str, operand: str) -> None:
    with pytest.raises(ValueError):
        if operand == "and":
            _ = parse_version_specifier(a) & parse_version_specifier(b)
        else:
            _ = parse_version_specifier(a) | parse_version_specifier(b)
