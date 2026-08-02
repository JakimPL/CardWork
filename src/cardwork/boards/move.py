from collections.abc import Callable
from functools import wraps
from typing import Concatenate, ParamSpec, TypeVar

from cardwork.cards.deck import Group, Indices, Variant

P = ParamSpec("P")
R = TypeVar("R")
S = TypeVar("S")


def validate_indices(
    collection: Variant,
    indices: Indices,
) -> None:
    if not indices:
        return

    max_index = max(indices)
    size = len(collection)
    if max_index >= size:
        raise KeyError(f"Index {max_index} exceeds the size {size} of the collections")


def pop_cards(
    collection: Variant,
    remove: Indices,
) -> Group:
    kept: Group = []
    popped: Group = []

    for i, item in enumerate(collection):
        if i in remove:
            popped.append(item)
        else:
            kept.append(item)

    collection.clear()
    collection.extend(kept)
    return popped


def transfer_cards(
    method: Callable[Concatenate[S, Group, P], R],
) -> Callable[Concatenate[S, Variant, Indices, P], R]:
    """
    Turn a method taking the popped cards into one taking a collection
    and the indices to take from it.
    """

    @wraps(method)
    def wrapper(
        instance: S,
        collection: Variant,
        indices: Indices,
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        validate_indices(collection, indices)
        cards = pop_cards(collection, indices)
        return method(instance, cards, *args, **kwargs)

    return wrapper
