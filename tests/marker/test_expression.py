import pytest

from dep_logic.markers import parse_marker


def test_single_marker_normalisation() -> None:
    m1 = parse_marker("python_version>='3.6'")
    m2 = parse_marker("python_version >= '3.6'")
    assert m1 == m2
    assert hash(m1) == hash(m2)


def test_single_marker_intersect() -> None:
    m = parse_marker('sys_platform == "darwin"')

    intersection = m & parse_marker('implementation_name == "cpython"')
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and implementation_name == "cpython"'
    )

    m = parse_marker('python_version >= "3.4"')

    intersection = m & parse_marker('python_version < "3.6"')
    assert str(intersection) == 'python_version >= "3.4" and python_version < "3.6"'


def test_single_marker_intersect_compacts_constraints() -> None:
    m = parse_marker('python_version < "3.6"')

    intersection = m & parse_marker('python_version < "3.4"')
    assert str(intersection) == 'python_version < "3.4"'


def test_single_marker_intersect_with_multi() -> None:
    m = parse_marker('sys_platform == "darwin"')

    intersection = m & (
        parse_marker('implementation_name == "cpython" and python_version >= "3.6"')
    )
    assert (
        str(intersection)
        == 'implementation_name == "cpython" and python_version >= "3.6" and'
        ' sys_platform == "darwin"'
    )


def test_single_marker_intersect_with_multi_with_duplicate() -> None:
    m = parse_marker('python_version < "4.0"')

    intersection = m & (
        parse_marker('sys_platform == "darwin" and python_version < "4.0"')
    )
    assert str(intersection) == 'sys_platform == "darwin" and python_version < "4.0"'


def test_single_marker_intersect_with_multi_compacts_constraint() -> None:
    m = parse_marker('python_version < "3.6"')

    intersection = m & (
        parse_marker('implementation_name == "cpython" and python_version < "3.4"')
    )
    assert (
        str(intersection)
        == 'implementation_name == "cpython" and python_version < "3.4"'
    )


def test_single_marker_intersect_with_union_leads_to_single_marker() -> None:
    m = parse_marker('python_version >= "3.6"')

    intersection = m & (
        parse_marker('python_version < "3.6" or python_version >= "3.7"')
    )
    assert str(intersection) == 'python_version >= "3.7"'


def test_single_marker_intersect_with_union_leads_to_empty() -> None:
    m = parse_marker('python_version == "3.7"')

    intersection = m & (
        parse_marker('python_version < "3.7" or python_version >= "3.8"')
    )
    assert intersection.is_empty()


def test_single_marker_not_in_python_intersection() -> None:
    m = parse_marker('python_version not in "2.7, 3.0, 3.1"')

    intersection = m & (parse_marker('python_version not in "2.7, 3.0, 3.1, 3.2"'))
    assert str(intersection) == 'python_version not in "2.7, 3.0, 3.1, 3.2"'


@pytest.mark.parametrize(
    ("marker1", "marker2", "expected"),
    [
        # same value
        ('extra == "a"', 'extra == "a"', 'extra == "a"'),
        ('extra == "a"', 'extra != "a"', "<empty>"),
        ('extra != "a"', 'extra == "a"', "<empty>"),
        ('extra != "a"', 'extra != "a"', 'extra != "a"'),
        # different values
        ('extra == "a"', 'extra == "b"', 'extra == "a" and extra == "b"'),
        ('extra == "a"', 'extra != "b"', 'extra == "a" and extra != "b"'),
        ('extra != "a"', 'extra == "b"', 'extra != "a" and extra == "b"'),
        ('extra != "a"', 'extra != "b"', 'extra != "a" and extra != "b"'),
    ],
)
def test_single_marker_intersect_extras(
    marker1: str, marker2: str, expected: str
) -> None:
    assert str(parse_marker(marker1) & parse_marker(marker2)) == expected


def test_single_marker_union() -> None:
    m = parse_marker('sys_platform == "darwin"')

    union = m | (parse_marker('implementation_name == "cpython"'))
    assert str(union) == 'sys_platform == "darwin" or implementation_name == "cpython"'


def test_single_marker_union_is_any() -> None:
    m = parse_marker('python_version >= "3.4"')

    union = m | (parse_marker('python_version < "3.6"'))
    assert union.is_any()


@pytest.mark.parametrize(
    ("marker1", "marker2", "expected"),
    [
        (
            'python_version < "3.6"',
            'python_version < "3.4"',
            'python_version < "3.6"',
        ),
        (
            'sys_platform == "linux"',
            'sys_platform != "win32"',
            'sys_platform != "win32"',
        ),
        (
            'python_version == "3.6"',
            'python_version > "3.6"',
            'python_version >= "3.6"',
        ),
        (
            'python_version == "3.6"',
            'python_version < "3.6"',
            'python_version <= "3.6"',
        ),
        (
            'python_version < "3.6"',
            'python_version > "3.6"',
            'python_version != "3.6"',
        ),
    ],
)
def test_single_marker_union_is_single_marker(
    marker1: str, marker2: str, expected: str
) -> None:
    m = parse_marker(marker1)

    union = m | (parse_marker(marker2))
    assert str(union) == expected


def test_single_marker_union_with_multi() -> None:
    m = parse_marker('sys_platform == "darwin"')

    union = m | (
        parse_marker('implementation_name == "cpython" and python_version >= "3.6"')
    )
    assert (
        str(union) == 'implementation_name == "cpython" and python_version >= "3.6" or'
        ' sys_platform == "darwin"'
    )


def test_single_marker_union_with_multi_duplicate() -> None:
    m = parse_marker('sys_platform == "darwin" and python_version >= "3.6"')

    union = m | (parse_marker('sys_platform == "darwin" and python_version >= "3.6"'))
    assert str(union) == 'sys_platform == "darwin" and python_version >= "3.6"'


@pytest.mark.parametrize(
    ("single_marker", "multi_marker", "expected"),
    [
        (
            'python_version >= "3.6"',
            'python_version >= "3.7" and sys_platform == "win32"',
            'python_version >= "3.6"',
        ),
        (
            'sys_platform == "linux"',
            'sys_platform != "linux" and sys_platform != "win32"',
            'sys_platform != "win32"',
        ),
    ],
)
def test_single_marker_union_with_multi_is_single_marker(
    single_marker: str, multi_marker: str, expected: str
) -> None:
    m1 = parse_marker(single_marker)
    m2 = parse_marker(multi_marker)
    assert str(m1 | (m2)) == expected
    assert str(m2 | (m1)) == expected


def test_single_marker_union_with_multi_cannot_be_simplified() -> None:
    m = parse_marker('python_version >= "3.7"')
    union = m | (parse_marker('python_version >= "3.6" and sys_platform == "win32"'))
    assert (
        str(union)
        == 'python_version >= "3.6" and sys_platform == "win32" or python_version >='
        ' "3.7"'
    )


def test_single_marker_union_with_multi_is_union_of_single_markers() -> None:
    m = parse_marker('python_version >= "3.6"')
    union = m | (parse_marker('python_version < "3.6" and sys_platform == "win32"'))
    assert str(union) == 'sys_platform == "win32" or python_version >= "3.6"'


def test_single_marker_union_with_multi_union_is_union_of_single_markers() -> None:
    m = parse_marker('python_version >= "3.6"')
    union = m | (
        parse_marker(
            'python_version < "3.6" and sys_platform == "win32" or python_version <'
            ' "3.6" and sys_platform == "linux"'
        )
    )
    assert (
        str(union)
        == 'sys_platform == "win32" or sys_platform == "linux" or python_version >='
        ' "3.6"'
    )


def test_single_marker_union_with_union() -> None:
    m = parse_marker('sys_platform == "darwin"')

    union = m | (
        parse_marker('implementation_name == "cpython" or python_version >= "3.6"')
    )
    assert (
        str(union)
        == 'implementation_name == "cpython" or python_version >= "3.6" or sys_platform'
        ' == "darwin"'
    )


def test_single_marker_not_in_python_union() -> None:
    m = parse_marker('python_version not in "2.7, 3.0, 3.1"')

    union = m | parse_marker('python_version not in "2.7, 3.0, 3.1, 3.2"')
    assert str(union) == 'python_version not in "2.7, 3.0, 3.1"'


def test_single_marker_union_with_union_duplicate() -> None:
    m = parse_marker('sys_platform == "darwin"')

    union = m | (parse_marker('sys_platform == "darwin" or python_version >= "3.6"'))
    assert str(union) == 'sys_platform == "darwin" or python_version >= "3.6"'

    m = parse_marker('python_version >= "3.7"')

    union = m | (parse_marker('sys_platform == "darwin" or python_version >= "3.6"'))
    assert str(union) == 'sys_platform == "darwin" or python_version >= "3.6"'

    m = parse_marker('python_version <= "3.6"')

    union = m | (parse_marker('sys_platform == "darwin" or python_version < "3.4"'))
    assert str(union) == 'sys_platform == "darwin" or python_version <= "3.6"'


def test_single_marker_union_with_inverse() -> None:
    m = parse_marker('sys_platform == "darwin"')
    union = m | (parse_marker('sys_platform != "darwin"'))
    assert union.is_any()


@pytest.mark.parametrize(
    ("marker1", "marker2", "expected"),
    [
        # same value
        ('extra == "a"', 'extra == "a"', 'extra == "a"'),
        ('extra == "a"', 'extra != "a"', ""),
        ('extra != "a"', 'extra == "a"', ""),
        ('extra != "a"', 'extra != "a"', 'extra != "a"'),
        # different values
        ('extra == "a"', 'extra == "b"', 'extra == "a" or extra == "b"'),
        ('extra == "a"', 'extra != "b"', 'extra == "a" or extra != "b"'),
        ('extra != "a"', 'extra == "b"', 'extra != "a" or extra == "b"'),
        ('extra != "a"', 'extra != "b"', 'extra != "a" or extra != "b"'),
    ],
)
def test_single_marker_union_extras(marker1: str, marker2: str, expected: str) -> None:
    assert str(parse_marker(marker1) | (parse_marker(marker2))) == expected
