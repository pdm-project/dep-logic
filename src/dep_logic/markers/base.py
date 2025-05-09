from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, Literal

EvaluationContext = Literal["lock_file", "metadata", "requirement"]


class BaseMarker(metaclass=ABCMeta):
    @property
    def complexity(self) -> tuple[int, ...]:
        """
        The first number is the number of marker expressions,
        and the second number is 1 if the marker is single-like.
        """
        return 1, 1

    @abstractmethod
    def __and__(self, other: Any) -> BaseMarker:
        raise NotImplementedError

    @abstractmethod
    def __or__(self, other: Any) -> BaseMarker:
        raise NotImplementedError

    def is_any(self) -> bool:
        """Returns True if the marker allows any environment."""
        return False

    def is_empty(self) -> bool:
        """Returns True if the marker disallows any environment."""
        return False

    @abstractmethod
    def evaluate(
        self,
        environment: dict[str, str | set[str]] | None = None,
        context: EvaluationContext = "metadata",
    ) -> bool:
        """Evaluates the marker against the given environment.

        Args:
            environment: The environment to evaluate against.
            context: The context in which the evaluation is performed,
                can be "lock_file", "metadata", or "requirement".
        """
        raise NotImplementedError

    @abstractmethod
    def without_extras(self) -> BaseMarker:
        """Generate a new marker from the current marker but without "extra" markers."""
        raise NotImplementedError

    @abstractmethod
    def exclude(self, marker_name: str) -> BaseMarker:
        """Generate a new marker from the current marker but without the given marker."""
        raise NotImplementedError

    @abstractmethod
    def only(self, *marker_names: str) -> BaseMarker:
        """Generate a new marker from the current marker but only with the given markers."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self}>"

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError
