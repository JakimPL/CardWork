from enum import Enum


class Creation(str, Enum):
    """Who may gather a table here: everyone, the overseer alone, or everyone until the overseer says otherwise.

    A friendly host lets the company gather its own tables, a guarded one keeps the opening of them to whoever
    runs it, and a hybrid one starts open and closes on a word: the overseer settling it to `admin-only` is what
    turns a run from the first into the second without a restart.
    """

    SELF_SERVE = "self-serve"
    ADMIN_ONLY = "admin-only"
    HYBRID = "hybrid"

    @property
    def open_to_guests(self) -> bool:
        """Whether a guest may gather a table, which everything but a run kept to its overseer admits."""
        return self is not Creation.ADMIN_ONLY
