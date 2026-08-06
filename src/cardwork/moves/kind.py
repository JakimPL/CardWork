from enum import StrEnum


class ActionKind(StrEnum):
    """The word an action carries as its tag, which is what tells one intent from another on the wire.

    The tag is the discriminator of `AnyAction`, so a client sending a move names one of these and a layer
    reading a move back branches on it. Naming the vocabulary here lets anything that speaks about a kind of
    move — a presentation layer saying which gesture puts one on the table — hold a member rather than a
    string that happens to match.
    """

    PASS = "pass"
    PLAY = "play"
    TAKE = "take"
    GIVE = "give"
    REJECT = "reject"
    DISCARD = "discard"
    DECLARE = "declare"
