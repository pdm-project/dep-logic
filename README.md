# Dep-Logic

![PyPI - Version](https://img.shields.io/pypi/v/dep-logic)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fpdm-project%2Fdep-logic%2Fmain%2Fpyproject.toml)
![GitHub License](https://img.shields.io/github/license/pdm-project/dep-logic)


Python dependency specifications supporting logical operations

## Installation

```bash
pip install dep-logic
```

This library requires Python 3.8 or later.

Currently, it contains two sub-modules:

- `dep_logic.specifier` - a module for parsing and calculating PEP 440 version specifiers.
- `dep_logic.markers` - a module for parsing and calculating PEP 508 environment markers.

## What does it do?

This library allows logic operations on version specifiers and environment markers.

For example:

```pycon
>>> from dep_logic.specifiers import parse_version_specifier
>>>
>>> a = parse_version_specifier(">=1.0.0")
>>> b = parse_version_specifier("<2.0.0")
>>> print(a & b)
>=1.0.0,<2.0.0
>>> a = parse_version_specifier(">=1.0.0,<2.0.0")
>>> b = parse_version_specifier(">1.5")
>>> print(a | b)
>=1.0.0
```

For markers:

```pycon
>>> from dep_logic.markers import parse_marker
>>> m1 = parse_marker("python_version < '3.8'")
>>> m2 = parse_marker("python_version >= '3.6'")
>>> print(m1 & m2)
python_version < "3.8" and python_version >= "3.6"
```

## About the project

This project is based on @sdispater's [poetry-core](https://github.com/python-poetry/poetry-core) code, but it includes additional packages and a lark parser, which increases the package size and makes it less reusable.

Furthermore, `poetry-core` does not always comply with PEP-508. As a result, this project aims to offer a lightweight utility for dependency specification logic using [PyPA's packaging](https://github.com/pypa/packaging).

Submodules:

- `dep_logic.specifiers` - PEP 440 version specifiers
- `dep_logic.markers` - PEP 508 environment markers
- `dep_logic.tags` - PEP 425 platform tags

## Caveats

Logic operations with `===<string>` specifiers is partially supported.
