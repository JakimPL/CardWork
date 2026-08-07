from cardwork.models.base import BaseFrozen


class CommandAccepted(BaseFrozen):
    """The sequence a command was committed at, which the table stands one commit past.

    A client holding this commit stands at `seq + 1` commits, and that count is what its next command quotes
    as `base_seq`. A move and an arrangement are answered alike, since what either of them leaves behind is
    one commit in the record every seat reads.
    """

    seq: int
