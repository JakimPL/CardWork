from cardwork.ordering.preorder import Key, Preorder


class Composite[T](Preorder[T]):
    """One order refined by the next: their keys concatenated, and so read in the order given.

    Rank before suit turns a preorder into a total order; the same composition compares two straights by
    their top card and then by whatever a game wants to settle the rest.
    """

    def __init__(self, *orders: Preorder[T]) -> None:
        if not orders:
            raise ValueError("A composite order refines at least one order")

        self._orders = orders

    def key(self, value: T) -> Key:
        return tuple(place for order in self._orders for place in order.key(value))
