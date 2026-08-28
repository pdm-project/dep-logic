from __future__ import annotations

from typing import Any

from dep_logic.markers.base import BaseMarker, EvaluationContext


class EmptyMarker(BaseMarker):
    def __invert__(self) -> BaseMarker:
        from dep_logic.markers.any import AnyMarker

        return AnyMarker()

    def __and__(self, other: Any) -> BaseMarker:
        if not isinstance(other, BaseMarker):
            return NotImplemented
        return self

    __rand__ = __and__

    def __or__(self, other: Any) -> BaseMarker:
        if not isinstance(other, BaseMarker):
            return NotImplemented
        return other

    __ror__ = __or__

    def is_empty(self) -> bool:
        return True

    def evaluate(
        self,
        environment: dict[str, str | set[str]] | None = None,
        context: EvaluationContext = "metadata",
    ) -> bool:
        return False

    def without_extras(self) -> BaseMarker:
        return self

    def exclude(self, marker_name: str) -> BaseMarker:
        return self

    def only(self, *marker_names: str) -> BaseMarker:
        return self

    def __str__(self) -> str:
        return "<empty>"

    def __repr__(self) -> str:
        return "<EmptyMarker>"

    def __hash__(self) -> int:
        return hash("empty")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseMarker):
            return NotImplemented

        return other.is_empty()
