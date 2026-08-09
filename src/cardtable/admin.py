from cardwork.models.base import BaseFrozen


class Admin(BaseFrozen):
    """The credential the overseer's panel answers behind: a secret a file pins, or a token minted as a run starts.

    A run stating a secret oversees under that same token every time it starts, which is what lets a deployment
    hold one panel across a restart and pin it out of band. A run stating none is minted a fresh token as it
    starts and reads it out where the join code is, so the panel a run leaves behind it answers to whoever
    started that run and to nobody it hands a table to.

    The secret is asked for outright the way the rest of a run is, so a file states which of the two it means
    rather than leaving it to be met as a surprise in service.
    """

    secret: str | None
