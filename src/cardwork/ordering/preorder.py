from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence

type Key = tuple[int, ...]
type Positions = tuple[int, ...]


class Preorder[T](ABC):
    """A total preorder over one kind of value, carried by the place each value takes in it.

    The relation is `left ≾ right`, read as "the left value stands no higher than the right", and it is
    reflexive and transitive. One mapping realises it: every value has a key, and `left ≾ right` holds
    exactly where `key(left) <= key(right)` compares those keys left to right. Two properties follow, and
    both are the reason for the structure:

    - **Places carry the order, and values take places.** Several values may share a key, and values
      sharing one stand alongside each other here — which is what lets an order by rank hold 7♠ and 7♥ in
      a single place. The values sharing a key are precisely one equivalence class of the relation.
    - **Every pair compares.** Keys stand in a line, so "which of these two stands higher" always has an
      answer, and the top of a run is the set of values reaching it.

    A key is a tuple, which gives refinement directly: one order refines another by concatenating their
    keys, so rank before suit reaches a single winner out of any pair, and a ranking reads its tier first
    and settles the rest afterwards. Carrying a place as a key also means putting a run of values in order
    costs one sort.

    Strength that answers to a situation — the suit led to a trick, the trump a hand agreed — belongs to
    that situation, and a game states it by choosing the order the situation calls for.
    """

    @abstractmethod
    def key(self, value: T) -> Key:
        """Where the value sits in this order, read left to right.

        Raises:
            KeyError: when the order holds no place for the value.
        """

    def compare(self, left: T, right: T) -> int:
        """-1, 0 or 1 as the left value sits below, alongside, or above the right one."""
        left_key = self.key(left)
        right_key = self.key(right)
        if left_key == right_key:
            return 0

        return -1 if left_key < right_key else 1

    def equivalent(self, left: T, right: T) -> bool:
        """Whether both values occupy one place, as two cards of a single rank do."""
        return self.key(left) == self.key(right)

    def ascending(self, values: Iterable[T]) -> tuple[T, ...]:
        """The values from the lowest place upwards, ones sharing a place keeping the order given."""
        return tuple(sorted(values, key=self.key))

    def descending(self, values: Iterable[T]) -> tuple[T, ...]:
        """The values from the highest place downwards, ones sharing a place keeping the order given."""
        return tuple(sorted(values, key=self.key, reverse=True))

    def maxima(self, values: Iterable[T]) -> tuple[T, ...]:
        """Every value standing at the top of the order, which is several wherever the top is shared."""
        ordered = tuple(values)
        return tuple(ordered[place] for place in self.argmaxima(ordered))

    def minima(self, values: Iterable[T]) -> tuple[T, ...]:
        """Every value standing at the foot of the order, which is several wherever the foot is shared."""
        ordered = tuple(values)
        return tuple(ordered[place] for place in self.argminima(ordered))

    def argmaxima(self, values: Sequence[T]) -> Positions:
        """The positions of the values standing at the top, and none of them from an empty run."""
        return self._extremes(values, highest=True)

    def argminima(self, values: Sequence[T]) -> Positions:
        """The positions of the values standing at the foot, and none of them from an empty run."""
        return self._extremes(values, highest=False)

    def _extremes(
        self,
        values: Sequence[T],
        *,
        highest: bool,
    ) -> Positions:
        """The positions of every value whose key reaches one end of the run."""
        keys = [self.key(value) for value in values]
        if not keys:
            return ()

        reached = max(keys) if highest else min(keys)
        return tuple(place for place, key in enumerate(keys) if key == reached)
