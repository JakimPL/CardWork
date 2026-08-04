# CardWork

A framework for server-authoritative, transactional playing-card games with partial knowledge.

Four packages:

- **`cardwork`** — the engine. Synchronous and pure: a position is a value, a move produces another
  value, and every commit is recorded as data that replays exactly.
- **`cardserver`** — a FastAPI adapter that puts tables into service over HTTP and server-sent events.
- **`cardgames`** — the games written on it, each stated twice over: `backend` holds a game's rules and
  `frontend` the layout a player reads them through. `passing` is a game of four cards played in turn;
  `showdown`, a game of ten turns played at once; `shedding`, a game of matched sets laid down several cards
  at a time.
- **`cardtable`** — the host: it opens a table of a chosen game, hands out a token per seat, and serves
  the player interface beside the endpoints. The one place a game and a transport meet.

`docs/architecture.md` is the design and the reasoning behind it; `docs/combinations.md`, `docs/rounds.md`,
`docs/presentation.md` and `docs/games/` state the parts a game reaches for and the three games themselves.
What follows is enough to start.

## Getting set up

```bash
make install      # uv sync --all-extras, and the page's own dependencies
make check        # lint, mypy --strict, import contracts, coverage, the page's tests
make test         # pytest -n auto, and the page's tests
make interface    # install, test and build the player interface
make play         # open the table config.yaml states; GAME=showdown PLAYERS=4 to depart from it
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
| `cardgames.backend.shedding` | a turn of two minds: shed a set of one rank, or draw a card and pass it on | a game whose move names several cards, and one that asked the layers below it for nothing |

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
uv run cardtable                                  # the run config.yaml states
uv run cardtable --game showdown --players 4      # or: make play GAME=showdown PLAYERS=4
```

`config.yaml` states the run: the game played, the table's name and seating, the seed and grace window it
deals and settles with, the cards it is drawn with, and the address it answers at. Every option of the
command line stands empty until it is given, so it states where one run departs from that file:

```yaml
game: passing

table:
  name: green-baize
  players: 3
  rounds: 3
  seed: 20260803
  grace_seconds: 2.0

artwork:
  pack: kare
  back: crosshatch

service:
  host: 127.0.0.1
  port: 8000
  log_level: info
```

It prints one address per seat, and one that watches the table:

```
Table 'green-baize' is open at http://127.0.0.1:8000
  seat 0: http://127.0.0.1:8000/#table=green-baize&token=Ux9-tKPqf1A
  seat 1: http://127.0.0.1:8000/#table=green-baize&token=x2mE7Rl0aQs
  seat 2: http://127.0.0.1:8000/#table=green-baize&token=Kd4pT1nWqZ8
  watching: http://127.0.0.1:8000/#table=green-baize
```

Each player opens the line they were handed in a tab of their own, and that is the whole of joining: the
table and the token stand in the fragment, which a browser sends to nobody, and the page offers the token in
a header from then on. The page comes out of the same application the endpoints do, so nothing is
cross-origin and no address holds a credential.

A table lives as long as the process: the position is held in memory, and a restart deals a fresh one.

## The interface

`frontend/` is the page a table is played through — React and TypeScript, built by Vite into
`frontend/dist`, which the host mounts at the root of the same application:

```bash
make interface                    # install, test and build it
make types                        # regenerate its API types from the endpoints
npm --prefix frontend run dev     # a development server, proxying /tables to the table config.yaml opens
```

A game states how it is read and the page draws whatever it is handed: the layout names the zones, where
they sit and how their cards lie, the plaques and the words for each phase, so the page holds the name of
neither game. What it is served is what its seat may know — a card it may not read arrives as a placeholder
at that card's own position, and draws as a back.

The table fits one screen at any size and scrolls nowhere: cards are measured from the shorter side of the
window, a hand closes up as it fills so a holding of any size reads by the corners, and a heap reads by the card
on top with the depth of the rest beneath it. A heap opens for a moment on whatever the last commit laid there —
one card per seat where a turn settles them all at once — and then closes over it, so a player reads what
arrived without being asked to watch for it.

A move is made by pointing. The cards some move names light up; clicking one picks it up and the highlight
narrows to the cards a longer move could still name; the places the cards in hand can be sent to — a zone of
the table, or another player — light up in turn, and clicking one of those is what sends the move. So a click
on a card commits nothing, a card in hand goes back down by clicking it again, and the line under the cards
says in the game's own words what the selection would do. Every bit of it comes from the moves the table
reports as open, which is why the page needs to know nothing about a rank or a count.

The layout vocabulary is generated from the OpenAPI document the endpoints publish, since `/layout` is the
one answer standing apart from a game's own state. A view and an event are generic in the state a game
declares and publish no schema, so `src/api/views.ts` mirrors those two by hand. Commits arrive over
server-sent events read through `fetch`, which is what lets a seat token stay in a header:

```
GET /layout, GET /view   as the page loads
GET /events?since=<seq>  from there onward, resumed by Last-Event-ID
POST /moves              a move armed by a selection, pinned to the sequence it was weighed against
```

The page answers the same standard as the Python: Prettier for the formatting, ESLint reading it with the
types in hand, Stylelint for the sheet, `tsc --noEmit`, and Vitest. `make format`, `make lint`, `make
typecheck` and `make test` each cover both languages, and the pre-commit hooks run the page's formatter and
type check on a commit touching `frontend/`, with its tests at push. Building it is what turns
`uv run cardtable` from a set of endpoints into a table you can look at.

Card artwork is fetched rather than kept here:

```bash
make assets      # into a gitignored assets/
```

Two whole packs land side by side, a file per card and a `manifest.json` stating what each holds. `kare` is
Susan Kare's Solitaire artwork cut out of the `cards.dll` it shipped in: fifty-two faces, twelve of the card
backs Windows dealt face down, and two jokers drawn on the card the faces share out of the suit marks the
deuces carry, since Solitaire wanted no joker and the library holds none. Every picture is written four times
the size it was drawn, a pixel to a square, so it reads at any size as the edges a hand placed in 1990. `svg`
is a public-domain drawing per card and a public-domain back besides.

`artwork:` says which pack a table draws with and which of that pack's backs its face-down cards lie under,
and `--pack` and `--back` state either for one run. A table serves the pack it was fetched at `/artwork`,
stating what it holds at `/artwork/manifest.json`, so the page is told the size a card was written at and the
one back this table deals rather than carrying a list of files. The page reads that once as it opens and draws
every card as the picture named for it, measuring the whole table to the shape the pack was written at: a hand
of Kare pixels lies at the proportions Windows dealt them, drawn a pixel to a square at any size.

Neither pack is needed. `pack: null`, or `--pack none`, draws every card from the glyphs the page carries,
which is also what a checkout that has fetched nothing reads: `Suit` values are `♠♥♦♣` and `Rank` values are
`2` through `A`, so a readable card draws from the JSON alone.
