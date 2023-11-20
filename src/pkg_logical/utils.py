from __future__ import annotations

import re
from typing import Iterable, Literal, Protocol, TypeVar

_prefix_regex = re.compile(r"^([0-9]+)((?:a|b|c|rc)[0-9]+)$")


class Unique(Protocol):
    def __hash__(self) -> int:
        ...

    def __eq__(self, __value: object) -> bool:
        ...


T = TypeVar("T", bound=Unique)
V = TypeVar("V")


def version_split(version: str) -> list[str]:
    result: list[str] = []
    for item in version.split("."):
        match = _prefix_regex.search(item)
        if match:
            result.extend(match.groups())
        else:
            result.append(item)
    return result


def is_not_suffix(segment: str) -> bool:
    return not any(
        segment.startswith(prefix) for prefix in ("dev", "a", "b", "rc", "post")
    )


def flatten_items(items: Iterable[T], flatten_cls: type[Iterable[T]]) -> list[T]:
    flattened: list[T] = []
    for item in items:
        if isinstance(item, flatten_cls):
            for subitem in flatten_items(item, flatten_cls):
                if subitem not in flattened:
                    flattened.append(subitem)
        elif item not in flattened:
            flattened.append(item)
    return flattened


def first_different_index(
    iterable1: Iterable[object], iterable2: Iterable[object]
) -> int:
    for index, (item1, item2) in enumerate(zip(iterable1, iterable2)):
        if item1 != item2:
            return index
    return index + 1


def pad_zeros(parts: list[V], to_length: int) -> list[V | Literal[0]]:
    if len(parts) >= to_length:
        return parts
    return parts + [0] * (to_length - len(parts))
