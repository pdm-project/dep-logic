import pytest

from dep_logic.markers import MarkerUnion, MultiMarker, parse_marker
from dep_logic.markers.empty import EmptyMarker
from dep_logic.utils import union

EMPTY = "<empty>"


def test_multi_marker() -> None:
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    assert isinstance(m, MultiMarker)
    assert m.markers == (
        parse_marker('sys_platform == "darwin"'),
        parse_marker('implementation_name == "cpython"'),
    )


def test_multi_marker_is_empty_is_contradictory() -> None:
    m = parse_marker(
        'sys_platform == "linux" and python_version >= "3.5" and python_version < "2.8"'
    )

    assert m.is_empty()

    m = parse_marker('sys_platform == "linux" and sys_platform == "win32"')

    assert m.is_empty()


def test_multi_complex_multi_marker_is_empty() -> None:
    m1 = parse_marker(
        'python_full_version >= "3.0.0" and python_full_version < "3.4.0"'
    )
    m2 = parse_marker(
        'python_version >= "3.6" and python_full_version < "3.0.0" and python_version <'
        ' "3.7"'
    )
    m3 = parse_marker(
        'python_version >= "3.6" and python_version < "3.7" and python_full_version >='
        ' "3.5.0"'
    )

    m = m1 & (m2 | m3)

    assert m.is_empty()


def test_multi_marker_is_any() -> None:
    m1 = parse_marker('python_version != "3.6" or python_version == "3.6"')
    m2 = parse_marker('python_version != "3.7" or python_version == "3.7"')

    assert m1 & m2.is_any()
    assert m2 & m1.is_any()


def test_multi_marker_intersect_multi() -> None:
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    intersection = m & (
        parse_marker('python_version >= "3.6" and os_name == "Windows"')
    )
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and implementation_name == "cpython" '
        'and python_version >= "3.6" and os_name == "Windows"'
    )


def test_multi_marker_intersect_multi_with_overlapping_constraints() -> None:
    m = parse_marker('sys_platform == "darwin" and python_version < "3.6"')

    intersection = m & (
        parse_marker(
            'python_version <= "3.4" and os_name == "Windows" and sys_platform =='
            ' "darwin"'
        )
    )
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and python_version <= "3.4" and os_name =='
        ' "Windows"'
    )


def test_multi_marker_intersect_with_union_drops_union() -> None:
    m = parse_marker('python_version >= "3" and python_version < "4"')
    m2 = parse_marker('python_version < "2" or python_version >= "3"')
    assert str(m & m2) == str(m)
    assert str(m2 & m) == str(m)


def test_multi_marker_intersect_with_multi_union_leads_to_empty_in_one_step() -> None:
    # empty marker in one step
    # py == 2 and (py < 2 or py >= 3) -> empty
    m = parse_marker('sys_platform == "darwin" and python_version == "2"')
    m2 = parse_marker(
        'sys_platform == "darwin" and (python_version < "2" or python_version >= "3")'
    )
    assert (m & m2).is_empty()
    assert (m2 & m).is_empty()


def test_multi_marker_intersect_with_multi_union_leads_to_empty_in_two_steps() -> None:
    # empty marker in two steps
    # py >= 2 and (py < 2 or py >= 3) -> py >= 3
    # py < 3 and py >= 3 -> empty
    m = parse_marker('python_version >= "2" and python_version < "3"')
    m2 = parse_marker(
        'sys_platform == "darwin" and (python_version < "2" or python_version >= "3")'
    )
    assert (m & m2).is_empty()
    assert (m2 & m).is_empty()


def test_multi_marker_union_multi() -> None:
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    union = m | parse_marker('python_version >= "3.6" and os_name == "Windows"')
    assert (
        str(union) == 'sys_platform == "darwin" and implementation_name == "cpython" '
        'or python_version >= "3.6" and os_name == "Windows"'
    )


def test_multi_marker_union_multi_is_single_marker() -> None:
    m = parse_marker('python_version >= "3" and sys_platform == "win32"')
    m2 = parse_marker('sys_platform != "win32" and python_version >= "3"')
    assert str(m | m2) == 'python_version >= "3"'
    assert str(m2 | m) == 'python_version >= "3"'


@pytest.mark.parametrize(
    "marker1, marker2, expected",
    [
        (
            'python_version >= "3" and sys_platform == "win32"',
            (
                'python_version >= "3" and sys_platform != "win32" and sys_platform !='
                ' "linux"'
            ),
            'python_version >= "3" and sys_platform != "linux"',
        ),
        (
            (
                'python_version >= "3.8" and python_version < "4.0" and sys_platform =='
                ' "win32"'
            ),
            'python_version >= "3.8" and python_version < "4.0"',
            'python_version ~= "3.8"',
        ),
    ],
)
def test_multi_marker_union_multi_is_multi(
    marker1: str, marker2: str, expected: str
) -> None:
    m1 = parse_marker(marker1)
    m2 = parse_marker(marker2)
    assert str(m1 | m2) == expected
    assert str(m2 | m1) == expected


@pytest.mark.parametrize(
    "marker1, marker2, expected",
    [
        # Ranges with same start
        (
            'python_version >= "3.6" and python_full_version < "3.6.2"',
            'python_version >= "3.6" and python_version < "3.7"',
            'python_version >= "3.6" and python_version < "3.7"',
        ),
        (
            'python_version > "3.6" and python_full_version < "3.6.2"',
            'python_version > "3.6" and python_version < "3.7"',
            'python_version > "3.6" and python_version < "3.7"',
        ),
        # Ranges meet exactly
        (
            'python_version >= "3.6" and python_full_version < "3.6.2"',
            'python_full_version >= "3.6.2" and python_version < "3.7"',
            'python_version >= "3.6" and python_full_version < "3.7.0"',
        ),
        (
            'python_version >= "3.6" and python_full_version <= "3.6.2"',
            'python_full_version > "3.6.2" and python_version < "3.7"',
            'python_version >= "3.6" and python_version < "3.7"',
        ),
        # Ranges overlap
        (
            'python_version >= "3.6" and python_full_version <= "3.6.8"',
            'python_full_version >= "3.6.2" and python_version < "3.7"',
            'python_version >= "3.6" and python_full_version < "3.7.0"',
        ),
        # Ranges with same end.
        (
            'python_version >= "3.6" and python_version < "3.7"',
            'python_full_version >= "3.6.2" and python_version < "3.7"',
            'python_version >= "3.6" and python_version < "3.7"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_full_version >= "3.6.2" and python_version <= "3.7"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        # A range covers an exact marker.
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_version == "3.6"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_version == "3.6" and implementation_name == "cpython"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_full_version == "3.6.2"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_full_version == "3.6.2" and implementation_name == "cpython"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_version == "3.7"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_version == "3.7" and implementation_name == "cpython"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
    ],
)
def test_version_ranges_collapse_on_union(
    marker1: str, marker2: str, expected: str
) -> None:
    m1 = parse_marker(marker1)
    m2 = parse_marker(marker2)
    assert str(m1 | m2) == expected
    assert str(m2 | m1) == expected


def test_multi_marker_union_with_union() -> None:
    m1 = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')
    m2 = parse_marker('python_version >= "3.6" or os_name == "Windows"')

    # Union isn't _quite_ symmetrical.
    expected1 = (
        'sys_platform == "darwin" and implementation_name == "cpython" or'
        ' python_version >= "3.6" or os_name == "Windows"'
    )
    assert str(m1 | m2) == expected1

    expected2 = (
        'python_version >= "3.6" or os_name == "Windows" or'
        ' sys_platform == "darwin" and implementation_name == "cpython"'
    )
    assert str(m2 | m1) == expected2


def test_multi_marker_union_with_multi_union_is_single_marker() -> None:
    m = parse_marker('sys_platform == "darwin" and python_version == "3"')
    m2 = parse_marker(
        'sys_platform == "darwin" and python_version < "3" or sys_platform == "darwin"'
        ' and python_version > "3"'
    )
    assert str(m | m2) == 'sys_platform == "darwin"'
    assert str(m2 | m) == 'sys_platform == "darwin"'


def test_multi_marker_union_with_union_multi_is_single_marker() -> None:
    m = parse_marker('sys_platform == "darwin" and python_version == "3"')
    m2 = parse_marker(
        'sys_platform == "darwin" and (python_version < "3" or python_version > "3")'
    )
    assert str(m | m2) == 'sys_platform == "darwin"'
    assert str(m2 | m) == 'sys_platform == "darwin"'


def test_marker_union() -> None:
    m = parse_marker('sys_platform == "darwin" or implementation_name == "cpython"')

    assert isinstance(m, MarkerUnion)
    assert m.markers == (
        parse_marker('sys_platform == "darwin"'),
        parse_marker('implementation_name == "cpython"'),
    )


def test_marker_union_deduplicate() -> None:
    m = parse_marker(
        'sys_platform == "darwin" or implementation_name == "cpython" or sys_platform'
        ' == "darwin"'
    )

    assert str(m) == 'sys_platform == "darwin" or implementation_name == "cpython"'


def test_marker_union_intersect_single_marker() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m & parse_marker('implementation_name == "cpython"')
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and implementation_name == "cpython" '
        'or python_version < "3.4" and implementation_name == "cpython"'
    )


def test_marker_union_intersect_single_with_overlapping_constraints() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m & parse_marker('python_version <= "3.6"')
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and python_version <= "3.6" or python_version <'
        ' "3.4"'
    )

    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')
    intersection = m & parse_marker('sys_platform == "darwin"')
    assert str(intersection) == 'sys_platform == "darwin"'


def test_marker_union_intersect_marker_union() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m & (
        parse_marker('implementation_name == "cpython" or os_name == "Windows"')
    )
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and implementation_name == "cpython" '
        'or sys_platform == "darwin" and os_name == "Windows" or '
        'python_version < "3.4" and implementation_name == "cpython" or '
        'python_version < "3.4" and os_name == "Windows"'
    )


def test_marker_union_intersect_marker_union_drops_unnecessary_markers() -> None:
    m = parse_marker(
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.4" and python_version < "4.0"'
    )
    m2 = parse_marker(
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.4" and python_version < "4.0"'
    )

    intersection = m & m2
    expected = (
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version ~= "3.4"'
    )
    assert str(intersection) == expected


def test_marker_union_intersect_multi_marker() -> None:
    m1 = parse_marker('sys_platform == "darwin" or python_version < "3.4"')
    m2 = parse_marker('implementation_name == "cpython" and os_name == "Windows"')

    # Intersection isn't _quite_ symmetrical.
    expected1 = (
        'sys_platform == "darwin" and implementation_name == "cpython" and os_name =='
        ' "Windows" or python_version < "3.4" and implementation_name == "cpython" and'
        ' os_name == "Windows"'
    )

    intersection = m1 & m2
    assert str(intersection) == expected1

    expected2 = (
        'implementation_name == "cpython" and os_name == "Windows" and sys_platform'
        ' == "darwin" or implementation_name == "cpython" and os_name == "Windows"'
        ' and python_version < "3.4"'
    )

    intersection = m2 & m1
    assert str(intersection) == expected2


def test_marker_union_union_with_union() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    union = m | (
        parse_marker('implementation_name == "cpython" or os_name == "Windows"')
    )
    assert (
        str(union) == 'sys_platform == "darwin" or python_version < "3.4" '
        'or implementation_name == "cpython" or os_name == "Windows"'
    )


def test_marker_union_union_duplicates() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    union = m | parse_marker('sys_platform == "darwin" or os_name == "Windows"')
    assert (
        str(union)
        == 'sys_platform == "darwin" or python_version < "3.4" or os_name == "Windows"'
    )

    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    union = m | (
        parse_marker(
            'sys_platform == "darwin" or os_name == "Windows" or python_version <='
            ' "3.6"'
        )
    )
    assert (
        str(union)
        == 'sys_platform == "darwin" or python_version <= "3.6" or os_name == "Windows"'
    )


def test_marker_union_all_any() -> None:
    union = MarkerUnion.of(parse_marker(""), parse_marker(""))

    assert union.is_any()


def test_marker_union_not_all_any() -> None:
    union = MarkerUnion.of(parse_marker(""), parse_marker(""), EmptyMarker())

    assert union.is_any()


def test_marker_union_all_empty() -> None:
    union = MarkerUnion.of(EmptyMarker(), EmptyMarker())

    assert union.is_empty()


def test_marker_union_not_all_empty() -> None:
    union = MarkerUnion.of(EmptyMarker(), EmptyMarker(), parse_marker(""))

    assert not union.is_empty()


def test_intersect_compacts_constraints() -> None:
    m = parse_marker('python_version < "4.0"')

    intersection = m & parse_marker('python_version < "5.0"')
    assert str(intersection) == 'python_version < "4.0"'


def test_multi_marker_removes_duplicates() -> None:
    m = parse_marker('sys_platform == "win32" and sys_platform == "win32"')

    assert str(m) == 'sys_platform == "win32"'

    m = parse_marker(
        'sys_platform == "darwin" and implementation_name == "cpython" '
        'and sys_platform == "darwin" and implementation_name == "cpython"'
    )

    assert str(m) == 'sys_platform == "darwin" and implementation_name == "cpython"'


def test_union_of_a_single_marker_is_the_single_marker() -> None:
    union = MarkerUnion.of(m := parse_marker("python_version>= '2.7'"))

    assert m == union


def test_union_of_multi_with_a_containing_single() -> None:
    single = parse_marker('python_version >= "2.7"')
    multi = parse_marker('python_version >= "2.7" and extra == "foo"')
    union = multi | single

    assert union == single


def test_single_markers_are_found_in_complex_intersection() -> None:
    m1 = parse_marker('implementation_name != "pypy" and python_version <= "3.6"')
    m2 = parse_marker(
        'python_version >= "3.6" and python_version < "4.0" and implementation_name =='
        ' "cpython"'
    )
    intersection = m1 & m2
    assert (
        str(intersection)
        == 'implementation_name == "cpython" and python_version == "3.6"'
    )


@pytest.mark.parametrize(
    "marker1, marker2",
    [
        (
            (
                '(platform_system != "Windows" or platform_machine != "x86") and'
                ' python_version == "3.8"'
            ),
            'platform_system == "Windows" and platform_machine == "x86"',
        ),
        # Following example via
        # https://github.com/python-poetry/poetry-plugin-export/issues/163
        (
            (
                'python_version >= "3.8" and python_version < "3.11" and'
                ' (python_version > "3.9" or platform_system != "Windows" or'
                ' platform_machine != "x86") or python_version >= "3.11" and'
                ' python_version < "3.12"'
            ),
            (
                'python_version == "3.8" and platform_system == "Windows" and'
                ' platform_machine == "x86" or python_version == "3.9" and'
                ' platform_system == "Windows" and platform_machine == "x86"'
            ),
        ),
    ],
)
def test_empty_marker_is_found_in_complex_intersection(
    marker1: str, marker2: str
) -> None:
    m1 = parse_marker(marker1)
    m2 = parse_marker(marker2)
    assert (m1 & m2).is_empty()
    assert (m2 & m1).is_empty()


def test_empty_marker_is_found_in_complex_parse() -> None:
    marker = parse_marker(
        '(python_implementation != "pypy" or python_version != "3.6") and '
        '((python_implementation != "pypy" and python_version != "3.6") or'
        ' (python_implementation == "pypy" and python_version == "3.6")) and '
        '(python_implementation == "pypy" or python_version == "3.6")'
    )
    assert marker.is_empty()


def test_complex_union() -> None:
    """
    real world example on the way to get mutually exclusive markers
    for numpy(>=1.21.2) of https://pypi.org/project/opencv-python/4.6.0.66/
    """
    markers = [
        parse_marker(m)
        for m in [
            (
                'python_version < "3.7" and python_version >= "3.6"'
                ' and platform_system == "Darwin" and platform_machine == "arm64"'
            ),
            (
                'python_version >= "3.10" or python_version >= "3.9"'
                ' and platform_system == "Darwin" and platform_machine == "arm64"'
            ),
            (
                'python_version >= "3.8" and platform_system == "Darwin"'
                ' and platform_machine == "arm64" and python_version < "3.9"'
            ),
            (
                'python_version >= "3.7" and platform_system == "Darwin"'
                ' and platform_machine == "arm64" and python_version < "3.8"'
            ),
        ]
    ]
    assert (
        str(union(*markers))
        == 'platform_system == "Darwin" and platform_machine == "arm64"'
        ' and python_version >= "3.6" or python_version >= "3.10"'
    )


def test_union_avoids_combinatorial_explosion() -> None:
    """
    combinatorial explosion without AtomicMultiMarker and AtomicMarkerUnion
    based gevent constraint of sqlalchemy 2.0.7
    see https://github.com/python-poetry/poetry/issues/7689 for details
    """
    expected = (
        'python_full_version >= "3.11.0" and python_version < "4.0"'
        ' and platform_machine in "WIN32,win32,AMD64,amd64,x86_64,aarch64,ppc64le"'
    )
    m1 = parse_marker(expected)
    m2 = parse_marker(
        'python_full_version >= "3.11.0" and python_full_version < "4.0.0"'
        ' and (platform_machine == "aarch64" or platform_machine == "ppc64le"'
        ' or platform_machine == "x86_64" or platform_machine == "amd64"'
        ' or platform_machine == "AMD64" or platform_machine == "win32"'
        ' or platform_machine == "WIN32")'
    )
    assert str(m1 | m2) == expected
    assert str(m2 | m1) == expected


def test_intersection_avoids_combinatorial_explosion() -> None:
    """
    combinatorial explosion without AtomicMultiMarker and AtomicMarkerUnion
    based gevent constraint of sqlalchemy 2.0.7
    see https://github.com/python-poetry/poetry/issues/7689 for details
    """
    m1 = parse_marker(
        'python_full_version >= "3.11.0" and python_full_version < "4.0.0"'
    )
    m2 = parse_marker(
        'python_version >= "3" and (platform_machine == "aarch64" '
        'or platform_machine == "ppc64le" or platform_machine == "x86_64" '
        'or platform_machine == "amd64" or platform_machine == "AMD64" '
        'or platform_machine == "win32" or platform_machine == "WIN32")'
    )
    assert (
        str(m1 & m2)
        == 'python_full_version >= "3.11.0" and python_full_version < "4.0.0"'
        ' and (platform_machine == "aarch64" or platform_machine == "ppc64le"'
        ' or platform_machine == "x86_64" or platform_machine == "amd64"'
        ' or platform_machine == "AMD64" or platform_machine == "win32"'
        ' or platform_machine == "WIN32")'
    )
    assert (
        str(m2 & m1)
        == '(platform_machine == "aarch64" or platform_machine == "ppc64le"'
        ' or platform_machine == "x86_64" or platform_machine == "amd64"'
        ' or platform_machine == "AMD64" or platform_machine == "win32"'
        ' or platform_machine == "WIN32") and python_full_version >= "3.11.0" '
        'and python_full_version < "4.0.0"'
    )


@pytest.mark.parametrize(
    "python_version, python_full_version, "
    "expected_intersection_version, expected_union_version",
    [
        # python_version > 3.6 (equal to python_full_version >= 3.7.0)
        ('> "3.6"', '> "3.5.2"', '> "3.6"', '> "3.5.2"'),
        ('> "3.6"', '>= "3.5.2"', '> "3.6"', '>= "3.5.2"'),
        ('> "3.6"', '> "3.6.2"', '> "3.6"', '> "3.6.2"'),
        ('> "3.6"', '>= "3.6.2"', '> "3.6"', '>= "3.6.2"'),
        ('> "3.6"', '> "3.7.0"', '> "3.7.0"', '> "3.6"'),
        ('> "3.6"', '>= "3.7.0"', '> "3.6"', '> "3.6"'),
        ('> "3.6"', '> "3.7.1"', '> "3.7.1"', '> "3.6"'),
        ('> "3.6"', '>= "3.7.1"', '>= "3.7.1"', '> "3.6"'),
        ('> "3.6"', '== "3.6.2"', EMPTY, None),
        ('> "3.6"', '== "3.7.0"', '== "3.7.0"', '> "3.6"'),
        ('> "3.6"', '== "3.7.1"', '== "3.7.1"', '> "3.6"'),
        ('> "3.6"', '!= "3.6.2"', '> "3.6"', '!= "3.6.2"'),
        ('> "3.6"', '!= "3.7.0"', '> "3.7.0"', ""),
        ('> "3.6"', '!= "3.7.1"', None, ""),
        ('> "3.6"', '< "3.7.0"', EMPTY, ""),
        ('> "3.6"', '<= "3.7.0"', '== "3.7.0"', ""),
        ('> "3.6"', '< "3.7.1"', None, ""),
        ('> "3.6"', '<= "3.7.1"', None, ""),
        # python_version >= 3.6 (equal to python_full_version >= 3.6.0)
        ('>= "3.6"', '> "3.5.2"', '>= "3.6"', '> "3.5.2"'),
        ('>= "3.6"', '>= "3.5.2"', '>= "3.6"', '>= "3.5.2"'),
        ('>= "3.6"', '> "3.6.0"', '> "3.6.0"', '>= "3.6"'),
        ('>= "3.6"', '>= "3.6.0"', '>= "3.6"', '>= "3.6"'),
        ('>= "3.6"', '> "3.6.1"', '> "3.6.1"', '>= "3.6"'),
        ('>= "3.6"', '>= "3.6.1"', '>= "3.6.1"', '>= "3.6"'),
        ('>= "3.6"', '== "3.5.2"', EMPTY, None),
        ('>= "3.6"', '== "3.6.0"', '== "3.6.0"', '>= "3.6"'),
        ('>= "3.6"', '!= "3.5.2"', '>= "3.6"', '!= "3.5.2"'),
        ('>= "3.6"', '!= "3.6.0"', '> "3.6.0"', ""),
        ('>= "3.6"', '!= "3.6.1"', None, ""),
        ('>= "3.6"', '!= "3.7.1"', None, ""),
        ('>= "3.6"', '< "3.6.0"', EMPTY, ""),
        ('>= "3.6"', '<= "3.6.0"', '== "3.6.0"', ""),
        ('>= "3.6"', '< "3.6.1"', None, ""),  # '== "3.6.0"'
        ('>= "3.6"', '<= "3.6.1"', None, ""),
        # python_version < 3.6 (equal to python_full_version < 3.6.0)
        ('< "3.6"', '< "3.5.2"', '< "3.5.2"', '< "3.6"'),
        ('< "3.6"', '<= "3.5.2"', '<= "3.5.2"', '< "3.6"'),
        ('< "3.6"', '< "3.6.0"', '< "3.6"', '< "3.6"'),
        ('< "3.6"', '<= "3.6.0"', '< "3.6"', '<= "3.6.0"'),
        ('< "3.6"', '< "3.6.1"', '< "3.6"', '< "3.6.1"'),
        ('< "3.6"', '<= "3.6.1"', '< "3.6"', '<= "3.6.1"'),
        ('< "3.6"', '== "3.5.2"', '== "3.5.2"', '< "3.6"'),
        ('< "3.6"', '== "3.6.0"', EMPTY, '<= "3.6.0"'),
        ('< "3.6"', '!= "3.5.2"', None, ""),
        ('< "3.6"', '!= "3.6.0"', '< "3.6"', '!= "3.6.0"'),
        ('< "3.6"', '> "3.6.0"', EMPTY, '!= "3.6.0"'),
        ('< "3.6"', '>= "3.6.0"', EMPTY, ""),
        ('< "3.6"', '> "3.5.2"', None, ""),
        ('< "3.6"', '>= "3.5.2"', '~= "3.5.2"', ""),
        # python_version <= 3.6 (equal to python_full_version < 3.7.0)
        ('<= "3.6"', '< "3.6.1"', '< "3.6.1"', '<= "3.6"'),
        ('<= "3.6"', '<= "3.6.1"', '<= "3.6.1"', '<= "3.6"'),
        ('<= "3.6"', '< "3.7.0"', '<= "3.6"', '<= "3.6"'),
        ('<= "3.6"', '<= "3.7.0"', '<= "3.6"', '<= "3.7.0"'),
        ('<= "3.6"', '== "3.6.1"', '== "3.6.1"', '<= "3.6"'),
        ('<= "3.6"', '== "3.7.0"', EMPTY, '<= "3.7.0"'),
        ('<= "3.6"', '!= "3.6.1"', None, ""),
        ('<= "3.6"', '!= "3.7.0"', '<= "3.6"', '!= "3.7.0"'),
        ('<= "3.6"', '> "3.7.0"', EMPTY, '!= "3.7.0"'),
        ('<= "3.6"', '>= "3.7.0"', EMPTY, ""),
        ('<= "3.6"', '> "3.6.2"', None, ""),
        ('<= "3.6"', '>= "3.6.2"', '~= "3.6.2"', ""),
        # python_version == 3.6
        # (equal to python_full_version >= 3.6.0 and python_full_version < 3.7.0)
        ('== "3.6"', '< "3.5.2"', EMPTY, None),
        ('== "3.6"', '<= "3.5.2"', EMPTY, None),
        ('== "3.6"', '> "3.5.2"', '== "3.6"', '> "3.5.2"'),
        ('== "3.6"', '>= "3.5.2"', '== "3.6"', '>= "3.5.2"'),
        ('== "3.6"', '!= "3.5.2"', '== "3.6"', '!= "3.5.2"'),
        ('== "3.6"', '< "3.6.0"', EMPTY, '< "3.7.0"'),
        ('== "3.6"', '<= "3.6.0"', '== "3.6.0"', '< "3.7.0"'),
        ('== "3.6"', '> "3.6.0"', None, '>= "3.6.0"'),
        ('== "3.6"', '>= "3.6.0"', '== "3.6"', '>= "3.6.0"'),
        ('== "3.6"', '!= "3.6.0"', None, ""),
        ('== "3.6"', '< "3.6.1"', None, '< "3.7.0"'),
        ('== "3.6"', '<= "3.6.1"', None, '< "3.7.0"'),
        ('== "3.6"', '> "3.6.1"', None, '>= "3.6.0"'),
        ('== "3.6"', '>= "3.6.1"', '~= "3.6.1"', '>= "3.6.0"'),
        ('== "3.6"', '!= "3.6.1"', None, ""),
        ('== "3.6"', '< "3.7.0"', '== "3.6"', '< "3.7.0"'),
        ('== "3.6"', '<= "3.7.0"', '== "3.6"', '<= "3.7.0"'),
        ('== "3.6"', '> "3.7.0"', EMPTY, None),
        ('== "3.6"', '>= "3.7.0"', EMPTY, '>= "3.6.0"'),
        ('== "3.6"', '!= "3.7.0"', '== "3.6"', '!= "3.7.0"'),
        ('== "3.6"', '<= "3.7.1"', '== "3.6"', '<= "3.7.1"'),
        ('== "3.6"', '< "3.7.1"', '== "3.6"', '< "3.7.1"'),
        ('== "3.6"', '> "3.7.1"', EMPTY, None),
        ('== "3.6"', '>= "3.7.1"', EMPTY, None),
        ('== "3.6"', '!= "3.7.1"', '== "3.6"', '!= "3.7.1"'),
        # python_version != 3.6
        # (equal to python_full_version < 3.6.0 or python_full_version >= 3.7.0)
        ('!= "3.6"', '< "3.5.2"', '< "3.5.2"', '!= "3.6"'),
        ('!= "3.6"', '<= "3.5.2"', '<= "3.5.2"', '!= "3.6"'),
        ('!= "3.6"', '> "3.5.2"', None, ""),
        ('!= "3.6"', '>= "3.5.2"', None, ""),
        ('!= "3.6"', '!= "3.5.2"', None, ""),
        ('!= "3.6"', '< "3.6.0"', '< "3.6.0"', '!= "3.6"'),
        ('!= "3.6"', '<= "3.6.0"', '< "3.6.0"', None),
        ('!= "3.6"', '> "3.6.0"', '>= "3.7.0"', '!= "3.6.0"'),
        ('!= "3.6"', '>= "3.6.0"', '>= "3.7.0"', ""),
        ('!= "3.6"', '!= "3.6.0"', '!= "3.6"', '!= "3.6.0"'),
        ('!= "3.6"', '< "3.6.1"', '< "3.6.0"', None),
        ('!= "3.6"', '<= "3.6.1"', '< "3.6.0"', None),
        ('!= "3.6"', '> "3.6.1"', '>= "3.7.0"', None),
        ('!= "3.6"', '>= "3.6.1"', '>= "3.7.0"', None),
        ('!= "3.6"', '!= "3.6.1"', '!= "3.6"', '!= "3.6.1"'),
        ('!= "3.6"', '< "3.7.0"', '< "3.6.0"', ""),
        ('!= "3.6"', '<= "3.7.0"', None, ""),
        ('!= "3.6"', '> "3.7.0"', '> "3.7.0"', '!= "3.6"'),
        ('!= "3.6"', '>= "3.7.0"', '>= "3.7.0"', '!= "3.6"'),
        ('!= "3.6"', '!= "3.7.0"', None, ""),
        ('!= "3.6"', '<= "3.7.1"', None, ""),
        ('!= "3.6"', '< "3.7.1"', None, ""),
        ('!= "3.6"', '> "3.7.1"', '> "3.7.1"', '!= "3.6"'),
        ('!= "3.6"', '>= "3.7.1"', '>= "3.7.1"', '!= "3.6"'),
        ('!= "3.6"', '!= "3.7.1"', None, ""),
    ],
)
def test_merging_python_version_and_python_full_version(
    python_version: str,
    python_full_version: str,
    expected_intersection_version: str,
    expected_union_version: str,
) -> None:
    m = f"python_version {python_version}"
    m2 = f"python_full_version {python_full_version}"

    def get_expected_marker(expected_version: str, op: str) -> str:
        if expected_version is None:
            expected = f"{m} {op} {m2}"
        elif expected_version in ("", EMPTY):
            expected = expected_version
        else:
            expected_marker_name = (
                "python_version"
                if expected_version.count(".") < 2
                else "python_full_version"
            )
            expected = f"{expected_marker_name} {expected_version}"
        return expected

    expected_intersection = get_expected_marker(expected_intersection_version, "and")
    expected_union = get_expected_marker(expected_union_version, "or")

    intersection = parse_marker(m) & parse_marker(m2)
    assert str(intersection) == expected_intersection

    union = parse_marker(m) | parse_marker(m2)
    assert str(union) == expected_union
