from typing import Final

from cardwork.presentation import presets
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.scope import Scope
from cardwork.rounds.state import MatchPhase, RoundState

STANDING: Final[str] = "points"
ROUND_AWARD: Final[str] = "round_points"
ROUND_IN_PLAY: Final[str] = "round_number"


def test_a_match_of_rounds_pauses_where_its_two_reserved_phases_leave_the_table_at_rest() -> None:
    assert presets.match_interludes() == {
        MatchPhase.BETWEEN_ROUNDS: Interlude.ROUND,
        MatchPhase.MATCH_OVER: Interlude.MATCH,
    }


def test_a_match_of_rounds_captions_the_two_phases_it_pauses_at() -> None:
    """A layout is held to captioning every phase play pauses at, so the pair states the words for its own two."""
    assert presets.match_phases() == {
        MatchPhase.BETWEEN_ROUNDS: "Between rounds",
        MatchPhase.MATCH_OVER: "Match over",
    }
    assert presets.match_phases().keys() == presets.match_interludes().keys()


def test_a_match_of_rounds_shows_the_standing_the_round_it_scores_and_the_round_in_play() -> None:
    readouts = presets.match_readouts(RoundState)

    assert [(readout.field, readout.label, readout.scope) for readout in readouts] == [
        (STANDING, "Points", Scope.SEAT),
        (ROUND_AWARD, "This round", Scope.SEAT),
        (ROUND_IN_PLAY, "Round", Scope.TABLE),
    ]
