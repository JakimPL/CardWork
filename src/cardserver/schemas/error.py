from cardwork.models.base import BaseFrozen


class ErrorBody(BaseFrozen):
    """A refusal in the shape a client can act on: what kind it was, and what the server made of it.

    The kind is the name of the rule that refused, which lets a client branch on the answer while the
    detail stays a sentence for a person to read.
    """

    error: str
    detail: str
