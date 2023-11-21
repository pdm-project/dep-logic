# Dep-Logic

Python dependency specifications supporting logical operations

This library requires Python 3.8 or later.

Currently, we have two sub-modules:

- `dep_logic.specifier` - a module for parsing and calculating PEP 440 version specifiers.
- `dep_logic.markers` - a module for parsing and calculating PEP 508 environment markers.

## Caveats

`===` operator is not supported for logic operations.
