from typing import Final

import pytest

from cardserver.errors import NoSay, NotReady, NotTheHost, SeatsHeld
from cardserver.gathering import TINTS
from cardserver.schemas import Choosing, Founding, Governing

from ..games.demo import SEATS
from .company import Gathered, a_sealed_round
from .conftest import ATTENDANCE, TABLE, holding
from .harness import Following

COMPANY: Final[tuple[str, ...]] = ("Ada", "Grace", "Alan")
A_FREE_TINT = TINTS[-1]
HOSTED: Final[str] = "hosted-table"
A_SMALLER_TABLE: Final[int] = 2


def a_seated_company(gathered: Gathered) -> None:
    """The demo table with all its seats taken, which is a company one commitment short of a deal."""
    gathering = gathered.gathering
    for seat, name in enumerate(COMPANY):
        gathering.admit(name)
        gathering.claim(name, seat, gathering.revision)


def readies(gathered: Gathered) -> None:
    """Every seated guest of the demo company committing to the settings as they stand."""
    gathering = gathered.gathering
    for name in COMPANY:
        gathering.ready(name, True, gathering.revision)


def committed(gathered: Gathered, name: str) -> bool:
    """Whether one guest of the company is read as committed to the settings as they stand."""
    guest = next(guest for guest in gathered.gathering.view(name).company if guest.name == name)
    return guest.ready


def test_a_settings_change_takes_back_every_commitment(gathered: Gathered) -> None:
    a_seated_company(gathered)
    readies(gathered)

    gathered.gathering.choose("Ada", a_sealed_round(SEATS), gathered.gathering.revision)

    assert not any(committed(gathered, name) for name in COMPANY)


def test_a_seat_change_takes_back_every_commitment(gathered: Gathered) -> None:
    a_seated_company(gathered)
    readies(gathered)

    gathered.gathering.claim("Alan", None, gathered.gathering.revision)

    assert not committed(gathered, "Ada")


def test_a_tint_leaves_every_commitment_where_it_stood(gathered: Gathered) -> None:
    """A tint is no part of what is played, so taking one is the one change readiness reads nothing of."""
    a_seated_company(gathered)
    readies(gathered)

    gathered.gathering.tint("Ada", A_FREE_TINT, gathered.gathering.revision)

    assert committed(gathered, "Ada")


def test_a_standing_guest_commits_nothing(gathered: Gathered) -> None:
    gathered.gathering.admit("Ada")

    with pytest.raises(NoSay):
        gathered.gathering.ready("Ada", True, gathered.gathering.revision)


def test_the_deal_waits_on_every_seat_committing(gathered: Gathered) -> None:
    a_seated_company(gathered)
    gathered.gathering.ready("Ada", True, gathered.gathering.revision)
    gathered.gathering.ready("Grace", True, gathered.gathering.revision)

    with pytest.raises(NotReady):
        gathered.gathering.deal(gathered.gathering.revision)

    assert gathered.deals.dealt == []


def test_a_company_of_one_mind_is_dealt(gathered: Gathered) -> None:
    a_seated_company(gathered)
    readies(gathered)

    gathered.gathering.deal(gathered.gathering.revision)

    assert gathered.gathering.dealt is True
    assert [table for table, _, _ in gathered.deals.dealt] == [TABLE]


def test_founding_a_table_hands_the_host_a_code_and_a_token(gathered: Gathered) -> None:
    admitted = gathered.gatherings.create(
        Founding(
            table=HOSTED,
            name="Ada",
            choice=a_sealed_round(A_SMALLER_TABLE),
        ),
        democratic=False,
    )

    host = next(guest for guest in admitted.gathering.company if guest.name == "Ada")

    assert admitted.token
    assert host.host is True
    assert gathered.gatherings.at(HOSTED).host == "Ada"


def test_shrinking_a_table_under_a_seat_its_company_holds_is_refused(gathered: Gathered) -> None:
    """A player in the last seat holds a table that size open, so a smaller one is weighed by where they sit."""
    gathering = gathered.gathering
    for name, seat in (("Grace", 0), ("Ada", SEATS - 1)):
        gathering.admit(name)
        gathering.claim(name, seat, gathering.revision)

    with pytest.raises(SeatsHeld):
        gathering.choose("Grace", a_sealed_round(SEATS - 1), gathering.revision)


def test_a_guest_may_shrink_a_table_no_one_holds_the_far_seats_of(gathered: Gathered) -> None:
    gathering = gathered.gathering
    gathering.admit("Ada")
    gathering.claim("Ada", 0, gathering.revision)

    gathering.choose("Grace", a_sealed_round(SEATS - 1), gathering.revision)

    assert gathering.view("Ada").choice.players == SEATS - 1


def test_the_host_may_shrink_a_table_standing_a_seated_player_up(gathered: Gathered) -> None:
    gathered.gatherings.create(
        Founding(table=HOSTED, name="Ada", choice=a_sealed_round(SEATS)),
        democratic=True,
    )
    hosted = gathered.gatherings.at(HOSTED)
    hosted.claim("Ada", 0, hosted.revision)
    hosted.admit("Grace")
    hosted.claim("Grace", SEATS - 1, hosted.revision)

    hosted.choose("Ada", a_sealed_round(SEATS - 1), hosted.revision)

    assert hosted.seat_of("Grace") is None
    assert hosted.seat_of("Ada") == 0


def test_a_table_governed_by_its_host_gives_a_seated_guest_no_say(gathered: Gathered) -> None:
    gathered.gatherings.create(
        Founding(table=HOSTED, name="Ada", choice=a_sealed_round(A_SMALLER_TABLE)),
        democratic=False,
    )
    hosted = gathered.gatherings.at(HOSTED)
    hosted.claim("Ada", 0, hosted.revision)
    hosted.admit("Grace")
    hosted.claim("Grace", 1, hosted.revision)

    gathered.gatherings.choose(
        HOSTED,
        "Ada",
        Choosing(choice=a_sealed_round(A_SMALLER_TABLE), base_revision=hosted.revision),
    )

    with pytest.raises(NoSay):
        gathered.gatherings.choose(
            HOSTED,
            "Grace",
            Choosing(choice=a_sealed_round(A_SMALLER_TABLE), base_revision=hosted.revision),
        )


def test_governing_a_table_is_the_host_s_alone(gathered: Gathered) -> None:
    gathered.gatherings.create(
        Founding(
            table=HOSTED,
            name="Ada",
            choice=a_sealed_round(A_SMALLER_TABLE),
        ),
        democratic=False,
    )
    hosted = gathered.gatherings.at(HOSTED)
    hosted.admit("Grace")
    hosted.claim("Grace", 1, hosted.revision)

    with pytest.raises(NotTheHost):
        gathered.gatherings.govern(HOSTED, "Grace", Governing(democratic=False, base_revision=hosted.revision))

    gathered.gatherings.govern(HOSTED, "Ada", Governing(democratic=False, base_revision=hosted.revision))

    assert gathered.gatherings.at(HOSTED).democratic is False


def test_breaking_a_gathering_up_closes_it_with_a_word_on_why(gathered: Gathered) -> None:
    gathered.gathering.admit("Ada")

    gathered.gatherings.break_up(TABLE, "the host called it a night")

    view = gathered.gathering.view("Ada")

    assert view.closed is True
    assert view.reason == "the host called it a night"


async def test_a_broken_up_gathering_is_the_last_thing_a_stream_carries(gathered: Gathered) -> None:
    token = gathered.gathering.admit("Ada")

    async with Following(gathered.app, ATTENDANCE, holding(token)) as stream:
        await stream.frame()
        gathered.gatherings.break_up(TABLE, "closing up")
        closed = await stream.frame()
        nothing_after = await stream.quiet()

    assert "event: closed" in closed
    assert "closing up" in closed
    assert nothing_after is True
