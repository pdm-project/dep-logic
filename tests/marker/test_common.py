from __future__ import annotations

import pytest

from dep_logic.markers import parse_marker


@pytest.mark.parametrize(
    "marker, expected",
    [
        ('python_version >= "3.6"', 'python_version >= "3.6"'),
        ('python_version >= "3.6" and extra == "foo"', 'python_version >= "3.6"'),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar")',
            'python_version >= "3.6"',
        ),
        (
            (
                'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
                ' implementation_name == "pypy"'
            ),
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        (
            (
                'python_version >= "3.6" and extra == "foo" or implementation_name =='
                ' "pypy" and extra == "bar"'
            ),
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        (
            (
                'python_version >= "3.6" or extra == "foo" and implementation_name =='
                ' "pypy" or extra == "bar"'
            ),
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        ('extra == "foo"', ""),
        ('extra == "foo" or extra == "bar"', ""),
    ],
)
def test_without_extras(marker: str, expected: str) -> None:
    m = parse_marker(marker)

    assert str(m.without_extras()) == expected


@pytest.mark.parametrize(
    "marker, excluded, expected",
    [
        ('python_version >= "3.6"', "implementation_name", 'python_version >= "3.6"'),
        ('python_version >= "3.6"', "python_version", "*"),
        ('python_version >= "3.6" and python_version < "3.11"', "python_version", "*"),
        (
            'python_version >= "3.6" and extra == "foo"',
            "extra",
            'python_version >= "3.6"',
        ),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar")',
            "python_version",
            'extra == "foo" or extra == "bar"',
        ),
        (
            (
                'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
                ' implementation_name == "pypy"'
            ),
            "python_version",
            'extra == "foo" or extra == "bar" or implementation_name == "pypy"',
        ),
        (
            (
                'python_version >= "3.6" and extra == "foo" or implementation_name =='
                ' "pypy" and extra == "bar"'
            ),
            "implementation_name",
            'python_version >= "3.6" and extra == "foo" or extra == "bar"',
        ),
        (
            (
                'python_version >= "3.6" or extra == "foo" and implementation_name =='
                ' "pypy" or extra == "bar"'
            ),
            "implementation_name",
            'python_version >= "3.6" or extra == "foo" or extra == "bar"',
        ),
        (
            'extra == "foo" and python_version >= "3.6" or python_version >= "3.6"',
            "extra",
            'python_version >= "3.6"',
        ),
    ],
)
def test_exclude(marker: str, excluded: str, expected: str) -> None:
    m = parse_marker(marker)

    if expected == "*":
        assert m.exclude(excluded).is_any()
    else:
        assert str(m.exclude(excluded)) == expected


@pytest.mark.parametrize(
    "marker, only, expected",
    [
        ('python_version >= "3.6"', ["python_version"], 'python_version >= "3.6"'),
        ('python_version >= "3.6"', ["sys_platform"], ""),
        (
            'python_version >= "3.6" and extra == "foo"',
            ["python_version"],
            'python_version >= "3.6"',
        ),
        ('python_version >= "3.6" and extra == "foo"', ["sys_platform"], ""),
        ('python_version >= "3.6" or extra == "foo"', ["sys_platform"], ""),
        ('python_version >= "3.6" or extra == "foo"', ["python_version"], ""),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar")',
            ["extra"],
            'extra == "foo" or extra == "bar"',
        ),
        (
            (
                'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
                ' implementation_name == "pypy"'
            ),
            ["implementation_name"],
            "",
        ),
        (
            (
                'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
                ' implementation_name == "pypy"'
            ),
            ["implementation_name", "extra"],
            'extra == "foo" or extra == "bar" or implementation_name == "pypy"',
        ),
        (
            (
                'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
                ' implementation_name == "pypy"'
            ),
            ["implementation_name", "python_version"],
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        (
            (
                'python_version >= "3.6" and extra == "foo" or implementation_name =='
                ' "pypy" and extra == "bar"'
            ),
            ["implementation_name", "extra"],
            'extra == "foo" or implementation_name == "pypy" and extra == "bar"',
        ),
    ],
)
def test_only(marker: str, only: list[str], expected: str) -> None:
    m = parse_marker(marker)

    assert str(m.only(*only)) == expected
