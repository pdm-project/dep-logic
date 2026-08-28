from __future__ import annotations

import pytest

from dep_logic.markers import BaseMarker, parse_marker


class ReflectedOperand:
    def __rand__(self, other: object) -> str:
        return "reflected and"

    def __ror__(self, other: object) -> str:
        return "reflected or"


MARKERS = [
    parse_marker(""),
    parse_marker("<empty>"),
    parse_marker('os_name == "posix" and sys_platform == "linux"'),
    parse_marker('os_name == "posix" or sys_platform == "linux"'),
]


@pytest.mark.parametrize("marker", MARKERS)
def test_binary_operators_return_not_implemented(marker: BaseMarker) -> None:
    assert marker.__and__(object()) is NotImplemented
    assert marker.__or__(object()) is NotImplemented


@pytest.mark.parametrize("marker", MARKERS)
def test_binary_operators_raise_type_error(marker: BaseMarker) -> None:
    with pytest.raises(TypeError):
        marker & object()
    with pytest.raises(TypeError):
        marker | object()


@pytest.mark.parametrize("marker", MARKERS)
def test_binary_operators_use_reflected_method(marker: BaseMarker) -> None:
    operand = ReflectedOperand()

    assert marker & operand == "reflected and"
    assert marker | operand == "reflected or"


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
