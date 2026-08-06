from cardwork.exceptions import LogicError


def held[ValueT](value: ValueT | None, subject: str) -> ValueT:
    """The value standing there, read where the rules have already settled that something does.

    A field that holds nothing until the table reaches a certain standing — the seat leading a round, the
    combination the trick stands on — is read back through this once that standing is reached, which leaves
    the reading typed and states the one refusal in a sentence.

    Args:
        value: what stands there, or None where nothing does.
        subject: what is missing, as the refusal states it after the word no.

    Raises:
        LogicError: when nothing stands there.
    """
    if value is None:
        raise LogicError(f"No {subject}")

    return value
