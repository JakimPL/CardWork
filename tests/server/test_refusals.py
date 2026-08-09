from dataclasses import dataclass
from http import HTTPStatus
from typing import Final

import pytest
from httpx import AsyncClient

from cardserver.schemas import ErrorBody
from tests.cases import Case, descriptions

from .company import CODE, WRONG_CODE
from .conftest import GUESTS, SEAT, arrives, holding

NAMED: Final[str] = "Ada"
NO_SUCH_SEAT: Final[int] = 99
FIRST_REVISION: Final[int] = 1


@dataclass(frozen=True)
class MisstatedCase(Case):
    """One request the schemas turn away, and the field the answer is to name as the one that went wrong."""

    stated: object
    field: str


MISSTATEMENTS: Final[tuple[MisstatedCase, ...]] = (
    MisstatedCase(
        description="an arrival stating nothing of itself",
        stated={},
        field="body.code",
    ),
    MisstatedCase(
        description="an arrival naming a code and no name",
        stated={"code": CODE},
        field="body.name",
    ),
    MisstatedCase(
        description="a body that is text where the schemas read fields, which is what a transport dropping "
        "the content type leaves behind",
        stated="{}",
        field="body",
    ),
    MisstatedCase(
        description="a body that is a list where the schemas read fields",
        stated=[{"code": CODE, "name": NAMED}],
        field="body",
    ),
)


async def test_a_refusal_the_rules_state_carries_the_kind_and_the_sentence(visitor: AsyncClient) -> None:
    answered = await visitor.post(GUESTS, json={"code": WRONG_CODE, "name": NAMED})

    assert answered.status_code == HTTPStatus.FORBIDDEN
    assert ErrorBody.model_validate(answered.json()).error == "Unadmitted"


@pytest.mark.parametrize("case", MISSTATEMENTS, ids=descriptions(MISSTATEMENTS))
async def test_a_request_the_schemas_turn_away_is_refused_in_the_shape_every_refusal_takes(
    visitor: AsyncClient,
    case: MisstatedCase,
) -> None:
    """A misstated request is answered as the rest are, since a page reads one answer and shows one sentence."""
    answered = await visitor.post(GUESTS, json=case.stated)
    refused = ErrorBody.model_validate(answered.json())

    assert answered.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert refused.error == "RequestValidationError"
    assert refused.detail.startswith(f"{case.field}: ")


async def test_a_misstatement_names_every_field_it_got_wrong(visitor: AsyncClient) -> None:
    answered = await visitor.post(GUESTS, json={"code": None, "name": None})
    refused = ErrorBody.model_validate(answered.json())

    assert "body.code: " in refused.detail
    assert "body.name: " in refused.detail


async def test_a_seat_claimed_outside_the_table_is_refused_by_the_rules_rather_than_the_schemas(
    visitor: AsyncClient,
) -> None:
    """A value the schemas admit and the table holds nowhere reaches the rules, which name the refusal."""
    token = await arrives(visitor, NAMED)
    answered = await visitor.put(
        SEAT,
        json={"seat": NO_SUCH_SEAT, "base_revision": FIRST_REVISION},
        headers=holding(token),
    )

    assert answered.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert ErrorBody.model_validate(answered.json()).error == "NoSuchSeat"
