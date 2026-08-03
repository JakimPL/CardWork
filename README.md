# CardWork

A framework for server-authoritative, transactional playing-card games with partial knowledge.

Two packages:

- **`cardwork`** — the engine. Synchronous and pure: a position is a value, a move produces another
  value, and every commit is recorded as data that replays exactly.
- **`cardserver`** — a FastAPI adapter that puts tables into service over HTTP and server-sent events.

`docs/architecture.md` is the design and the reasoning behind it. What follows is enough to start.

## Getting set up

```bash
make install      # uv sync --all-extras
make check        # lint, mypy --strict, import contracts, coverage
make test         # pytest -n auto
```

## Writing a game

A game subclasses `Game` and fills in the rules hooks. Every hook takes the position it operates on, so
the same rules serve a live table, a replay and a search.

```python
from random import Random

from cardwork.decks.deck import Deck
from cardwork.effects.effects import Effects
from cardwork.games.game import Game
from cardwork.moves.move import Move
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.zones.zone import Zones


class Trump(GameState):
    """A game's own state, with its own typed fields."""

    suit: str | None = None


Table = Position[Trump]
Changes = Effects[Trump]


class MyGame(Game[Trump]):
    def zones(self, players: int, deck: Deck) -> Zones: ...        # the table before anyone touches it
    def _initialize(self, players: int) -> Trump: ...              # the pre-deal cursor
    def _deal_cards(self, position: Table, rng: Random) -> Changes: ...   # shuffle and distribute
    def _validate_players(self, players: int) -> None: ...
    def _validate_initial_deck(self, deck: Deck) -> None: ...
    def _final_validation(self, position: Table) -> None: ...

    def validate(self, position: Table, move: Move) -> None: ...   # raise IllegalMove
    def expand(self, position: Table, move: Move, rng: Random) -> Changes: ...  # intent -> effects
    def advance(self, position: Table, move: Move | None) -> Changes: ...  # turn, phase, scoring
```

Two hooks ship with a body and are overridden only to change a policy: `authorize`, which admits the seats
`to_act` names, and `legal_moves`, which enumerates nothing until a game chooses to.

Four rules of thumb, each explained at length in `docs/architecture.md`:

1. **Randomness is recorded, not re-rolled.** A shuffle is a `Reorder` carrying the permutation that
   `decks.draw.permutation(size, rng)` drew. `rng` reaches `_deal_cards` and `expand`, and nowhere else.
2. **The turn is a set.** `to_act == {p}` is sequential play; `to_act == {0, 1, 2}` is simultaneous, and the
   phase resolves when it empties. `advance` receives the move that led here, or `None` while the table
   settles on its own.
3. **Secrecy comes from zones.** A card's `face_down` is physical; who that conceals it from is the zone's
   `Visibility`. Sealing a commitment is moving cards face-down into a `HAND` zone the seat owns — opponents
   read the count and nothing else.
4. **Build the next cursor with `state.with_changes(...)`** and hand it to `SetState`, which validates it
   against your own declared fields.

`tests/games/demo.py` is a small, complete exercise game: a simultaneous round with sealed commitments, a
reveal, scoring and take-backs.

## Serving it

```python
from cardserver import TableRegistry, TokenSeats, create_app
from cardwork.decks.standard import standard_deck

registry: TableRegistry[Trump] = TableRegistry(grace_seconds=2.0)
session = registry.open("green-baize", MyGame(players=3, deck=standard_deck()))

app = create_app(registry, TokenSeats({"green-baize": {"tok-0": 0, "tok-1": 1, "tok-2": 2}}))
```

Run it with `uvicorn`, and the table answers four endpoints:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/tables/{id}/moves` | Submit `{move, base_seq, idempotency_key}`; answers `{seq}` |
| `GET` | `/tables/{id}/view` | This observer's projection of the table, stamped with `seq` |
| `GET` | `/tables/{id}/events` | SSE stream of projected commits, resumable via `Last-Event-ID` |
| `GET` | `/tables/{id}/journal` | The full record, once `session.reveal()` has opened it |

A client identifies itself with the `X-Seat-Token` header; a request without one watches as a spectator.
Each response carries what that observer is entitled to know, and nothing further.

Two decisions the host makes:

- **`grace_seconds`** is how long a closed round stays open for a seat to retract its commitment. Each
  command restarts the wait, and the rules decide whether a retraction is still in time.
- **`session.reveal()`** opens a table's full record for analysis. Until then `/journal` answers `403`,
  since the record names every card a seat still holds.
