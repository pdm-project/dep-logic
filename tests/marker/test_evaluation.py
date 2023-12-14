from __future__ import annotations

import os

import pytest

from dep_logic.markers import parse_marker


@pytest.mark.parametrize(
    ("marker_string", "environment", "expected"),
    [
        (f"os_name == '{os.name}'", None, True),
        ("os_name == 'foo'", {"os_name": "foo"}, True),
        ("os_name == 'foo'", {"os_name": "bar"}, False),
        ("'2.7' in python_version", {"python_version": "2.7.5"}, True),
        ("'2.7' not in python_version", {"python_version": "2.7"}, False),
        (
            "os_name == 'foo' and python_version ~= '2.7.0'",
            {"os_name": "foo", "python_version": "2.7.6"},
            True,
        ),
        (
            "python_version ~= '2.7.0' and (os_name == 'foo' or " "os_name == 'bar')",
            {"os_name": "foo", "python_version": "2.7.4"},
            True,
        ),
        (
            "python_version ~= '2.7.0' and (os_name == 'foo' or " "os_name == 'bar')",
            {"os_name": "bar", "python_version": "2.7.4"},
            True,
        ),
        (
            "python_version ~= '2.7.0' and (os_name == 'foo' or " "os_name == 'bar')",
            {"os_name": "other", "python_version": "2.7.4"},
            False,
        ),
        ("extra == 'security'", {"extra": "quux"}, False),
        ("extra == 'security'", {"extra": "security"}, True),
        ("extra == 'SECURITY'", {"extra": "security"}, True),
        ("extra == 'security'", {"extra": "SECURITY"}, True),
        ("extra == 'pep-685-norm'", {"extra": "PEP_685...norm"}, True),
        (
            "extra == 'Different.punctuation..is...equal'",
            {"extra": "different__punctuation_is_EQUAL"},
            True,
        ),
    ],
)
def test_evaluates(
    marker_string: str, environment: dict[str, str], expected: bool
) -> None:
    args = [] if environment is None else [environment]
    assert parse_marker(marker_string).evaluate(*args) == expected


@pytest.mark.parametrize(
    ("marker_string", "environment", "expected"),
    [
        (f"os.name == '{os.name}'", None, True),
        ("sys.platform == 'win32'", {"sys_platform": "linux2"}, False),
        ("platform.version in 'Ubuntu'", {"platform_version": "#39"}, False),
        ("platform.machine=='x86_64'", {"platform_machine": "x86_64"}, True),
        (
            "platform.python_implementation=='Jython'",
            {"platform_python_implementation": "CPython"},
            False,
        ),
        (
            "python_version == '2.5' and platform.python_implementation!= 'Jython'",
            {"python_version": "2.7"},
            False,
        ),
        (
            (
                "platform_machine in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
                " amd64 AMD64 win32 WIN32'"
            ),
            {"platform_machine": "foo"},
            False,
        ),
        (
            (
                "platform_machine in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
                " amd64 AMD64 win32 WIN32'"
            ),
            {"platform_machine": "x86_64"},
            True,
        ),
        (
            (
                "platform_machine not in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
                " amd64 AMD64 win32 WIN32'"
            ),
            {"platform_machine": "foo"},
            True,
        ),
        (
            (
                "platform_machine not in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
                " amd64 AMD64 win32 WIN32'"
            ),
            {"platform_machine": "x86_64"},
            False,
        ),
        # extras
        # single extra
        ("extra != 'security'", {"extra": "quux"}, True),
        ("extra != 'security'", {"extra": "security"}, False),
        ("extra != 'security'", {}, True),
        ("extra != 'security'", {"platform_machine": "x86_64"}, True),
        # normalization
        ("extra == 'Security.1'", {"extra": "security-1"}, True),
        ("extra == 'a'", {}, False),
        ("extra != 'a'", {}, True),
        ("extra == 'a' and extra == 'b'", {}, False),
        ("extra == 'a' or extra == 'b'", {}, False),
        ("extra != 'a' and extra != 'b'", {}, True),
        ("extra != 'a' or extra != 'b'", {}, True),
        ("extra != 'a' and extra == 'b'", {}, False),
        ("extra != 'a' or extra == 'b'", {}, True),
        # multiple extras
        ("extra == 'a'", {"extra": ("a", "b")}, True),
        ("extra == 'a'", {"extra": ("b", "c")}, False),
        ("extra != 'a'", {"extra": ("a", "b")}, False),
        ("extra != 'a'", {"extra": ("b", "c")}, True),
        ("extra == 'a' and extra == 'b'", {"extra": ("a", "b", "c")}, True),
        ("extra == 'a' and extra == 'b'", {"extra": ("a", "c")}, False),
        ("extra == 'a' or extra == 'b'", {"extra": ("a", "c")}, True),
        ("extra == 'a' or extra == 'b'", {"extra": ("b", "c")}, True),
        ("extra == 'a' or extra == 'b'", {"extra": ("c", "d")}, False),
        ("extra != 'a' and extra != 'b'", {"extra": ("a", "c")}, False),
        ("extra != 'a' and extra != 'b'", {"extra": ("b", "c")}, False),
        ("extra != 'a' and extra != 'b'", {"extra": ("c", "d")}, True),
        ("extra != 'a' or extra != 'b'", {"extra": ("a", "b", "c")}, False),
        ("extra != 'a' or extra != 'b'", {"extra": ("a", "c")}, True),
        ("extra != 'a' or extra != 'b'", {"extra": ("b", "c")}, True),
        ("extra != 'a' and extra == 'b'", {"extra": ("a", "b")}, False),
        ("extra != 'a' and extra == 'b'", {"extra": ("b", "c")}, True),
        ("extra != 'a' and extra == 'b'", {"extra": ("c", "d")}, False),
        ("extra != 'a' or extra == 'b'", {"extra": ("a", "b")}, True),
        ("extra != 'a' or extra == 'b'", {"extra": ("c", "d")}, True),
        ("extra != 'a' or extra == 'b'", {"extra": ("a", "c")}, False),
    ],
)
def test_evaluate_extra(
    marker_string: str, environment: dict[str, str] | None, expected: bool
) -> None:
    m = parse_marker(marker_string)

    assert m.evaluate(environment) is expected


@pytest.mark.parametrize(
    "marker, env",
    [
        (
            'platform_release >= "9.0" and platform_release < "11.0"',
            {"platform_release": "10.0"},
        )
    ],
)
def test_parse_version_like_markers(marker: str, env: dict[str, str]) -> None:
    m = parse_marker(marker)

    assert m.evaluate(env)
