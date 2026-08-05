from typing import Self

from cardwork.models.base import BaseFrozen
from cardwork.presentation.repeats import repeated
from cardwork.presentation.scope import Scope
from cardwork.states.state import GameState


class Readout(BaseFrozen):
    """A field of the cursor shown to the player, under the word the game calls it by.

    Every number and word an interface states about where play stands is one of these, so the score, the round
    in play and a game's own tallies all reach the screen by one route and no interface holds the name of a
    field a particular game declares. `field` names a field of the state the game is played with, and `scope`
    says whether that field speaks about the table or about each seat in turn.

    `of` builds one against the state class that declares the field, which is what keeps the name honest.
    """

    field: str
    label: str
    scope: Scope

    @classmethod
    def of(
        cls,
        state: type[GameState],
        field: str,
        label: str,
        *,
        scope: Scope,
    ) -> Self:
        """A readout of one field, read against the state that declares it so the reference holds.

        A layout states the fields of its own game's cursor by name, and that name is the one part of a layout
        only the game itself vouches for: a field renamed leaves a readout pointing at a name the cursor has
        dropped, and the interface shows a blank where a figure belongs. The state class settles it, and it
        belongs to the game rather than to the layout drawn from it, so it arrives as an argument here and
        stays out of the model a client reads.

        Args:
            state: the game's own state class, whose declared fields the name is looked for among.
            field: the name of the field to show.
            label: the word to show it under.
            scope: whether the field speaks about the table or about each seat.

        Raises:
            ValueError: when the state declares no field of that name.
        """
        if field not in state.model_fields:
            raise ValueError(f"{state.__name__} declares no field {field!r} for a readout to show")

        return cls(field=field, label=label, scope=scope)


def misread(readouts: tuple[Readout, ...]) -> str | None:
    """What a run of readouts gets wrong, and None where every field of the cursor reads once.

    A figure shown twice under two words leaves a player weighing which of them to believe, so one field takes
    one readout. A `Layout` and the `Scene` it is drawn from are held to this one rule.

    Args:
        readouts: the readouts of one run, in the order they are shown.
    """
    twice = repeated(tuple(readout.field for readout in readouts))
    if twice:
        return f"A field of the cursor reads once, and these take two readouts apiece: {twice}"

    return None
