import itertools

import pytest

from dep_logic.markers import InvalidMarker, parse_marker

VARIABLES = [
    "extra",
    "implementation_name",
    "implementation_version",
    "os_name",
    "platform_machine",
    "platform_release",
    "platform_system",
    "platform_version",
    "python_full_version",
    "python_version",
    "platform_python_implementation",
    "sys_platform",
]

PEP_345_VARIABLES = [
    "os.name",
    "sys.platform",
    "platform.version",
    "platform.machine",
    "platform.python_implementation",
]


OPERATORS = ["===", "==", ">=", "<=", "!=", "~=", ">", "<", "in", "not in"]

VALUES = [
    "1.0",
    "5.6a0",
    "dog",
    "freebsd",
    "literally any string can go here",
    "things @#4 dsfd (((",
]


@pytest.mark.parametrize(
    "marker_string",
    ["{} {} {!r}".format(*i) for i in itertools.product(VARIABLES, OPERATORS, VALUES)]
    + [
        "{2!r} {1} {0}".format(*i)
        for i in itertools.product(VARIABLES, OPERATORS, VALUES)
    ],
)
def test_parses_valid(marker_string: str):
    parse_marker(marker_string)


@pytest.mark.parametrize(
    "marker_string",
    [
        "this_isnt_a_real_variable >= '1.0'",
        "python_version",
        "(python_version)",
        "python_version >= 1.0 and (python_version)",
        '(python_version == "2.7" and os_name == "linux"',
        '(python_version == "2.7") with random text',
    ],
)
def test_parses_invalid(marker_string: str):
    with pytest.raises(InvalidMarker):
        parse_marker(marker_string)


@pytest.mark.parametrize(
    "marker_string",
    [
        "{} {} {!r}".format(*i)
        for i in itertools.product(PEP_345_VARIABLES, OPERATORS, VALUES)
    ]
    + [
        "{2!r} {1} {0}".format(*i)
        for i in itertools.product(PEP_345_VARIABLES, OPERATORS, VALUES)
    ],
)
def test_parses_pep345_valid(marker_string: str) -> None:
    parse_marker(marker_string)
