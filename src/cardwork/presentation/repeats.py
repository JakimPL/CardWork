from collections import Counter
from collections.abc import Hashable


def distinct[ValueT: Hashable](
    values: tuple[ValueT, ...],
) -> tuple[ValueT, ...]:
    """The values, each named a single time, in the order they first appear."""
    return tuple(dict.fromkeys(values))


def repeated[ValueT: Hashable](
    values: tuple[ValueT, ...],
) -> tuple[ValueT, ...]:
    """The values appearing more than once, each named a single time, in the order they first appear."""
    counts = Counter(values)
    return tuple(value for value in distinct(values) if counts[value] > 1)
