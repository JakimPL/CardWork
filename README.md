# CardWork

A framework for server-authoritative, transactional playing-card games with partial knowledge.

Four packages:

- **`cardwork`** — the engine. Synchronous and pure: a position is a value, a move produces another
  value, and every commit is recorded as data that replays exactly.
- **`cardserver`** — a FastAPI adapter that puts tables into service over HTTP and server-sent events.
- **`cardgames`** — the games written on it, each stated twice over: `backend` holds a game's rules and
  `frontend` the layout a player reads them through. `passing` is a game of four cards played in turn;
  `showdown`, a game of ten turns played at once.
- **`cardtable`** — the host: it opens a table of a chosen game, hands out a token per seat, and serves
  the player interface beside the endpoints. The one place a game and a transport meet.

`docs/architecture.md` is the design and the reasoning behind it; `docs/combinations.md`, `docs/rounds.md`,
`docs/presentation.md` and `docs/games/` state the parts a game reaches for and the two games themselves. What
follows is enough to start.

## Getting set up

```bash
make install      # uv sync --all-extras
make check        # lint, mypy --strict, import contracts, coverage
make test         # pytest -n auto
make play         # open a table and answer for it; GAME=showdown PLAYERS=4 to choose
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
    def advance(self, position: Table, move: Move | None, rng: Random) -> Changes: ...  # turn, phase, scoring
```

Two hooks ship with a body and are overridden only to change a policy: `authorize`, which admits the seats
`to_act` names, and `legal_moves`, which enumerates nothing until a game chooses to. A game that does
enumerate has them reach every client, since a view and an event each carry the moves their observer may make.

## Laying a game out

A game states how it is played under `cardgames.backend.<game>` and how it is read under
`cardgames.frontend.<game>`, which is one `Scene`:

```python
MYGAME_SCENE: Final[Scene] = Scene(
    title="My game",
    shared=(presets.heap(DISCARD, "Discard", place=0),),   # the zones every observer reads alike
    held=slots_of,           # seat -> the zones it holds, where they sit, how their cards lie
    gestures=gestures_of,    # seat -> which move a selection sends, and what is clicked to send it
    counts=counts_of,        # seat -> the zones of its own the table reads the size of
    readouts=READOUTS,       # Readout.of(MyState, "suit", "Trump", scope=Scope.TABLE)
    phases=PHASES,           # what each phase is called in words
)

layout = MYGAME_SCENE.layout(players=3, observer=1)
```

`Scene.layout` reads those three functions at one seat and builds that observer's `Layout`: its own zones
beside the shared ones, its own gestures, and a plaque for every seat. A spectator gets the shared table and
no gesture, which is the entitlement the projection gives it over the cards — stated once here rather than in
each game.

The rules name the layout nowhere, so a game plays with no screen attached; the layout names the rules for
their zone ids and phases, so no string is written twice. `docs/presentation.md` states the vocabulary.

Four rules of thumb, each explained at length in `docs/architecture.md`:

1. **Randomness is recorded, not re-rolled.** A shuffle is a `Reorder` carrying the permutation that
   `decks.draw.permutation(size, rng)` drew. `rng` reaches `_deal_cards`, `expand` and `advance`, and
   nowhere else.
2. **The turn is a set.** `to_act == {p}` is sequential play; `to_act == {0, 1, 2}` is simultaneous, and the
   phase resolves when it empties. `advance` receives the move that led here, or `None` while the table
   settles on its own.
3. **Secrecy comes from zones.** A card's `face_down` is physical; who that conceals it from is the zone's
   `Visibility`. Sealing a commitment is moving cards face-down into a `HAND` zone the seat owns — opponents
   read the count and nothing else — and a `HIDDEN` zone seals it from its owner too.
4. **Build the next cursor with `state.with_changes(...)`** and hand it to `SetState`, which validates it
   against your own declared fields.

## Four things a game reaches for

Rules that more than one game wants live in the framework, each in a layer of its own:

- **`cardwork.ordering` and `cardwork.cards`** answer which of two cards stands higher and what one is
  worth. `Preorder[T]` places a value in an order and admits ties; `REGULAR_ORDER` is rank then ♠ ♥ ♦ ♣,
  and `REGULAR_POINTS` scores a pip at its face and a jack through an ace at ten.
- **`cardwork.combinations`** reads a run of cards: whether four cards hold three of a suit, whether seven
  hold a full house, which of two hands wins. Jokers stand in, duplicates count or collapse per game, and
  every query is answered from counters and bit masks. `docs/combinations.md`.
- **`cardwork.rounds`** plays a match as a series of rounds, each dealt afresh from what the last left
  where it lay, led by a seat in turn and scored into a standing. A game of rounds subclasses `RoundGame`
  and states five hooks about one round; the layer states the match around it. `docs/rounds.md`.
- **`cardwork.presentation`** states how a game is laid out for one player: which zones show and where, how
  their cards lie, which move a click sends, what each plaque reads. A `Layout` is data a game states and an
  interface draws, so the geometry stays with the interface. `docs/presentation.md`.

## Games to read

| game | plays | reads for |
|---|---|---|
| `cardgames.backend.passing` | a sequential turn: one exchange with the pile, then a pass round the table | a game whose rules ask a question about cards |
| `cardgames.backend.showdown` | a simultaneous turn: every seat commits one sealed card, and they turn over together | a game whose turn belongs to the whole table |

`tests/games/demo.py` is a smaller exercise game: a simultaneous round with sealed commitments, a reveal,
scoring and take-backs.

## Serving it

```python
from cardserver import TableRegistry, TokenSeats, create_app
from cardwork.decks.standard import standard_deck

registry: TableRegistry[Trump] = TableRegistry(grace_seconds=2.0)
session = registry.open("green-baize", MyGame(players=3, deck=standard_deck()), MYGAME_SCENE)

app = create_app(registry, TokenSeats({"green-baize": {"tok-0": 0, "tok-1": 1, "tok-2": 2}}))
```

A table opens with the game and the arrangement it is read through, since a client asks for both. Run it
with `uvicorn`, and the table answers five endpoints:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/tables/{id}/moves` | Submit `{move, base_seq, idempotency_key}`; answers `{seq}` |
| `GET` | `/tables/{id}/layout` | How this observer lays the table out: its own zones and gestures, and the shared table |
| `GET` | `/tables/{id}/view` | This observer's projection of the table and the moves it may make, stamped with `seq` |
| `GET` | `/tables/{id}/events` | SSE stream of projected commits, resumable via `Last-Event-ID` |
| `GET` | `/tables/{id}/journal` | The full record, once `session.reveal()` has opened it |

A client identifies itself with the `X-Seat-Token` header; a request without one watches as a spectator.
Each response carries what that observer is entitled to know, and nothing further.

Two decisions the host makes:

- **`grace_seconds`** is how long a closed round stays open for a seat to retract its commitment. Each
  command restarts the wait, and the rules decide whether a retraction is still in time.
- **`session.reveal()`** opens a table's full record for analysis. Until then `/journal` answers `403`,
  since the record names every card a seat still holds.

## Playing it

`cardtable` does the wiring above for the games in this repository, which is all it takes to sit down at
one:

```bash
uv run cardtable --game showdown --players 4      # or: make play GAME=showdown PLAYERS=4
```

It prints the address and one token per seat. Each player opens the address in a tab of their own and
offers their token; a tab offering none watches the table. The page comes out of the same application the
endpoints do, so nothing is cross-origin and the token stays in a header.

A table lives as long as the process: the position is held in memory, and a restart deals a fresh one.

Card artwork is fetched rather than kept here:

```bash
make assets      # into a gitignored assets/
```

Two packs land side by side — Susan Kare's Solitaire faces as one 13×4 sprite sheet at 71×96 a card, and a
public-domain drawing per card that covers the jokers the sheet has no face for. Neither is needed: `Suit`
values are `♠♥♦♣` and `Rank` values are `2` through `A`, so a readable card draws from the JSON alone.
