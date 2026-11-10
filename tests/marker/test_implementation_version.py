from __future__ import annotations

import operator

import pytest
from packaging.markers import Marker

from dep_logic.markers import parse_marker


@pytest.mark.parametrize(
    "expression",
    [
        'implementation_version == "3.12" and implementation_version == "3.12.0"',
        'implementation_version == "3.12" or implementation_version == "3.13"',
        'implementation_version != "3.12" and implementation_version != "3.13"',
        'implementation_version == "3.12" and implementation_version != "3.12.0"',
        'implementation_version == "3.12a1" or implementation_version >= "3.12"',
        'implementation_version == "3.12.*" and implementation_version >= "3.12.1"',
        'implementation_version ~= "3.12" and implementation_version < "4"',
        'implementation_version >= "3.12" and implementation_version < "3.13"',
        'implementation_version == "1!3.12" or implementation_version == "1!3.12.0"',
        'implementation_version == "3.12+vendor" or implementation_version == "3.13"',
        '"3.12" == implementation_version or "3.13" == implementation_version',
        '"3.12" != implementation_version and "3.13" != implementation_version',
        'implementation_version in "3.12.0,3.13.0" and implementation_version >= "3.12"',
        'implementation_version not in "3.12.0,3.13.0" or implementation_version <= "3.12"',
        (
            '(implementation_version == "3.12" or implementation_version == "3.13") '
            'and implementation_name == "cpython"'
        ),
    ],
)
@pytest.mark.parametrize(
    "version",
    [
        "3.11.0",
        "3.12a1",
        "3.12a2",
        "3.12",
        "3.12.0",
        "3.12.1",
        "3.13.0",
        "1!3.12.0",
        "3.12+vendor",
    ],
)
def test_implementation_version_preserves_pep440_evaluation(
    expression: str, version: str
) -> None:
    environment = {"implementation_version": version, "implementation_name": "cpython"}
    assert parse_marker(expression).evaluate(
        {"implementation_version": version, "implementation_name": "cpython"}
    ) == Marker(expression).evaluate(environment)


@pytest.mark.parametrize("operation", [operator.and_, operator.or_])
def test_implementation_version_direct_binary_operators(operation) -> None:
    left = 'implementation_version == "3.12"'
    right = 'implementation_version == "3.12.0"'
    marker = operation(parse_marker(left), parse_marker(right))
    for version in ("3.12.0", "3.12.1", "3.13.0"):
        environment = {"implementation_version": version}
        assert marker.evaluate({"implementation_version": version}) == operation(
            Marker(left).evaluate(environment), Marker(right).evaluate(environment)
        )


@pytest.mark.parametrize("operation", ["==", "!=", "<", "<=", ">", ">="])
def test_implementation_version_inversion_preserves_comparisons(operation: str) -> None:
    expression = f'implementation_version {operation} "3.12"'
    inverted = ~parse_marker(expression)
    opposite = {"==": "!=", "!=": "==", "<": ">=", "<=": ">", ">": "<=", ">=": "<"}
    expected = Marker(f'implementation_version {opposite[operation]} "3.12"')
    for version in ("3.11.0", "3.12.0", "3.12.1", "3.13.0"):
        environment = {"implementation_version": version}
        assert inverted.evaluate(
            {"implementation_version": version}
        ) == expected.evaluate(environment)


def test_implementation_version_unknown_literal_keeps_string_fallback() -> None:
    expression = (
        'implementation_version == "unknown" or implementation_version == "other"'
    )
    marker = parse_marker(expression)
    for version in ("unknown", "other", "3.12.0"):
        environment = {"implementation_version": version}
        assert marker.evaluate({"implementation_version": version}) == Marker(
            expression
        ).evaluate(environment)


def test_unrelated_markers_still_simplify() -> None:
    assert parse_marker('os_name == "posix" and os_name == "nt"').is_empty()
    assert parse_marker(
        'python_full_version == "3.12" and python_full_version == "3.12.0"'
    ).evaluate({"python_full_version": "3.12.0"})


@pytest.mark.parametrize("forward_first", [False, True])
@pytest.mark.parametrize("operation", ["and", "or"])
def test_implementation_version_caches_preserve_operand_direction(
    forward_first: bool, operation: str
) -> None:
    forward = 'implementation_version == "3.12"'
    reverse = '"3.12" == implementation_version'
    comparisons = (forward, reverse) if forward_first else (reverse, forward)
    environment = {
        "implementation_version": "3.12+vendor",
        "implementation_name": "cpython",
    }
    for comparison in comparisons:
        expression = (
            f'({comparison} or implementation_version == "3.12a1") '
            f'{operation} implementation_name == "cpython"'
        )
        assert parse_marker(expression).evaluate(
            {
                "implementation_version": "3.12+vendor",
                "implementation_name": "cpython",
            }
        ) == Marker(expression).evaluate(environment)


@pytest.mark.parametrize("operation", ["and", "or"])
@pytest.mark.parametrize("comparison", ["==", "!="])
@pytest.mark.parametrize("forward_first", [False, True])
def test_implementation_version_keeps_mixed_direction_atoms(
    operation: str, comparison: str, forward_first: bool
) -> None:
    forward = f'implementation_version {comparison} "3.12"'
    reverse = f'"3.12" {comparison} implementation_version'
    left, right = (forward, reverse) if forward_first else (reverse, forward)
    expression = f"({left}) {operation} ({right})"
    environment = {"implementation_version": "3.12+vendor"}
    assert parse_marker(expression).evaluate(
        {"implementation_version": "3.12+vendor"}
    ) == Marker(expression).evaluate(environment)


def test_operand_direction_identity_is_specific_to_implementation_version() -> None:
    forward = parse_marker('implementation_version == "3.12"')
    reverse = parse_marker('"3.12" == implementation_version')
    assert forward != reverse
    assert len({forward, reverse}) == 2
    assert parse_marker('os_name == "posix"') == parse_marker('"posix" == os_name')
