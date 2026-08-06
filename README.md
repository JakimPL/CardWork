# CardWork

A framework for server-authoritative, transactional playing-card games with partial knowledge.

Four packages:

- **`cardwork`** — the engine. Synchronous and pure: a position is a value, a move produces another
  value, and every commit is recorded as data that replays exactly.
- **`cardserver`** — a FastAPI adapter that gathers tables and puts them into service over HTTP and
  server-sent events.
- **`cardgames`** — the games written on it, each stated twice over: `backend` holds a game's rules and
  `frontend` the layout a player reads them through. `passing` is a game of four cards played in turn;
  `showdown`, a game of ten turns played at once; `shedding`, a game of matched sets laid down several cards
  at a time; `climbing`, a game of combinations answered by stronger ones.
- **`cardtable`** — the host: it gathers a table on a join code, deals whichever game its company settles
  on, and serves the player interface beside the endpoints. The one place a game and a transport meet. All
  four games are playable in a browser, across a room or over a LAN.

`docs/architecture.md` is the design and the reasoning behind it; `docs/combinations.md`, `docs/rounds.md`,
`docs/presentation.md` and `docs/games/` state the parts a game reaches for and the four games themselves.
What follows is enough to start.

## Getting set up

```bash
make install      # uv sync --all-extras, and the page's own dependencies
make check        # lint, mypy --strict, import contracts, coverage, the page's tests
make test         # pytest -n auto, and the page's tests
make interface    # install, test and build the player interface
make build        # draw the player interface the table serves, which play does for itself
make play         # gather the table config.yaml states; GAME=showdown PLAYERS=4 to depart from it
                  # HOST=0.0.0.0 to be reached from another machine on the network
```

## Writing a game

A game subclasses `Game` and fills in the rules hooks. Every hook takes the position it operates on, so
the same rules serve a live table, a replay and a search.

```python
from random import Random
from typing import ClassVar

from cardwork.decks.deck import Deck
from cardwork.effects.effects import Effects
from cardwork.games.game import Game
from cardwork.games.intents import Intents
from cardwork.moves.actions import Play, Take
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
    intents: ClassVar[Intents[Play | Take]] = Intents(Play, Take)   # the intents its rules answer to

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

`intents` is the one line of the surface a game states rather than writes. It names the actions the rules
answer to, and the framework does the rest: a move carrying another is refused before the rules read it, and
`self.intents.read(move)` hands a game its own move back at the type it declared — so a `match` over an
intent is covered by the cases the game named. Left at `None` it states a condition on nothing, and every
intent a client may send reaches the rules.

## Laying a game out

A game states how it is played under `cardgames.backend.<game>` and how it is read under
`cardgames.frontend.<game>`, which is one `Scene` and no function at all:

```python
MYGAME_SCENE: Final[Scene] = Scene(
    title="My game",
    table=(Fixture.heap(DISCARD, "Discard"),),   # the zones of the table, read alike by everybody
    seated=(                                     # the zone families the seats hold, stated once for all
        Setting.hand(HANDS, "Hand", mine="Your hand", tally="Cards"),
    ),
    gestures=(                                   # which move a selection sends, and what is pressed to send it
        Making(
            kind=ActionKind.DISCARD,
            group=HANDS,
            picked=HANDS,
            commit=Commit.ZONE,
            target=DISCARD,
            caption="Discard these cards",
        ),
    ),
    readouts=READOUTS,       # Readout.of(MyState, "suit", "Trump", scope=Scope.TABLE)
    phases=PHASES,           # what each phase is called in words
    interludes=INTERLUDES,   # which of those phases play pauses at
    award=Award.HIGHEST,     # which end of the standing the match is won at
)

layout = MYGAME_SCENE.layout(players=3, observer=1)
```

**A zone is stated once, addressed by the `Family` that stands it at every seat**, and `Scene.layout` binds the
seat: the observer reads its own zones under `held`, every other seat under `seen`, the table's own besides,
and is offered a `Gesture` built from each `Making`. A spectator gets the table and no gesture, which is the
entitlement the projection gives it over the cards. Where a zone sits among its owner's is the index of its
declaration, so a game orders its zones by moving a line. The scene checks itself as the module loads, which is
where a mistake in a layout is met.

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
| `cardgames.backend.climbing` | a combination put down on lead, climbed over by the seats after it or passed | a game whose contest sits in the cursor, a turn given up by word, a standing of penalties won at the low end, and a table dealt from one deck or two (two at four seats or five, where the hands stay ones it reads) |

`tests/games/demo.py` is a smaller exercise game: a simultaneous round with sealed commitments, a reveal,
scoring and take-backs.

## Serving it

```python
from cardserver import TableRegistry, TokenSeats, create_app
from cardwork.decks.standard import standard_deck

registry = TableRegistry(grace_seconds=2.0)
session = registry.open("green-baize", MyGame(players=3, deck=standard_deck()), MYGAME_SCENE)

app = create_app(registry, TokenSeats({"green-baize": {"tok-0": 0, "tok-1": 1, "tok-2": 2}}), None)
```

A table opens with the game and the arrangement it is read through, since a client asks for both. Run it
with `uvicorn`, and the table answers six endpoints:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/tables/{id}/moves` | Submit `{move, base_seq, idempotency_key}`; answers `{seq}` |
| `POST` | `/tables/{id}/arrangements` | Lay out a zone of this seat's own: `{zone, order, base_seq, idempotency_key}`; answers `{seq}` |
| `GET` | `/tables/{id}/layout` | How this observer lays the table out: its own zones and gestures, and the shared table |
| `GET` | `/tables/{id}/view` | This observer's projection of the table and the moves it may make, stamped with `seq` |
| `GET` | `/tables/{id}/events` | SSE stream of projected commits, resumable via `Last-Event-ID` |
| `GET` | `/tables/{id}/journal` | The full record, once `session.reveal()` has opened it |

A client identifies itself with the `X-Seat-Token` header; a request without one watches as a spectator.
Each response carries what that observer is entitled to know, and nothing further.

**A table already seated is one way to open one, and gathering it is the other.** Hand `create_app` a
`Gatherings` in place of that `None` — as the lobby *and* as the seat policy, since a token minted at arrival
is what holds a seat — and the application carries seven more routes: `/offerings`, and the guests, room,
stream, seat, choice and deal of each table gathering. A company then arrives on a join code of six card ranks,
names themselves, takes seats, settles what to play out of what the host offers, and deals it. `cardtable` does
that wiring, below.

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
uv run cardtable --host 0.0.0.0                   # or: make play HOST=0.0.0.0, to be reached across a room
```

A table hands out the page as `make build` last drew it, which is what `make play` draws before opening one.

`config.yaml` states the run: the table gathered, the choice it opens on, the cards it is drawn with, and the
address it answers at. Every option of the command line stands empty until it is given, so it states where one
run departs from that file:

```yaml
table:
  name: green-baize
  grace_seconds: 2.0

choice:
  game: passing
  players: 3
  decks: 1
  conclusion:
    rounds: 3

artwork:
  pack: kare
  back: crosshatch

service:
  host: 127.0.0.1
  port: 8421
  advertise: null
  log_level: info
```

The table's own fields are what the host holds — the name it answers under, the window it settles in, and the
seed and code it draws where the file states neither. Everything under `choice` is where the gathering opens
rather than what it plays, since the company settles that for itself.

It prints the code the table gathers behind, and a line per address it is reached at:

```
Table 'green-baize' is gathering — join code K 7 A Q 3 J
  http://192.168.1.42:8421/#table=green-baize&code=K7AQ3J
  http://127.0.0.1:8421/#table=green-baize&code=K7AQ3J
  dealt from seed 20260806
```

Everyone opens a line in a tab of their own, names themselves, and that is the whole of joining: one dialog,
with the table and the code already filled in from the line they were handed. Somebody who reached the address
bare is offered the tables gathering there and types the code themselves. The table and the code stand in the
fragment, which a browser sends to nobody; arriving mints a token that takes the code's place there, so a
reload rejoins as the same guest and no address the server writes down holds a credential. The page comes out
of the same application the endpoints do, so nothing is cross-origin.

From there the room is the page: every guest sees who else is at it, any of them takes a seat, and any guest
holding a seat settles the game, the seating, the decks where the rules admit more than one, and how long the
match runs. The room hands out a colour apiece as people arrive, and any guest takes another that stands free —
a company runs to eight, which is how many colours tell people apart. Pressing the deal puts
every page at the table at once, each plaque reading the name and the colour its guest arrived under. From
there the colour says who: a player's plaque, their place round the table and the panel they play from all
stand in it, and the seat whose turn it is stands in theirs at full strength.

A run bound to `0.0.0.0` is reached from another machine at the address it announces, so a table of people in
one room needs nothing further; `--advertise` states an address instead, for a run behind a name or a tunnel.

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
they sit and how their cards lie, the plaques and the words for each phase, and an offering names the tables
and deck counts each game admits — so the page holds the name of no game at all, in the room as at the table. What it is served is what its seat may know — a card it may not read arrives as a placeholder
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
