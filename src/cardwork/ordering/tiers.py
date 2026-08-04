from collections.abc import Hashable, Sequence

from cardwork.ordering.preorder import Key, Preorder


class Tiers[T: Hashable](Preorder[T]):
    """An order over a listed run of values, each taking the place its position in the list names."""

    def __init__(self, sequence: Sequence[T]) -> None:
        self._places: dict[T, int] = {value: place for place, value in enumerate(sequence)}
        if len(self._places) != len(sequence):
            raise ValueError(f"Every value takes one place, and {len(sequence)} of them fill {len(self._places)}")

    def key(self, value: T) -> Key:
        if value not in self._places:
            raise KeyError(f"{value!r} takes no place among the {len(self._places)} values this order lists")

        return (self._places[value],)
