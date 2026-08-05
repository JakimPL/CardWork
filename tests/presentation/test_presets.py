from cardwork.presentation import presets
from cardwork.presentation.interlude import Interlude
from cardwork.rounds.state import MatchPhase


def test_a_match_of_rounds_pauses_where_its_two_reserved_phases_leave_the_table_at_rest() -> None:
    assert presets.match_interludes() == {
        MatchPhase.BETWEEN_ROUNDS: Interlude.ROUND,
        MatchPhase.MATCH_OVER: Interlude.MATCH,
    }
