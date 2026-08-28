import pytest

from dep_logic.markers import parse_marker


@pytest.mark.parametrize(
    ("marker", "expected"),
    [
        ('os_name == "posix"', 'os_name != "posix"'),
        ('os_name != "posix"', 'os_name == "posix"'),
        ('os_name in "posix,nt"', 'os_name not in "posix,nt"'),
        ('os_name not in "posix,nt"', 'os_name in "posix,nt"'),
        ('python_version < "3.10"', 'python_version >= "3.10"'),
        ('python_version <= "3.10"', 'python_version > "3.10"'),
        ('python_version > "3.10"', 'python_version <= "3.10"'),
        ('python_version >= "3.10"', 'python_version < "3.10"'),
        ('"3.10" < python_version', '"3.10" >= python_version'),
    ],
)
def test_invert_marker_expression(marker: str, expected: str) -> None:
    assert str(~parse_marker(marker)) == expected


def test_invert_compatible_release_marker() -> None:
    marker = ~parse_marker('python_version ~= "3.10"')

    assert str(marker) == 'python_version < "3.10" or python_version >= "4.0"'


@pytest.mark.parametrize(
    ("marker", "expected"),
    [
        (
            'os_name == "posix" and sys_platform == "linux"',
            'os_name != "posix" or sys_platform != "linux"',
        ),
        (
            'os_name == "posix" or sys_platform == "linux"',
            'os_name != "posix" and sys_platform != "linux"',
        ),
    ],
)
def test_invert_compound_marker(marker: str, expected: str) -> None:
    assert str(~parse_marker(marker)) == expected


def test_invert_collapsed_single_markers() -> None:
    equality_union = parse_marker('os_name == "posix" or os_name == "nt"')
    inequality_multi = parse_marker('os_name != "posix" and os_name != "nt"')

    assert ~equality_union == inequality_multi
    assert ~inequality_multi == equality_union


def test_invert_any_and_empty_markers() -> None:
    assert (~parse_marker("")).is_empty()
    assert (~parse_marker("<empty>")).is_any()


@pytest.mark.parametrize(
    "marker",
    [
        'os_name == "posix"',
        'python_version ~= "3.10"',
        'python_version == "3.10.*"',
        'os_name == "posix" and sys_platform != "linux"',
        'os_name == "posix" or sys_platform != "linux"',
    ],
)
def test_double_inversion_is_equivalent(marker: str) -> None:
    original = parse_marker(marker)

    assert ~~original == original


def test_arbitrary_marker_cannot_be_inverted() -> None:
    with pytest.raises(ValueError, match="Cannot invert an ArbitrarySpecifier"):
        ~parse_marker('python_version === "3.10-custom"')
