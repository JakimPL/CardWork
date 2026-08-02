from random import Random


def permutation(size: int, rng: Random) -> tuple[int, ...]:
    """Draw a shuffle as data: the source positions in the order they come to occupy.

    Randomness is resolved once, while a move expands, and travels onwards inside a `Reorder` effect.
    The journal then records the outcome itself, so replay reproduces the shuffle exactly from that
    record alone.

    Args:
        size: how many positions take part in the shuffle; must be at least 0.
        rng: the generator to consume, supplied by the caller so the draw stays reproducible.
    """
    order = list(range(size))
    rng.shuffle(order)
    return tuple(order)
