# CardWork Architecture

CardWork runs multiplayer card games in which the server holds the whole truth and each player is told
only what they are entitled to know. Four packages divide the work:

- **`cardwork`** — the engine. Synchronous and pure: a position is a value, a move produces another
  value, and every commit is recorded as data that replays exactly.
- **`cardserver`** — an adapter that gathers tables and puts them into service over HTTP and server-sent
  events.
- **`cardgames`** — the games written on the framework, each stated twice over: `backend` holds its rules
  and `frontend` the layout a player reads them through. This is where every claim this document makes is
  answerable.
- **`cardtable`** — the host, and the one place a game and a transport meet: it gathers a table on a join
  code, deals whichever game its company settles on, and serves the player interface beside the endpoints
  (§10, *The host*).

A game is a subclass of `Game` that fills in rules hooks: the zone layout, the deal, what a move means,
and how the turn advances. Everything else — journalling, projection, concurrency, reconnection, replay —
is supplied.

This document is organised as principles first, then the mechanisms each principle produces. §1 is the
part to internalise: when a design question arises that the rest of the document leaves open, the six
rules answer it.

Seven documents state the parts a game reaches for and the games themselves, and this one states what they
all rest on:

| document | states |
|---|---|
| `docs/combinations.md` | what a run of cards reads as: patterns, jokers, duplicates, rankings, points |
| `docs/rounds.md` | a match played as a series of rounds, each dealt afresh and scored into a standing |
| `docs/presentation.md` | how a game states its own table for a player: settings, spreads, gestures, plaques |
| `docs/games/passing.md` | a game of four cards, in which a fourth circulates and three reading alike win |
| `docs/games/showdown.md` | a game of ten sealed turns, every seat committing one card at once |
| `docs/games/shedding.md` | a game of matched sets, a turn shedding several cards of one rank or drawing one |
| `docs/games/climbing.md` | a game of combinations, each answered by a stronger one of as many cards or passed |

---

## 1. Principles

### P1 — The core is a pure function

```
apply(position, move) -> position
```

A game position is a value; applying a move produces another value. The core reads no clock, opens no
socket, consumes no randomness at apply time, and defines nothing `async`. This is the property that
makes everything else cheap: undo, replay, AI search, testing, and reasoning about concurrency all
collapse into "call a function and keep the old value around".

### P2 — Randomness is resolved once and recorded as data

The RNG is consulted exactly once per random decision, at the moment a move is *expanded* into effects,
and the **outcome** is written into the transaction. A shuffle is stored as the resulting permutation.

This is what makes retroactive analysis exact. Replaying a five-year-old game depends on the data in the
journal alone, not on `random.shuffle` having the same implementation it had then.

### P3 — The board is mechanism; rules are policy

`Board` knows about zones and cards: how to take three cards from here and put them there. Whose turn it
is, whether a move is legal, and how points are scored live in the per-game rules.

The consequence is that a new game adds *rules*, and the board it plays on is the one every other game
plays on. Any operation that cannot be written without knowing which game is being played belongs to the
game.

### P4 — Projection is the only thing that crosses the wire

Clients receive a `PositionView` or an `EventView`, each computed from a position **and an observer**.
Both come from one module, `views.project`, which is the place to look when asking "can a player learn
something from the network traffic that the rules withhold?"

The complete `Position` — every card in the game — stays server-side, including for a client that is
obviously entitled to most of it.

### P5 — The journal is append-only above the publication mark

Once a transaction has been **published** — emitted to any observer — it is immutable forever and the
journal only grows. Below that mark the journal is a working document: `undo` truncates it, because
nothing outside the process has read it.

This is what makes replication trivial. A client that has seen up to sequence number *n* needs *n+1*
onwards and nothing else, so the reconnect protocol stays a slice of a tuple.

The mark is a number rather than a convention. The engine tracks it, the adapter advances it as it
commits (§10, *Publication*), and `undo` requires the head to stand above it. On a served table the mark
equals the head, so undo is available to in-process drivers alone — enforced by the engine rather than by
remembering to leave an endpoint unwired. A player who wants their move back is served by §4.4 instead:
a further command that retracts it, which leaves the mark alone because it adds a transaction.

### P6 — The engine owns one cursor; rules own nothing

`Game` holds exactly one piece of mutable *game* state: a history of positions whose last element is
*now*. `state`, `board` and `players` are read-only views of it. Rules — `authorize`, `validate`,
`expand`, `advance`, `legal_moves` — receive the position they operate on and read the engine's cursor
never, even though it is in scope.

Both halves earn their place. A cursor held as one value makes a half-applied transaction unrepresentable
rather than merely unlikely. Rules that read their argument work identically on the table's current
position and on a node ten plies into a search (§8), which is what keeps a search evaluating the rules
the server enforces.

---

## 2. The package contract

`cardwork` is a stack of layers, each importing downward only. Sixteen of them, which read in six bands,
each band a run of the order rather than a grouping laid over it:

| Band | Layers |
|---|---|
| how a game is shown | `presentation` |
| how a table and a match run | `rounds`, `games` |
| what happened, and who is told of it | `views`, `transactions` |
| the table, and what changes it | `effects`, `positions`, `boards`, `states`, `moves`, `zones` |
| cards, and what a run of them reads as | `decks`, `combinations`, `cards`, `ordering` |
| what every model stands on | `models` |

The bands are a way to read the stack; the order is the contract. High to low:

| Layer | Holds | Answers |
|---|---|---|
| `presentation` | `Scene`, `Setting`, `Making` as a game states them; `Layout`, `Slot`, `Gesture`, `Plaque`, `Readout` as an observer is served them | how a game is laid out for a player |
| `rounds` | `RoundGame`, `RoundState`, `Redeal`, seating | how a match of rounds runs |
| `games` | `Game`: setup hooks, rules hooks, and the concrete engine; `Capacity`, `Intents` | how a table plays |
| `views` | `PositionView`, `EventView`, per-observer projection | what an observer is told |
| `transactions` | `Transaction`, `Journal`, `replay` | what happened |
| `effects` | the four primitives and `fold` | what changes a position |
| `positions` | `Position` = board, state, seat count, and the readings addressed by seat | what is true now |
| `boards` | `Board`, a container of zones, and the readings addressed by zone | where cards sit, and what lies there |
| `states` | `GameState` and a game's own subclass, `Award` | phase, turn, score |
| `moves` | `Action`, `Move` | what a client asks for |
| `zones` | `Zone`, `Family`, `Visibility`, `Audience`, resolution | who sees what, and which zone is whose |
| `decks` | `Deck`, index aliases, `named`, permutation draws | which cards exist |
| `combinations` | `Pattern`, `Evaluation`, `Combination`, the search, `Ranking` | what a run of cards reads as |
| `cards` | `Card`, `Joker`, `GameCard`, the card orders and point tables | one card, and what it is worth |
| `ordering` | `Preorder`, `Tiers`, `Composite` | which of two values stands higher |
| `models` | `BaseFrozen`, `held` | how every model behaves |

Two placements are worth explaining. `views` sits **above** `transactions` because projection applies to
transactions as well as positions (§7) — an `EventView` is a projected `Transaction` — and `transactions`
works without knowing that views exist. `moves` is a leaf of pure data: actions are client intents that
the rules translate into effects, and effects are what reach the board (P3), so nothing below `moves`
points into it.

**A question about a table is answered at the height its answer is knowable.** A question about one zone needs
no seat count, so `Board` answers it: the cards lying there as the rules read them, how many, whether any, the
top of an ordered run, and the cards a set of places names. A question about the seats needs the seat count,
which `Position` carries and nothing below it does, so `Position` answers those: the seats, what each holds of
a zone family, which of them hold anything, which hold fewest. A `Family` answers neither — `zones` stands
below both and may name neither — and states instead the one name every seat's zone is reached by, so
`HANDS.of(seat)` is where a zone id comes from and `zone.owner` is where a seat is read back. A game asks
`position.board.count(STACK)` and `position.holding(HANDS)`, and reaches into a zone's own cards for neither.

Three of the layers are the ones the first two games asked for, and each sits where what it knows puts it.
`ordering` is at the bottom because an order is a vocabulary about values of any kind: `Preorder[T]` names
which of two stands higher and admits ties, and `cards` uses it to order a rank and a suit. `combinations`
reads cards and jokers, so it stands above `cards` and below `decks`, and a game consults it as a question
about cards alone. `rounds` stands **above** `games` because it is `Game` plus the bookkeeping of a match —
the deal of a fresh round, the standing, the leader — while the cursor, the journal and the rules of play
stay where they already were (`docs/rounds.md` §1).

`presentation` sits at the head, and every layer beneath it plays a game whether or not anybody is watching. It
is a vocabulary for stating how a game is laid out on a screen: `zones` names a zone to lay out, `moves` a kind
of move to make, `states` a field of the cursor to show, and those three are the whole of what it reaches for. A
layout is data a game states and an interface reads, so the geometry stays with the interface and the game names
no measurement. A game states one `Scene` and the layer lays out every observer from it, which is what keeps the
entitlement of a spectator out of each game's hands (`docs/presentation.md`).

**A game states that scene as data, and the seat is the layer's to bind.** A zone is laid out once, addressed
by the `Family` the layers below already reach every seat's copy of it through: a `Setting` carries the lay its
owner reads, the lay the rest of the table reads and the word its count goes under, and a `Making` names a move
the same way, so one statement becomes a `Gesture` at each seat. Where a zone stands among its owner's is the
index of its declaration, which leaves a page ordinal out of a game's hands altogether. A scene answers for
itself as the module stating it loads, so a mistake in a layout is met where it was written rather than when a
client asks for one.

**`cardgames` is a distribution of its own, and the import goes one way.** A game imports the framework,
which is what keeps every mechanism here general enough for the game after the ones written. Each game stands
apart from every other besides, so a rule two of them want is a rule that has moved down into `cardwork`.

**A game is stated before it is shown.** `cardgames.backend.<game>` holds the rules — the zones, the cursor,
the moves, the scoring — and `cardgames.frontend.<game>` holds the `Layout` those rules are read through.
The layout names the backend for its zone ids and its phases, so no string is written twice; the rules name
the layout nowhere, which is what keeps a game playable with no screen attached and keeps a change of
presentation from reaching the journal. Every one of these four modules stands on the framework and on its
own game alone.

**The interface stands outside the import graph altogether.** `frontend/` is a page written in another
language, so no contract can hold it to the packages above and two artefacts do it instead: the OpenAPI
document the endpoints publish, which the layout vocabulary is generated from, and about ninety lines
mirroring the projections by hand, since those carry a game's own state and publish no schema (§10, *The
page*). Everything a game states about how it is read reaches the page as data, so the page holds the name of
no game at all.

**`cardtable` names all three, and nothing names it.** A game class and FastAPI have to meet somewhere, and
the two contracts above put that somewhere outside `cardgames` and outside `cardserver` alike: the host is
the fourth package, it holds one module per concern of putting a table into service, and the arrows all
point into it (§10, *The host*).

`cardwork.exceptions` sits outside the stack deliberately. The refusals of §6 are raised at four
different heights — journal truncation, the engine's concurrency check, a game's `authorize`, a game's
`validate` — and a shared vocabulary of refusals is the one thing every height may name.

### The contract is checked

import-linter holds twelve contracts over the four packages, so the boundaries are mechanical rather than
aspirational:

1. **Layered architecture** — the core order above.
2. **Rules are transport-free** — `cardwork` and `cardgames` name none of `cardserver`, `fastapi`,
   `starlette`, `httpx`, `asyncio`, `requests`. `asyncio` is on that list on purpose: the core is
   synchronous by P1, and the moment a domain function becomes `async`, callers need an event loop and the
   pure-function property holds on paper alone. `cardserver` is on it because the port belongs to the
   consumer (§10, *The port*), so the arrow between the packages points one way.
3. **The framework knows no game** — neither `cardwork` nor `cardserver` names `cardgames`, which is what
   keeps a mechanism general and an adapter game-agnostic.
4. **Adapter layers** — `cardserver` layers in its own right, high to low: `app`, `lobby`, `streams`,
   `registry`, `gathering`, `sessions`, `identity`, `errors`, `schemas`, `naming`, then `protocol` beside
   `codes` at the foot. `gathering` stands above `sessions` and below `registry` because a gathering ends by
   putting a table into service and reaches the registry through a port of its own (§10, *The gathering*).
5. **Rules know no presentation** — within `cardgames`, `frontend` stands above `backend`, so a game's rules
   are playable with no layout in sight and a layout is free to name the rules it lays out.
6. **Rules read cards rather than tables** — a game's `rules` module names none of `presentation`, `rounds`,
   `games`, `views`, `transactions`, `effects`, `positions`, `boards`, `moves` or `zones`. What it may name is
   the bottom of the stack, the cursor's own vocabulary in `states`, and the index aliases in `decks`: cards,
   counts and places inside a run of them. So a rules module states a rule and a `game` module states where
   the cards for it sit, and the boundary between the two halves of a game is checkable rather than habitual
   (§9, *Writing a game*).
7. **Passing stands apart** — a game names no other game at either height, so whatever two games share lives
   in `cardwork` where the third will find it.
8. **Showdown stands apart** — the same claim over showdown's rules and its layout.
9. **Shedding stands apart** — and over shedding's.
10. **Climbing stands apart** — and over climbing's.
11. **Nothing names the host** — none of `cardwork`, `cardserver` or `cardgames` names `cardtable`, so the
   composition root stays a leaf nothing depends on and a second host costs no change below it.
12. **Host layers** — `cardtable` layers in its own right, high to low: `cli`, `catalogue`, `hosting`,
   `config` beside `reaching`, then `settings`, `service`, `interface` and `artwork` standing independent of
   one another, and `games` beside `paths` at the foot.

**Four of those contracts state one claim, because a game is stated across two packages.**
`cardgames.*.passing` is the expression meaning everything that belongs to passing, and an `independence`
contract may not be given it: it expands a wildcard into one flat set of siblings and holds all of them
against each other, so it would refuse `frontend.passing` importing `backend.passing` — the one cross-height
import the design asks for. Handed the two heights separately instead, it holds each of them and lets a
layout reach into another game's rules unremarked, which is the likeliest of these mistakes to make, since a
layout is written by reading the last one. So the contracts are pairwise, one per game, and a fifth game
brings a fifth. One would cover them all where a game were a package of its own with its two heights inside
it, which is the structural change the growing count points at.

---

## 3. The table: cards, zones, and sight

### 3.1 Cards are values

```python
class GameCard(BaseFrozen):
    card: CardOrJoker
    face_down: bool = False

    def with_face(self, face_down: bool) -> GameCard: ...
```

Cards are frozen, so a card referenced from a snapshot keeps whatever it was when the snapshot was taken.
Flipping one produces a new `GameCard` through `with_face`, which is the single path both card-facing
effects go through.

`face_down` is the **physical** fact — which way the card is oriented — and it reads the same for every
observer. *Whom* that fact conceals the card from is a property of the zone, resolved per observer
(§3.3). Sight is therefore a derived predicate rather than a stored flag, and one code path answers it
for the holder, for an opponent and for a spectator alike.

### 3.2 One zone concept

```python
ZoneId = str
Zones = Mapping[ZoneId, Zone]


class Zone(BaseFrozen):
    id: ZoneId
    owner: int | None = None
    visibility: Visibility
    ordered: bool
    cards: GameCards = ()

    def with_cards(self, cards: GameCards) -> Zone: ...


class Board(BaseFrozen):
    starting_deck: Deck
    zones: Zones

    def zone(self, zone_id: ZoneId) -> Zone: ...
    def with_zones(self, *replacements: Zone) -> Board: ...
    def validate_board(self) -> None: ...
```

A hand, the draw pile, the discard stack, a played meld and a row of sealed commitments are the same
thing: a named, owned run of cards under a visibility policy, holding its arrangement either for the table
or for the seat. That single concept is what lets a seat hold private, per-seat, multi-zone storage — a
commitment tray beside a hand — which is the minimum a sealed simultaneous round needs.

`Board.zone` earns its place by what it raises. Effects address zones by name, so a game that emits a
move out of `hand:3` at a three-seat table has a typo; `zone()` names the ids the board does hold and
turns that into a legible failure at the point of the mistake.

One validator runs on every board: **the key a zone is filed under equals its own `id`.** Read paths take
the key and write paths take `zone.id`, so agreement between the two is what keeps a zone from being
served under another's name. `with_zones` files by `zone.id` and **constructs** a new board, so the
validator runs on every board an effect produces.

> **A frozen model freezes assignment, not containers.** Pydantic's `frozen=True` blocks attribute
> assignment and leaves a `list` or `dict` field open to in-place edits. So `Zone.cards` is genuinely a
> `tuple` — cards are what move between snapshots, and that is where aliasing bites. `Board.zones` stays
> a mapping for ergonomics, and `with_zones` is the one method that produces a changed one: a single
> place to audit rather than every future board operation.

### 3.3 Visibility is zone policy, resolved per observer

```python
class Audience(StrEnum):
    ALL = "all"
    OWNER = "owner"
    NONE = "none"


class Visibility(BaseFrozen):
    face_up: Audience = Audience.ALL
    face_down: Audience = Audience.NONE
    extra: frozenset[int] = frozenset()
```

`extra` covers ad-hoc reveals — a card deliberately shown to one opponent — with no separate mechanism.

Resolution is two small functions. `audience(zone, card, players) -> frozenset[int]` reads the policy that
the card's face selects and answers for the table, naming the seats entitled to identify the card.
`visible_to(zone, card, players, observer) -> bool` answers for one observer, and it is what projection
calls.

**A spectator holds no seat, so they read what the table reads: the cards a zone shows to everyone.** That
is the one place the two functions part company, and the reason they are separate. `audience` returns seat
numbers, and a spectator has no number to look for; treating them as an absent seat would be right by
accident and wrong for `extra`, which names seats and so belongs to the players it was written for.

Three presets cover the zones a game needs:

```python
HAND = Visibility(face_up=Audience.ALL, face_down=Audience.OWNER)
PILE = Visibility(face_up=Audience.ALL, face_down=Audience.NONE)
HIDDEN = Visibility(face_up=Audience.NONE, face_down=Audience.NONE)
```

| Zone | Preset | Owner | Cards | Result |
|---|---|---|---|---|
| A player's hand | `HAND` | `p` | face-down | only the owner identifies them |
| An exposed penalty card in a hand | `HAND` | `p` | face-up | everyone reads it |
| A tray of sealed commitments | `HAND` | `p` | face-down | the owner reads its own; everyone else reads the count |
| Cards you hold but have not looked at | `PILE` | `p` | face-down | the count is public, the identity is nobody's |
| Draw pile | `PILE` | — | face-down | the count is public |
| Discard pile, top card up | `PILE` | — | mixed | the face-up card is public |
| A played meld | `PILE` | — | face-up | public |
| A stack set aside out of play | `HIDDEN` | — | either | the count is public whichever way they lie |

`HAND` and `PILE` do the work; `HIDDEN` states the one case the other two leave out — a zone whose
contents stay concealed even face up, which is what a card removed from the game is. That the list is this
short, with the card's face doing the remaining work, is the argument that the model is the right size.
More policies are available the day they are wanted: `extra` plus a `Visibility` of a game's own.

#### Ownership and visibility are orthogonal

A card in your possession that you have yet to look at is `PILE` visibility on an *owned* zone —
`Zone(id="blind:1", owner=1, visibility=PILE)`. `owner=1` says whose cards these are for rules, scoring
and conservation; `PILE` says the owner reads them as everyone else does.

The consequence is that **learning a card is an explicit, journaled transition**: a move from `blind:1`
into `hand:1`, cards staying face-down, only the zone changing and with it the audience. Opponents read a
placeholder on both sides — a card moved between two of player 1's zones.

This is worth doing deliberately. In a server-authoritative game the moment a player *learns* a card is
the moment the server sends them its identity, so that moment exists in the model as a transaction with a
`seq`: it replays, it undoes, and "what did player 1 know at move 17?" (§8) answers correctly across it.

One cost, stated plainly: known and unknown cards of one holder live in two zones, so a single ordering
spans them only if a game gives the zone a per-index policy instead.

### 3.4 Arrangement is zone policy too, resolved per seat

`ordered` is the zone's word on whether the run its cards lie in is part of what it holds.

| Zone | `ordered` | Why |
|---|---|---|
| Draw pile, stock | `True` | the card that comes off next is named by position |
| Discard, a stack given up onto | `True` | the top card is what the rules read, and the run below it is the record of the round |
| A tray of sealed commitments | `True` | the run is the order the commitments were made in |
| A blind holding its owner cannot read | `True` | the run is the order the deal laid it in, and the turns read a card out of it by position |
| A player's hand | `False` | the rules read the cards a seat has, and the seat keeps them in whatever order it likes |

The word binds the players alone: the rules reorder whatever they need to, and a shuffle of the stock is a
`Reorder` over a zone marked `True`. What `ordered` settles is which zones a **seat** may lay out for its own
sake, and that permission is derived rather than declared — `arrangeable_by(zone, observer)` is
`not zone.ordered and zone.owner == observer`, which sits in `zones/resolution.py` beside `visible_to` and is
answered the same way: per observer, off the policy, never stored.

**One fact stated, two consequences.** A flag reading "the player may drag here" would let a game declare
something incoherent — a draggable stock — with nothing in the framework able to tell it was wrong. Stating what
the *rules* read instead makes the permission a theorem: if no rule reads the run, then permuting it is
unobservable to the rules and to every other seat, so the seat holding the zone may do as it pleases with it.

That the projection carries the answer rather than the question follows from P4. `ZoneView.arrangeable` is this
observer's own standing, resolved server-side out of the owner and the arrangement, so a client learns exactly
one thing about a zone's policy — the cards it may read, and the run it may lay them out in.

### 3.5 Conservation

`Board.validate_board` folds over every zone and compares the result against `starting_deck`, so a zone
layout that loses or duplicates a card fails at construction rather than at the point where the
arithmetic stops adding up. It runs on every dealt table.

Conservation is all it checks. "The discard pile lies face-down" is a rule of one game rather than of
cards in general (P3), and a game that wants it states it in `_final_validation`.

---

## 4. The turn

### 4.1 The turn is a set

```python
class GameState(BaseFrozen):
    phase: str
    to_act: frozenset[int] = frozenset()
    points: tuple[int, ...] | None = None

    @property
    def current(self) -> int | None: ...

    def with_changes(self, **changes: object) -> Self: ...
    def project(self, observer: int | None) -> Self: ...
```

- **Sequential play**: `to_act == {p}`. When *p* moves, the rules set `to_act = {(p + 1) % players}`.
- **Simultaneous play**: `to_act == {0, 1, 2, 3}`, shrinking as each move arrives. The phase resolves
  when it empties.

That is the whole turn model. A move is authorized when `move.player in state.to_act`, and one check
serves both modes — as the default body of a rules hook a game may widen (§4.4).

### 4.2 A game's own state

Three shared fields hold a phase, a turn and a score. A bid, a trump suit, who led the trick, or a buffer
of gathered commitments belong to the game, so a game declares its own `GameState` subclass with its own
typed fields and parameterises the engine with it: `Position`, `Effect`, `SetState`, `Transaction`,
`Journal`, `PositionView`, `EventView` and `Game` are generic in `StateT`. A game gets full type checking
on its own fields, exact serialization of them, and deserialization back into its own type.

The cost is that the type parameter threads through the whole stack, and a server is built for one rule
set at a time (§10, *The port*). What it buys is that the framework picks nothing about how a game holds
its own state. "How do simultaneous actions get gathered?" becomes a game's own choice: the framework
applies each commit immediately into private zones (§4.3), and a game that wants held, un-applied
commitments declares them in *its* state, narrows them in `project`, and answers for both.

Two methods make that subclass safe to extend:

**`with_changes`** is how a game derives the next cursor. It revalidates through the game's own model, so
a change that leaves the declared types — or names a field the state does not declare — raises where it
was written. This matters because the alternative, `model_copy(update=...)`, validates nothing and would
let a wrong type into the journal to be replayed faithfully forever.

**`project`** is the state's half of the security boundary (§7). The three shared fields are table
knowledge — the phase, the seats that owe an action and the running score are as public as the cards face
up on the table — so the default returns the state whole. A game whose own state holds something a seat
keeps to itself overrides this to blank those fields for other observers, and the cursor crossing the wire
then obeys the same entitlement the cards do. This hook is what keeps generic state inside §7 rather than
beside it.

### 4.3 Sealing falls out of visibility

The obvious worry about simultaneous play is *sealing*: player 1 commits a card that players 0 and 2 read
only at the reveal. This appears to want a separate sealed-move store, encryption, or a two-phase commit.

The visibility model already answers it:

- The commitment moves cards into `tray:1` — a zone owned by player 1, `HAND` visibility, cards
  face-down.
- The transaction is journaled immediately; the server holds the whole truth anyway.
- Players 0 and 2 receive a *projection* of that transaction, which says "`hand:1` lost a card and
  `tray:1` gained a placeholder" and carries no identity, because §7 computes exactly that from `HAND`.
- Once `to_act` empties, settlement lays every tray face up, and the next projection shows everyone
  everything.

**Simultaneity and sealing follow from `to_act: frozenset[int]` plus the visibility rules, with no
additional concepts.** That is the sign the two mechanisms are cut along the right joint.

### 4.4 Take-backs are forward moves

A player retracts a commitment while the round that received it is still open — the misclick, the second
thought, the tap that landed a keystroke too early.

**A take-back is a move, not an undo.** It is an ordinary command that carries the committed cards back
out of the tray and reopens the turn: a `MoveCards` from `tray:1` to `hand:1`, and a `SetState` putting
seat 1 back into `to_act`. The journal only grows, P5 stands, and no observer is asked to forget anything,
because opponents read a count where the card sat and they still do.

Three pieces make it work, each in the layer that owns the question:

**Authority is a rules hook.** The turn check refuses a retraction outright, since the retractor has
already acted. So it is `authorize(position, move)`, a concrete hook whose default body is exactly that
check (§9). A game that admits retractions overrides `authorize` alone.

**"Too late" is a rules predicate.** The window is the interval between the round closing (`to_act` empty)
and settlement changing the phase; the game's `validate` reads `phase` and decides. Keeping this apart
from `authorize` is what keeps §6's refusals legible: a seat with no standing gets `403`, a seat that
asked too late gets `422`.

**Latency is the adapter's problem.** P1 keeps clocks out of the core, so the adapter waits out a
configurable grace period before asking the rules to settle, and each command restarts the wait (§10,
*The grace window*). The core stays synchronous and timeless; the seconds live in one place.

---

## 5. Positions, effects, transactions

### 5.1 Position

```python
class Position(BaseFrozen, Generic[StateT]):
    board: Board
    state: StateT
    players: int = Field(ge=1)

    def with_board(self, board: Board) -> Position[StateT]: ...
    def with_state(self, state: StateT) -> Position[StateT]: ...
```

The complete server-side truth at one instant: every card, every point, whose turn it is. This is the
value that is passed around and snapshotted, and the value projection reads (§7).

**`players` is a field of the position rather than a parameter passed alongside it.** Projection needs the
seat count to resolve `Audience.ALL`, and a position recovered from `Journal.replay(17)` carries no other
source for it. A self-contained position is what makes historical knowledge answerable from a journal and
nothing else.

`with_board` and `with_state` are how effects derive a position. Each constructs and carries `players`
across, so the board's own validators (§3.2) run on every position an effect produces.

### 5.2 Effects

Four primitives cover everything a simultaneous, partial-knowledge game does to a table:

```python
class MoveCards(Effect[StateT]):
    kind: Literal["move_cards"] = "move_cards"
    source: ZoneId
    indices: NonEmptyIndices  # positions within source
    target: ZoneId
    at: int | None = None  # insertion index; None appends
    face_down: bool | None = None  # None keeps each card's current face


class SetFace(Effect[StateT]):
    kind: Literal["set_face"] = "set_face"
    zone: ZoneId
    indices: NonEmptyIndices
    face_down: bool


class Reorder(Effect[StateT]):
    kind: Literal["reorder"] = "reorder"
    zone: ZoneId
    order: tuple[int, ...]  # an explicit, recorded permutation


class SetState(Effect[StateT]):
    kind: Literal["set_state"] = "set_state"
    state: StateT  # the whole cursor, built through with_changes


type AnyEffect[S: GameState] = Annotated[
    MoveCards[S] | SetFace[S] | Reorder[S] | SetState[S],
    Field(discriminator="kind"),
]
```

Effects are **pure and total**: given a position they return a new position or raise, and they consult no
clock, socket or RNG.

**The `kind` tags are load-bearing.** Pydantic serializes a field by its *declared* type, so a wire-facing
field typed as an abstract base would carry the base's fields alone and offer nothing to deserialize back
into. The journal endpoint, the event payloads and any persisted journal rest on the discriminated union,
and a round-trip property guards it (§13).

Three places where the effects earn their bodies:

- **`MoveCards`** lifts by position and lays down in source order, so an unordered `frozenset` of indices
  produces a determined arrangement. `source == target` is a single-zone rearrangement, handled as one
  write. An `at` past the end raises, because an insertion index that misses is a rules bug worth hearing
  about.
- **`Reorder`** checks that `order` is a genuine permutation of `range(len(cards))` before applying
  anything, which is what keeps a mis-sized shuffle from dropping or duplicating a card.
- **`SetState`** carries the **whole** state. A bag of changes applied through `model_copy(update=...)`
  passes no validation, so a carried, validated state is what keeps the journal self-describing and lets a
  game's own subclass survive serialization intact.

`revalidate_instances="always"` on the effect base makes those checks unskippable: an effect handed to a
transaction is validated again as it enters, so what the journal records has passed the checks a caller's
construction passed.

A transaction applies a *sequence* of effects, so there is exactly one combinator, and it is the whole of
the application step:

```python
def fold(
    effects: Iterable[AnyEffect[StateT]], position: Position[StateT]
) -> Position[StateT]: ...
```

`Journal.replay`, the engine's commit path and speculative search all go through it. It is the single path
from effects to a position.

**`Reorder` is where P2 lives.** There is no `Shuffle` effect. Shuffling happens during expansion, where
the RNG is consulted once — `decks.draw.permutation(size, rng)` draws it — and the result is written down.
Replaying a `Reorder` a decade later reproduces the same order because the order *is* the data.

### 5.3 Actions are intents

`Action` names what a client asks for — play these cards to that group, take from there, discard — and the
rules translate it into effects in `expand`. Actions carry a `kind` tag apiece and union as `AnyAction` on
the same grounds as the effects: a `Move` crosses the wire in both directions. The tags are the members of
`ActionKind`, so a layer speaking about a kind of move rather than about one move — a layout saying which
gesture puts a `Take` on the table (`docs/presentation.md` §1) — holds a member of a closed vocabulary.

Seven intents cover the vocabulary a client sends, and a game reads the ones it is played with:

| intent | carries | asks for |
|---|---|---|
| `Pass()` | its word alone | the turn given up, and every card left where it lies |
| `Play(group, indices)` | a group and positions in the seat's own cards | these cards played to that group |
| `Take(group, indices)` | a group and positions | cards taken from there |
| `Give(target_player, indices)` | a seat and positions | cards handed to that seat |
| `Reject(indices)` | positions | cards declined |
| `Discard(group, indices)` | a group and positions | cards laid off |
| `Declare(claim, indices)` | a word and the positions it is claimed of | those cards read as the claim names |

**`Declare` is the one intent that carries a word.** A bid, a trump named, a contract announced — each names
positions *and* what the seat says of them, and the rules answer by reading the cards themselves. The word is
a `str` on the wire and a `StrEnum` in the game that reads it, which keeps the vocabulary of one game closed
while the action stays general. `indices` may be empty here alone among the intents that name positions, since
a declaration over a whole hand covers everything the seat holds.

No game here sends one, and the reason is worth stating: a declaration earns an intent where the seat's
word decides something. A win the cards already read decides nothing — a seat holding one gains nothing by
withholding it — so `cardgames.backend.passing` awards it instead of asking for it (`docs/games/passing.md` §1).

**`Pass` is the one intent that names no card.** A seat with nothing it may play, or nothing it will, gives the
turn up and the word is the whole of the move. So `group_of` reads None for it and `indices_of` an empty run,
which is what lets a layer reading the cards behind any move at all — an interface lighting up what a served
move would take — read one that is about none of them. A move naming no card is also the one a place on the
table stands for nowhere, so it reaches a player by the third commit a gesture states rather than by a zone to
point at (`docs/presentation.md` §5).

**A game states which of the seven it is played with, and the framework holds every move to that.** `Intents`
is that statement: a game names the actions its rules answer to and the engine reads a move against them at
step 7 of §6, so the refusal of an intent a game leaves out is written once, in the framework's own words —
`Seat 2 makes a take or a give, and offered a play`.

```python
class PassingGame(RoundGame[PassingState]):
    intents: ClassVar[Intents[Take | Give]] = Intents(Take, Give)

    def expand(self, position: Table, move: Move, rng: Random) -> Changes:
        match self.intents.read(
            move
        ):  # a Take or a Give, and the match is covered by those two
            case Take() as exchange:
                ...
            case Give() as passing:
                ...
```

The declaration is generic in the actions it names, so the vocabulary reaches the types a game is written
in: `read` answers with the actions the game stated, and a `match` over that answer is exhausted by their
cases. The vocabulary is one word per action, which is what `moves.kind_of` reads off a class.

**A game states no vocabulary by leaving the declaration at None**, which states a condition on nothing: every
intent reaches its rules, and reaches them still once an eighth is written. So the seven above are named in the
one place they are declared, and a game that reads them all says as much by saying nothing.

Actions address cards **positionally**: "the first, third and sixth cards of my hand". Positional
addressing is the right choice under partial knowledge, because it lets a client reference a card it
cannot identify — an opponent's face-down card at index 3 — which stable card ids manage only by leaking
identity or by maintaining per-observer handle tables. The cost of positional addressing is what §6's
`base_seq` pays.

Expansion is also where visibility policy is decided, and it is a rules question. Passing a card to
another seat's `hand` grants the receiver sight of it the instant it arrives, because `HAND` reveals
face-down cards to their owner; passing it to their `blind` zone leaves it unread until they look (§3.3).
The projection is faithful in both cases, so this is the class of question a rules test answers rather
than the no-leak property of §7.

### 5.4 Transactions and the journal

```python
class Transaction(BaseFrozen, Generic[StateT]):
    seq: int
    move: Move | None  # None for engine-initiated: the deal, settlement
    effects: Effects[StateT]
```

A transaction is the atomic unit; its effects apply in order, all or nothing.

**One command produces exactly one transaction.** The effects from `expand` and the effects from `advance`
are concatenated into it, because a move and the turn change it causes are neither separately undoable nor
separately observable — an observer that read a card moving before the turn advanced would be reading a
position that never existed.

```python
class Journal(BaseFrozen, Generic[StateT]):
    initial: Position[StateT]
    transactions: Transactions[StateT] = ()

    @property
    def head(self) -> int: ...

    def append(self, transaction: Transaction[StateT]) -> Journal[StateT]: ...
    def truncate(self) -> Journal[StateT]: ...
    def replay(self, upto: int | None = None) -> Position[StateT]: ...
```

`Journal` is frozen like everything else, so `append` and `truncate` **return** a journal and the engine
rebinds.

Two guards hold because a sequence number doubles as an index. `append` requires `transaction.seq` to
equal the head, which is what licenses `replay(n)` meaning "the first `n` transactions" and `base_seq`
meaning "the position I built on". `truncate` requires a transaction to be there, so `undo` reports
success on a table that has something to undo — transaction 0 is the deal, and a journal at its origin
describes a table that was never dealt.

`initial` is the **origin**: the components on the table before anyone touches them. Storing it here is
what lets the deal be transaction 0 rather than a privileged pre-history step (§9), and it is why a
journal replays on its own.

`replay(upto)` returns the position after `upto` transactions, so `replay(0)` is `initial` and
`replay(None)` is now. `truncate` drops one unpublished transaction, and by P5 it reaches nothing a client
has read — that bound is what spares the journal compensating transactions, tombstones and branches.

---

## 6. The command pipeline

```
Command(table, move, base_seq, idempotency_key)
   │
   ├─ 1. identity         adapter maps credential -> seat                401 Unauthenticated
   ├─ 2. standing         seat == move.player                            403 WrongSeat
   ├─ 3. lock             one writer per table (§10)                     the only concurrency
   ├─ 4. idempotency      key already applied? -> return its seq         200 (replayed)
   │      ── engine below this line; everything above is the adapter ──
   ├─ 5. concurrency      base_seq == journal.head                       409 StalePosition
   ├─ 6. authority        rules.authorize(position, move)                403 NotYourTurn
   ├─ 7. legality         rules.intents.read(move), then validate(...)   422 IllegalMove
   ├─ 8. expansion        rules.expand(position, move, rng) -> effects   ← RNG resolved and recorded
   ├─ 9. application      position' = fold(effects, position)            pure
   ├─ 10. advancement     follow = rules.advance(position', move, rng)   turn / phase / score, RNG too
   ├─ 11. commit          journal.append(Transaction(head, move, effects + follow))
   │      ── adapter again ──
   ├─ 12. publish         mark published; wake every stream watching
   └─ 13. settle          restart the grace window; when it passes, rules.settle()
```

Steps 5–10 produce values and touch nothing. The first mutation is step 11, and the commit method (§9) is
the only method in the engine that mutates at all.

**Atomicity is therefore free.** There is no rollback code, no `try/finally`, no compensating logic for
"effect 3 of 5 failed". A step that raises leaves the engine holding the original position and the caller
holding an error. Partial application is not something the design prevents; it is something the design
cannot express.

**Step 7 reads the vocabulary before the content.** A game states the intents it is played with (§5.3), and
the engine refuses a move carrying any other before `validate` is asked anything, so a game's own refusals
speak about the moves it plays and the vocabulary is answered for in one place.

**The seat check at step 2 is the adapter's alone.** The engine trusts `move.player`, because a seat number
is all the domain knows about identity (§10, *Identity*). So the adapter confirms that the credential
behind the request holds the seat the move was made for, before anything else looks at the move. Step 6
then asks a different question — does that seat have the turn — which is the game's to answer.

**Idempotency precedes concurrency**, and the order matters: a client retrying a command that in fact
succeeded gets its original `seq` back, whereas checking `base_seq` first would answer `409` for a move
that had already landed and send the client chasing a conflict it caused itself. The key is recorded once
the engine accepts the command, so a refusal leaves the client free to try again.

### Why `base_seq` matters more than it looks

Indices are meaningful against one specific version of the position (§5.3). If another player acts between
a client rendering its hand and submitting a move, index 2 may name a different card.

`base_seq` closes this exactly. The client sends the sequence number its view was computed from; the
server refuses anything stale with `409` and the client refetches. Optimistic concurrency control, about
six lines, and it turns a silent-wrong-card bug into a visible, recoverable protocol error.

### Idempotency

A retried `POST` — flaky network, impatient user, mobile handover — applies a move once. Each command
carries a client-generated `idempotency_key`; the table keeps `key -> seq` and returns the original result
on a repeat. This is why commands travel over HTTP `POST` rather than a bare socket message: the pattern
is standard, testable, and needs no invention.

### Settlement — the transactions no seat asked for

Step 10 runs `advance` once, so a command carries the turn change it caused. A round whose last seat has
just acted owes more than a turn change: the reveal, the scoring, the deal that opens the next hand. None
of that belongs to the seat that happened to act last — an observer reading its event should see one
seat's move.

So the engine has a second entry point, `settle()`, which commits `advance(position, None, rng)` repeatedly
until the rules ask for nothing more. Each round of it lands as its own transaction carrying `move=None`,
which keeps what a seat did legible apart from what the rules did in answer, and a table already at rest
yields an empty run. A `Final` cap bounds the loop, so an `advance` that carries the table in a circle
raises rather than spinning. The generator it hands on is the engine's own, which is what lets a round
boundary shuffle where no seat has acted (§9, and `docs/rounds.md` §3).

**Who calls it, and when, is the adapter's decision** — and the answer is "after the grace window", which
is what makes a take-back possible (§4.4). The engine stays synchronous and knows nothing of the wait.

### Arrangement — the commit a seat asks for outside the turn

A player sorting the hand it holds is the third thing that reaches the journal, and `arrange(zone, order, seat,
base_seq)` is the entry point for it. It runs a pipeline of its own, whose engine half is four steps to
`submit`'s seven:

```
Arrangement(table, zone, order, base_seq, idempotency_key)
   │
   ├─ 1. identity      adapter maps credential -> seat                 401 Unauthenticated
   ├─ 2. standing      a seat, rather than a spectator, is asking      403 WrongSeat
   ├─ 3. lock          the same single writer per table (§10)
   ├─ 4. idempotency   key already applied? -> return its seq          200 (replayed)
   │      ── engine below this line; everything above is the adapter ──
   ├─ 5. concurrency   base_seq == journal.head                        409 StalePosition
   ├─ 6. entitlement   arrangeable_by(zone, seat) (§3.4)               422 ArrangementRefused
   ├─ 7. permutation   the order names each position of the zone once  422 ArrangementRefused
   ├─ 8. commit        journal.append(Transaction(head, None, (Reorder(zone, order),)))
   │      ── adapter again ──
   └─ 9. publish       mark published; wake every stream watching
```

**No `authorize`, no `validate`, no `advance`.** The steps `submit` runs between those are the ones that ask what
the rules make of an intent, and a seat sorting a zone whose run no rule reads states no intent to ask about. So
the table stands as it stood across the commit: the same cards at the same faces under the same cursor, and every
other seat reads the zone exactly as before — a run of placeholders reads the same however it is permuted, so
`zone_changes` (§7) carries nothing at all for them. That is what admits an arrangement at any moment of a round
whoever holds the turn, and what leaves the grace window out of the last step: sorting a hand starts no window,
since nothing was committed for a seat to take back, and the changes a closed round owes fall due at the moment
the last move left them due.

**Step 2 asks less than `submit`'s does, and the seat is the answer to it.** A move states the seat it is made for
and the adapter confirms the credential holds it; an arrangement states no seat at all, so the credential is not
checked against a claim but read as one. That is the whole of why the body carries no seat: a request naming one
would be a request to be refused, and the shape a client cannot get wrong is the shape that leaves it out.

**It is a commit rather than a client-side display order** for two reasons, both about the one thing indices
mean here. Positions name cards against one version of the position (§5.3, and *Why `base_seq` matters* above),
so a client keeping an order of its own would hold a second coordinate system that every index crossing the wire
would have to be read through; and an order kept locally has no stable key — an index dies when a card leaves the
zone, and a card's identity is no key at all where a deck is doubled or where a seat owns a zone it cannot read.
Held on the server there is one coordinate system, nothing to rebase, and the order survives a reload. Step 5
earns its place here as much as in `submit`: sorting a hand moves the card each position names, so a move
already in flight against the old run is turned away rather than landing on the wrong card.

**It is not a move**, either, and that is a separate claim. A move is something the rules offer and answer for; a
reorder among `legal_moves` would name every card of a hand and so read, to an interface drawing what is in play
off the moves it was served (§10), as though every card in the hand were playable. A card a seat may sort is not
thereby a card it may play.

---

## 7. Knowledge and projection

This is the section to reread when in doubt. Everything a client learns, it learns here.

```python
class ZoneView(BaseFrozen):
    id: ZoneId
    owner: int | None
    arrangeable: bool  # whether this observer may lay the run out itself (§3.4)
    cards: tuple[
        GameCard | None, ...
    ]  # None = present, unidentifiable by this observer


class PositionView(BaseFrozen, Generic[StateT]):
    observer: int | None
    seq: int
    zones: Mapping[ZoneId, ZoneView]
    state: StateT
    legal: Moves  # the moves this observer may make, and those alone


def project_position(
    position: Position[StateT], seq: int, observer: int | None, legal: Moves
) -> PositionView[StateT]: ...
```

A card is carried through when `visible_to(zone, card, position.players, observer)` and stands as `None`
otherwise. An `observer` of `None` is a spectator, and reads the cards a zone shows to everyone (§3.3).

`seq` comes from the caller because a position is a snapshot of a table rather than a point in its
history: the same snapshot is projected at whatever sequence the journal had reached when it was taken,
and the engine is the only thing that knows which. The stamp is what a client quotes back as `base_seq`,
which is how §6's concurrency check ties a move to the view it was aimed at.

`state` passes through `GameState.project` (§4.2), so a game's own state is narrowed by the game's own
rule. Everything else in the view is narrowed by `visible_to`.

### Position-preserving, never compacted

`cards` keeps `None` placeholders at the exact indices the concealed cards occupy. Filtering them out
would make the payload smaller and every positional action wrong: client indices must agree with server
indices, and compaction fails quietly — the move succeeds, it just addresses a different card.

Counts, by the same reasoning, are disclosed on purpose. Knowing an opponent holds seven cards is both
ordinary card-game information and a prerequisite for addressing them at all.

### What stays server-side

- The full `Position`.
- The RNG seed, which determines the deal.
- Raw `Transaction.effects`, which name every card they touch.
- The `Journal`, until the host declares the game over (§10, *The sealed record*).

### The moves a seat may make are narrowed like the cards

Enumerating the moves a position admits is a rules hook (§9); putting them on the wire is a projection, so the
two meet where every other narrowing happens:

```python
def project_moves(moves: Moves, observer: int | None) -> Moves:
    return tuple(move for move in moves if move.player == observer)
```

A seat reads its own options and no others. That matters most in a simultaneous phase, where `to_act` holds
every seat at once: the moves open to another seat name positions inside zones this one may not read, so serving
them would spell out the shape of a holding the zone pass is busy concealing. A spectator receives none, since a
move belongs to a seat.

**A view and its moves name one position.** `PositionView` carries `legal` beside the `seq` a client quotes as
`base_seq`, and `EventView` carries the moves admitted by the position its commit produced — the table `seq + 1`
commits in, which is the `base_seq` a move drawn from `event.legal` is submitted against. So a client reading the
stream knows its options from the stream, and asks no second question that an incoming commit would race into
answering about a table that has already moved.

A game that enumerates nothing serves an empty run, and its clients propose a move and let `validate` answer
(§9). `legal` is what an interface offers and greys out with; what the server admits stays `authorize` and
`validate`, which every path runs through.

### Events are diffs of projections

```python
class MoveView(BaseFrozen):
    player: int
    action: AnyAction | None


class ZoneChange(BaseFrozen):
    zone: ZoneId
    before: tuple[GameCard | None, ...]
    after: tuple[GameCard | None, ...]


class EventView(BaseFrozen, Generic[StateT]):
    seq: int
    observer: int | None
    move: MoveView | None
    changes: tuple[ZoneChange, ...]
    state: StateT
    legal: Moves  # the moves open to this observer once the commit has landed


def project_transaction(
    transaction: Transaction[StateT],
    before: Position[StateT],
    after: Position[StateT],
    observer: int | None,
    legal: Moves,
) -> EventView[StateT]: ...
```

**An event takes two positions.** What an observer *learned* is a difference: a card moving from a
concealed zone to a public one becomes identifiable, and the observer has to be told. So the changes are
computed as the difference between two projections for the same observer — the position the commit was
applied to and the position it produced. The event is leak-proof by construction, it reuses
`project_position`'s zone pass verbatim, and one audience rule governs both wire shapes.

A zone the observer reads the same way on both sides is left out, which is what keeps a shuffle of a
face-down pile silent for everyone it stays concealed from. Player 1 sealing a card becomes, for player 0,
"`hand:1` lost one, `tray:1` gained a placeholder".

**`MoveView.action` reaches the acting seat alone.** This is the part the diff cannot do. An action naming
`indices={0, 4, 7}` names *positions in a concealed hand*; the zone diff shows `hand:1` three cards
shorter and leaves the indices out, so an opponent holding the raw action could track a once-seen card
through a hand across several moves. Everyone else receives the seat that acted — a turn being taken is
public — and that is the whole of it.

### The no-leak property

The security boundary is stated as an executable property rather than as a code-review promise:

> Take a position. Rewrite every card the observer is not entitled to identify — with a freely chosen
> card, not merely with each other. `project_position` returns an **identical** result.

**Substitution as well as permutation**, and the strengthening is deliberate. Permuting concealed cards
among themselves leaves their multiset intact, so a projection that disclosed "the concealed cards are the
two red aces" would pass. Drawing a fresh card for every concealed place leaves nothing about them fixed
except how many there are and where they sit — exactly a client's entitlement — so any other influence on
the output fails the property, through a count, an ordering, a hash, a length, or a serialization quirk.

The same pair of properties runs over `project_transaction`, whose generated commits carry a *before* and
an *after* position scrambled or restocked together. Alongside them sit the entitlement properties
substitution cannot state: every card on the board has an entry in the view, each card shown sits at the
index the board holds it at, every card the observer may identify is present, an event names exactly the
zones that observer reads differently, and the action reaches the seat that made it and no other. All of
it under Hypothesis, generated rather than enumerated.

---

## 8. Undo, speculation, replay

Immutability makes three different needs collapse into three cheap mechanisms.

### Speculation needs no engine

Steps 6–10 of §6 are pure, so they factor out of the pipeline as one method, and that method is the whole
of speculation:

```python
def step(
    self, position: Position[StateT], move: Move, rng: Random
) -> Position[StateT]: ...
```

`submit` is that same private path plus the concurrency check and the commit that speculation does not
need. **The search API and the server API are the same function**, which is what keeps an AI evaluating
the rules the server enforces — including `authorize`, so a move the table would refuse is refused in the
search too.

AI search, "what if" previews and rules experiments touch the engine not at all. There is nothing to undo
because nothing changed: the caller keeps or drops the returned value. This is where P6 is load-bearing —
the pure path reads only its `position` argument, so it is indifferent to whether that position is the
table's current one or a node ten plies deep.

`step` requires a `Random` rather than defaulting one, because sibling nodes evaluated against different
draws are not comparable. The caveat becomes a type error rather than a paragraph nobody reads.

Setup is the third caller of the same machinery. The constructor runs `_deal_cards` where a command runs
`authorize`, `validate` and `expand`, then the identical advance-and-concatenate, with `move=None`.

### Undo reaches down to the publication mark

Pushing a snapshot costs a pointer copy, because a `Position` is immutable and shares freely. There is no
deep copy, no inverse-effect table to get subtly wrong, and no risk that an undone object is still aliased
elsewhere.

`undo` truncates the journal and pops the snapshot, and **both structures move together**, which is
checkable rather than hoped for:

```
len(history) == journal.head + 1
history[n]   == journal.replay(n)        for every n
```

The journal is the record; the history is a memo of positions so that `position`, `undo` and
`snapshot(n)` are O(1) instead of a full replay. The second line says the two agree always, which is what
licenses using the cheap one for play and the honest one for analysis. Truncating the journal alongside
the memo is what keeps `base_seq` honest: a head that still counted an undone transaction would validate
every later command against a position that no longer exists.

`snapshot(seq)` is the memo's public face, and events are what it is for: an `EventView` is the difference
between the positions either side of a commit (§7), so building one asks for `snapshot(seq)` and
`snapshot(seq + 1)` — two list reads, where `replay` would fold the journal twice per event.

The guard on `undo` is P5's publication mark. On a served table the adapter marks each transaction
published as it commits, so `undo` raises there: un-revealing information players have already read is a
state the engine cannot reach rather than a policy the server declines to implement. In-process drivers —
setup, tooling, tests, tentative construction — publish nothing, so their whole run stays undoable.

**One limitation, in place deliberately.** `undo` rewinds the position and the journal, and leaves the RNG
where it stands. Undoing a transaction whose `expand` consumed randomness and resubmitting the same move
draws afresh and may resolve differently. This is correct for replay — P2 records outcomes, so `replay`
consults no RNG — and it is stated in the docstring rather than fixed, because snapshotting generator
state would put non-game state into the memo and make it something other than a list of positions.

### Retroactive analysis

```python
past = journal.replay(upto=17)
knew = project_position(past, 17, observer=1)
```

Two lines reconstruct **what player 1 knew after move 17** — not "what happened", which is easy, but what
one participant's information state was, which is the thing worth analysing. Projection is the only path
from truth to client and a pure function of its arguments, so pointing it at a historical position is all
it takes.

This is what pays for P2. Shuffles stored as seeds would put `replay` at the mercy of the RNG
implementation, and this would quietly stop being true.

---

## 9. Writing a game

Concrete games derive from `Game`. The engine half of `Game` is concrete and inherited; the abstract
surface is rules alone.

### What the engine supplies

Per P6, one mutable cursor and one method that moves it. The commit method folds the effects, appends the
transaction and extends the memo, in that order, so a journal that refuses a transaction number (§5.4)
leaves the memo untouched and the two structures in step. `state`, `board` and `players` are properties
over the cursor, so a game reads them and assignment to them does not typecheck.

`__init__` builds the origin from `zones` and `_initialize`, then expands the deal and commits it through
that same commit method. **Setup is the same pipeline as a move**: the deal is journaled, projectable,
replayable and — before publication — undoable, with no line of code that exists for setup alone.

Inherited verbatim, and listed here because they are the whole of what a game gets for free:

| Method | Gives |
|---|---|
| `submit(move, base_seq)` | steps 5–11 of §6, and the transaction it committed |
| `settle()` | the transactions the rules still owe, until the table comes to rest |
| `step(position, move, rng)` | the same pure path, applied to any position (§8) |
| `undo()` | one unpublished transaction rolled back |
| `view(observer)` | this observer's projection and the moves it may make, stamped with the head |
| `events(observer, since)` | every commit from `since` onward as that observer learns of it |
| `snapshot(seq)` / `replay(upto)` | the position at a sequence, cheaply or honestly |
| `mark_published()` | the publication mark advanced to the head (P5) |

A game that overrides any of them has found a missing hook.

### What a game supplies

| Hook | Kind | Responsibility |
|---|---|---|
| `zones(players, deck)` | abstract | the components on the table before anyone touches them: the layout, its visibility policy, and the zone the undealt deck sits in |
| `_initialize(players)` | abstract | the pre-deal state — what is knowable before a card has moved |
| `_deal_cards(position, rng)` | abstract | the physical deal: shuffle and distribute |
| `_validate_initial_deck(deck)` | abstract | conditions on supported initial decks |
| `_final_validation(position)` | abstract | game-specific checks on the dealt position |
| `validate(position, move)` | abstract | raise `IllegalMove` unless the move is permitted |
| `expand(position, move, rng)` | abstract | translate an intent into primitive effects |
| `advance(position, move, rng)` | abstract | turn and phase transitions, scoring, terminal detection |
| `authorize(position, move)` | concrete | raise `NotYourTurn` unless this seat may act. Default: `move.player in state.to_act` |
| `moves_of(position, seat)` | concrete | enumerate the moves one seat may make, for a search and for the interfaces they reach through `view` (§7). Default: none |
| `legal_moves(position)` | concrete | the whole move list this position admits. Default: `moves_of` gathered over the seats `to_act` names |
| `capacity` | declaration | the tables the game is played at, which the engine holds every table it opens to. Stated by every game |
| `intents` | declaration | the actions the rules answer to, which the engine holds a move to at step 7 of §6. Default: `None`, which is every intent |

Five rules for reading that surface:

- **Every hook takes its subject as a parameter.** No hook reads the engine's cursor. That is P6, and it
  is why each one works on a speculative position, a replayed position, and the table's own.
- **`rng` appears in three hooks**, `_deal_cards`, `expand` and `advance`, and is non-optional in all of
  them. Elsewhere its absence from the signature is the statement that the hook consumes no randomness.
  `advance` holds one because the rules draw where no seat has acted: the shuffle that opens the next round
  and the seat that leads it are settled during settlement, and each draw reaches the journal inside the
  effect it decided, so replay consults no generator (P2).
- **Three hooks ship with a body**, because most games want the default and the ones that do not want to
  change a policy rather than supply a missing one. `authorize` admits the seats the cursor names; `moves_of`
  enumerates nothing, which suits a game whose move space is wide or awkward to list and leaves clients to
  propose a move for `validate` to answer; and `legal_moves` gathers `moves_of` over the seats `to_act` names,
  which is a body a game changes only to answer for a whole position at once rather than seat by seat.
- **Two of that surface are declarations rather than hooks**, stated once in place of being written.
  `capacity` names the tables the game is played at and the engine holds every table it opens to it, so a
  seating range is a value rather than a check written four times over; a game stating none stands no table up
  at all, which is what keeps the range from being left out. `intents` names the actions of §5.3 the rules
  answer to, and the engine both refuses the rest and hands the game its own move back at the type it stated.
  A game annotating it — `ClassVar[Intents[Take | Give]]` — has those actions reach its signatures, so a
  `match` over an intent is covered by the cases it named. Left at None it states a condition on nothing, and
  every intent there is reaches the rules.
- **`advance` is a total function of its arguments.** It cannot remember having run, so `phase` carries
  that. Settlement leans on the same property: it calls `advance` until the answer is empty, which means
  something only while the answer depends on the position rather than on how many times it has been asked.

`advance` receives the move because it shrinks `to_act` in a simultaneous phase and rotates the turn in a
sequential one, and a position records who is *to* act rather than who just did. Passing the move keeps
`advance` pure in its arguments; the alternative is every game carrying a `last_actor` in its own state,
where it would be journaled, projected, and stale the moment settlement ran. `None` says the rules are
being asked what they owe with no seat behind the question.

**Two of the setup hooks state a condition rather than build anything, and the conditions games keep asking
for are stated below them.** `confirm_standard_deck(deck)` is the whole of `_validate_initial_deck` for a game
played with standard decks and the jokers it names; `confirm_dealt(position, family, sizes)` is the whole of
`_final_validation` for a game whose deal owes each seat a count, and it names the seats holding another. Both
refuse with `GameValidationError`, as `Capacity.confirm` does for the seating the engine checks on the game's
behalf — so a table refused while standing up is refused in the vocabulary of §6, and a game writes the
condition rather than the sentence.

### The origin is the components; transaction 0 is the deal

The origin is a table where the box has been opened and nothing else has happened: it contains no
decisions. Every decision — how the cards were shuffled, who got how many, who leads — is an effect.

That line is what puts the opening state in `advance` rather than in the constructor. Take the rule *the
player holding 2♦ leads*, which is how a climbing match opens. `_initialize` runs before anything is dealt, so
nobody holds 2♦ yet; and the deck it might be handed is still in its given order, because the shuffle is a
`Reorder` produced inside `_deal_cards`. A leader computed there would be computed from an arrangement that
never occurs.

So `_initialize` states what is knowable before a card moves — a `"deal"` phase, an empty `to_act`, a
zeroed score — and the rule goes where every other "whose turn is it" answer lives: `advance`, run on the
dealt position, in the branch that reads `phase == "deal"`. The branch that runs after every later move
answers the same question from the move it was given. In climbing the leader is the 2♦ holder to open with
and the seat that went out of the last round thereafter; splitting the first answer into the dealer would put
two answers to one question in two places, with nothing but chronology separating them.

`ClimbingGame` is that shape written out (`docs/games/climbing.md` §4). Its `opening_state` writes a `choosing`
phase naming no seat, since the seat the match opens on stands in cards it is handed too early to read;
`advance_round` answers that phase by reading the dealt hands and writing the turn, which is one settlement
transaction and the second of the two a table stands up with. So the choice is journaled, replays without a
generator, and is answerable after the fact from the transaction that made it.

Three things follow that a constructor-computed leader would not give:

- **It is journaled.** "Why is player 2 leading?" is answerable from transaction 0. A value assigned in
  `__init__` is invisible to replay, to projection, and to the historical-knowledge query of §8.
- **It generalises with no new machinery.** A leader decided by bidding is several transactions in a
  `"bid"` phase. A leader decided by cutting the deck is a `SetState` carrying the drawn value — recorded,
  per P2. A leader decided by 2♦ is a query over the dealt position. All three are effects from `advance`.
- **It survives undo and replay** like anything else, because it is a special case of nothing.

The same line explains why `zones` returns **populated** zones and why `_deal_cards` emits no `SetState`.
Deciding which zone a deck starts in means knowing the game, so it belongs to the game rather than to a
`Board` factory (P3); and turn logic in the dealer would write "who leads" twice.

### A match is a game plus bookkeeping

Most games worth writing are a series of rounds: dealt afresh, led by a seat in turn, scored into a
standing until the standing meets the ending the table was opened with. `cardwork.rounds` states that shape
once. `RoundGame` fills in `advance` and leaves a game five hooks, four of them about a single round;
`RoundState` carries the standing beside the tally of the round in play; `Redeal` gathers, shuffles and deals
out what the last round left where it lay, drawing again where a game asks something of the round it opens on.
A round boundary is an ordinary settlement transaction, so projection, replay, events and the adapter need
nothing new — which is the whole reason the layer is small. `docs/rounds.md` states it whole.

**How long a match runs is a setting of the table, and it travels in the record.** `Conclusion` holds the three
clauses a match played in rounds can end on — a count of rounds, a score some seat reaches, a lead one seat
holds over the next best — and states at least one of them, so a match with no ending is unconstructible. A
table is opened with one, `RoundGame` stamps its clauses onto the cursor the first round opens on, and
`match_over` reads them there. So the ending obeys P2's spirit as the shuffle does: it is data in the journal
rather than an attribute of the object that dealt, a replayed position describes the match it was always going
to be, and `Readout` reaches it by the one route every figure of a cursor reaches a client by. Which end of the
standing *wins* is the game's own rule rather than the table's, so it stands beside the clauses as `award` and
its vocabulary, `Award`, sits in `cardwork.states` beside the `points` tuple it reads.

The games in `cardgames` are the worked examples, and between them they exercise both shapes of turn:

| the game | plays | reads for |
|---|---|---|
| `cardgames.backend.passing` | a sequential turn: one exchange with the pile, then a pass round the table | an outcome a rules question over `combinations` decides, and a match ending on a lead rather than a count |
| `cardgames.backend.showdown` | a simultaneous turn: every seat commits one sealed card, and they turn over together | `to_act` holding every seat, `HIDDEN` zones, and a turn settled behind no move at all |
| `cardgames.backend.shedding` | a turn of two minds: shed a set of one rank, or draw a card and pass it on | a move naming several cards, a hand that grows, and a game that added no primitive below it |
| `cardgames.backend.climbing` | a combination put down on lead, and the seats after it climbing over what stands there or passing | a `Ranking` asked for every move a hand can make, a `Combination` carried in the cursor, a turn given up by word, a leader read off the cards a deal handed out, and a standing of penalties won at the low end |

**All four are played end to end over the endpoints in the suite** (§13), and each is opened by name through
`cardtable` (§10, *The host*). Climbing is the one that reads the standing the other way about: a round closes
on the seat that plays its last card and scores every seat the worth of the cards it is caught holding, so its
`award` is `Award.LOWEST` and the same `points` tuple names a winner at the other end
(`docs/games/climbing.md`).

---

## 10. Serving a table

### The port

The seam is a `Protocol` **declared in `cardserver`**. The consumer owns the interface: the engine is
written for the table alone, and the port states which part of its surface a transport depends on. A game
satisfies it by having the methods, which leaves the core free of any mention that an adapter exists.

```python
class Table(Protocol[StateT]):
    @property
    def players(self) -> int: ...
    @property
    def head(self) -> int: ...
    @property
    def journal(self) -> Journal[StateT]: ...

    def submit(self, move: Move, base_seq: int) -> Transaction[StateT]: ...
    def arrange(
        self, zone: ZoneId, order: Order, seat: int, base_seq: int
    ) -> Transaction[StateT]: ...
    def settle(self) -> Transactions[StateT]: ...
    def view(self, observer: int | None) -> PositionView[StateT]: ...
    def events(
        self, observer: int | None, since: int
    ) -> tuple[EventView[StateT], ...]: ...
    def mark_published(self) -> None: ...
```

Everything above it — HTTP, JSON, auth, sockets — is an adapter; everything below is a pure function.
`head` is on it because the streams need to know when there is more; `journal` because the post-game
reveal serves it; `mark_published` because publication is the adapter's act; `settle` because the grace
window is the adapter's clock; `players` because a layout is built for a table of a size; `arrange`
because a player sorting its own cards is a command a client sends, and the engine is where a commit is
made (§6).

**A table is served with the arrangement it is read through, which is a port of its own.** A client asks for
two things and they are answered from different halves of the design: the cards its seat is entitled to,
which the rules produce, and the layout it draws them into, which is stated apart from them. So `protocol.py`
holds a second `Protocol` beside `Table`, satisfied by `cardwork.presentation.Scene` and by anything else a
host keeps a table's arrangement in:

```python
class Presentation(Protocol):
    def layout(self, players: int, observer: int | None) -> Layout: ...
```

A table opens with both — `registry.open(table_id, table, presentation)` — and `TableSession` answers for
each, which is what puts a layout and a projection behind one credential and one seat.

**`StateT` is invariant, so the registry names no state type and a third `Protocol` is what it stores.** A
covariant state type would let one registry hold `Table[GameState]` for any game, and it is unsound:
`Journal.append` and `Effect.apply` use the parameter in argument position, so a table built for one state
type cannot stand where a table for the base type is expected — the caller would be free to hand it a bare
`GameState`. Making the registry generic instead binds one rule set per process, which is exactly what a
table chosen at runtime cannot do. So `protocol.py`'s neighbour `sessions.py` declares one table in service
read without naming its cursor:

```python
class InService(Protocol):
    @property
    def head(self) -> int: ...
    def view(self, observer: int | None) -> BaseFrozen: ...
    def events(self, observer: int | None, since: int) -> tuple[Commit, ...]: ...
    def layout(self, observer: int | None) -> Layout: ...
    ...
```

The three generic answers erase to what a client is served anyway: `view` and `record` to their pydantic base,
`events` to a `Commit` carrying the sequence and its own JSON. Return position is covariant, so
`TableSession[PassingState]` satisfies it structurally with nothing changed in `TableSession` itself, exactly
as a `Game` satisfies `Table`. The type parameter is kept where it earns something — `registry.open` is
generic per call, so a table is opened at its own state type — and dropped where the routes were already
declaring `response_model=None` for the same reason (`/view`, `/events`, `/journal`). What it buys is one
registry serving whatever game a company settles on, with each game's own state type reaching the wire with
every declared field intact.

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/tables/{id}/moves` | Submit a command. Body: `{move, base_seq, idempotency_key}`. Answers `{seq}`, or a refusal from the table below. |
| `POST` | `/tables/{id}/arrangements` | Lay out a zone of this seat's own. Body: `{zone, order, base_seq, idempotency_key}`. Answers `{seq}`. The seat comes off the credential, so the body names none. |
| `GET` | `/tables/{id}/layout` | How this observer lays the table out: its own zones and gestures, and the shared table. Asked for once on join. |
| `GET` | `/tables/{id}/view` | Full projection for this observer, stamped with `seq`. Used on join and reconnect. |
| `GET` | `/tables/{id}/events` | SSE stream of projected events, resuming from `Last-Event-ID` or `?since=`. |
| `GET` | `/tables/{id}/journal` | Full reveal for analysis, once the host has called the game over. |

A table is gathered before it is dealt, and the routes that happens over are carried by the same application,
since a person reaches the room and the table at one address:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/offerings` | Every game this host offers, the tables each seats and the deck counts each is dealt from. Open to anybody. |
| `POST` | `/tables/{id}/guests` | Arrive on the code that admits. Body: `{code, name}`. Answers `{token, gathering}`. The one route open to a stranger. |
| `GET` | `/tables/{id}/gathering` | The room as this guest reads it: the company, what is settled, where it stands. |
| `GET` | `/tables/{id}/gathering/events` | SSE of one whole reading per revision, resuming like the table's own stream, ending on the deal. |
| `PUT` | `/tables/{id}/seat` | Take a seat, or stand up by naming none. Body: `{seat, base_revision}`. |
| `PUT` | `/tables/{id}/choice` | Settle what is played. Body: `{choice, base_revision}`. |
| `POST` | `/tables/{id}/deal` | Deal the table the company settled on, which opens it and ends the gathering. Body: `{base_revision}`. |

`PUT` for the seat and the choice because both state a value; `POST` for arriving and dealing because both
happen once. The gathering routes are carried by a router `create_app` includes where a host gathers its own
tables, so a deployment serving a table already seated mounts none of them.

Request and response bodies are frozen models that forbid undeclared fields, so a body carrying a field
the schema leaves out is refused with `422` before a handler runs.

`/layout` is the one projection whose type is not generic in the game's state, so it is the one that
produces an OpenAPI schema rather than declaring `response_model=None`. That is what lets an interface
generate its layout types from the served document and hand-write only the view ones.

Refusals are mapped kind by kind, one handler each:

| Raised | Status | Meaning |
|---|---|---|
| `Unauthenticated` | `401` | the credential holds no seat at this table |
| `UnknownTable` | `404` | this server holds no such table |
| `WrongSeat` | `403` | the credential holds a seat other than the one the command was made for, or holds none at all |
| `JournalSealed` | `403` | the record opens once the game is over |
| `NotYourTurn` | `403` | the rules withhold the turn from this seat |
| `StalePosition` | `409` | commits have landed since `base_seq` |
| `IllegalMove` | `422` | the rules reject what the move asks for |
| `ArrangementRefused` | `422` | the seat arranges no such zone, or the order is no permutation of it |
| `Unadmitted` | `403` | the code offered admits nobody, the company is as large as it gets, or wrong codes have come too fast from one address |
| `NoSay` | `403` | the guest holds no say over what the table plays or when it is dealt |
| `NameTaken` | `409` | that name is already read at this table |
| `SeatTaken` | `409` | another guest of the company holds that seat |
| `GatheringOver` | `409` | the table is dealt and its gathering is done |
| `SeatsEmpty` | `409` | the deal was called for while a seat stood empty |
| `StaleGathering` | `409` | the gathering has moved past the revision the command was built on |
| `NoSuchSeat` | `422` | the seat stands outside the table the gathering settled on |
| `GameValidationError` | `422` | the rules refuse the table or the deck the choice asks for |

One handler per kind rather than one over a root exception is what keeps the mapping open at the edges:
Starlette walks an exception's MRO, so a game raising its own subclass of `IllegalMove` is answered `422`
without the adapter knowing that subclass exists. Anything outside the list reaches the server as the
defect it is.

**Both commands are answered alike, and both take a key.** `CommandAccepted` is one shape for the sequence a
commit took, since what either command leaves behind is one commit in the record every seat reads; and an
arrangement is deduped by its key for the reason a move is, so the retry a flaky network prompts lands the
order once rather than reading back as a table that has moved on. What the two do not share is the window:
`submit` restarts it and `arrange` leaves it standing (§6).

### Why SSE

**`Last-Event-ID` is the journal `seq`.** SSE has reconnection in the protocol: a dropped stream is
reconnected by the browser, which sends the id of the last event it received, and the server resumes from
`seq + 1`. Catch-up-after-disconnect — normally the fiddliest part of a realtime game — is a header lookup
and a slice of a tuple. `?since=` serves the first connection and any client that would rather say where
it stands; `Last-Event-ID` wins when both arrive, because the browser sends it unasked and it describes
what the client actually received.

**The journal is the stream's buffer.** A stream holds a cursor, asks the table for everything from it,
writes those frames, and waits to be told there is more. Nothing is queued per client and nothing is
dropped: a slow reader falls behind and catches up from the record, and a client that connects at seq 40
is served as one that never disconnected. Each frame is `id: <seq>`, `event: commit`, and the event view
as JSON.

SSE also matches the traffic shape. A turn-based card game sends a handful of commands per player per
minute and broadcasts a little more: rare client→server messages, a steady server→client trickle. HTTP
`POST` for the rare direction buys idempotency keys, retries, caching semantics, ordinary bearer-token
auth and standard status codes. SSE for the other buys push with no framing protocol, and it traverses
proxies that mishandle WebSocket upgrades.

**A silent stream is a table where nobody has moved**, which is the normal state of a turn-based game
between turns, so there are no heartbeats. A keep-alive frame is a few lines the day an intermediary turns
up that drops idle connections.

**When to choose WebSocket instead.** If client→server traffic becomes chatty — live chat, drag previews,
per-second clocks — or sub-100ms latency starts to matter, a single duplex connection wins. The port above
stays as it is and the adapter changes, which is the point of having a port.

### Why FastAPI

- The domain is already Pydantic v2, so request and response schemas are the models that exist. This is
  the strongest argument.
- OpenAPI generation is free for the request side, so a front-end gets a typed client for commands with no
  hand-maintained schema.
- SSE needs no extra dependency: a streaming response over an async generator.
- In-process transports run the whole stack with no live server and no port allocation, so the
  request/response endpoints are tested end to end.

Two properties of the framework shape the code:

**A state-generic response type has no schema**, so the `view` and `journal` routes declare no response
model and FastAPI serializes the returned model directly. `PositionView[StateT]` is a concrete type once a
server binds one, and a schema built from a type variable would describe nothing. The command side keeps
its full schema, which is the side a client has to get right.

**In-process HTTP clients buffer the whole response body**, awaiting the application to completion, so an
endless stream read through one yields its first frame never. The streams are therefore tested through a
small harness that drives the ASGI application directly and reads body messages one at a time — the real
routes, the real dependencies, the real streaming response, still with no port.

Alternatives weighed: **raw Starlette** gives up validation and dependency injection for no gain, since
FastAPI *is* Starlette; **gRPC** duplicates schema work already done in Pydantic and complicates browser
clients; **socket.io** imports a JavaScript-centric protocol and its reconnection semantics for problems
SSE already solves.

### Concurrency

The domain is synchronous and pure, so it needs no locks internally. Two commands for the same table are
serialized so that each sees the head the other left.

**One writer per table.** A registry holds a session per table, and each session holds an
`asyncio.Condition`. All command handling for a table happens inside it, and the pure domain call within
it runs to completion without yielding, so a reader arriving between two commands finds a whole position
and takes no lock to do it. Different tables run fully concurrently. This is the only place concurrency
exists in the system.

**The lock is a `Condition` because the streams need the wakeup anyway.** A commit does two things under
the same lock: close the table to undo, and tell every waiting stream there is more to read. `Condition`
is a lock with exactly that signal attached, so "one writer" and "wake the readers" are one object and
stay in step.

A session also holds the two things a served table needs that a bare game does not: the `key -> seq` map
behind §6's idempotency, and the timer of the grace window.

### The gathering

A table stands **gathered** before it is dealt. `gathering.py` holds the room: its code, its company, the seat
each guest has taken, the choice settled, and a `revision` that counts the changes. A gathering knows the name
of no game — it validates a `Choice` against the `Offering`s it was handed, exactly as the page draws a
`Layout` without knowing a game — and turning a settled choice into a table in service is a port of its own:

```python
class Opening(Protocol):
    def open(self, table: TableId, choice: Choice, names: Mapping[int, str]) -> None: ...
```

`cardtable.catalogue` is what satisfies it, so the one module naming `cardgames` is still the one module
naming `cardgames`.

**Concurrency is the table's, one layer up.** A `revision` only grows and a command quotes the one it was
built on, so two guests settling the choice at once leaves the second told rather than overruled — `base_seq`
for a room. What a gathering needs no lock for is that every change it goes through happens between two
awaits: a table serialises its commits and a gathering commits nothing. Its stream re-reads and re-answers
the whole room at each revision, the way `streams.py` already serves a table, and holding that stream is what
reads a guest as **present**, so the company a page draws is the company watching it. The deal is the last
thing a gathering has to say, and the frame carrying it closes the stream and takes every page at the room
over to the table.

**A code is a hand of card ranks.** `codes.py` reads a hand out of what somebody offered greedily and left to
right, over the code in capitals with the separators a person writes it with dropped — so `10` is taken where
`1` would be, and since neither `1` nor `0` names a rank alone every offering has one reading: `K10A7Q3` reads
as six ranks and `012345` as none. What a table may *gather* on is narrower, and `code_in` states it: six ranks
drawn from the twelve written in a character, so a code stands six ranks long and six characters wide at once
and a person types exactly what they counted. A code is passed on out loud, so it admits however it was written
down, and `admits` compares the two hands under `compare_digest`. Twelve ranks over six places name some three
million codes, which is a number a program reaches and a person does not, so what guards a code is the rate
rather than the length: a `Turnstile` counts wrong codes against the address they came from and stops reading
them past its allowance.

**The names a company settled reach the plaques without widening the port.** `Plaque.name` reads `"Seat {n}"`
until a host holds a name for one, so `naming.py` wraps a `Presentation` and reads the gathered names onto the
plaques of the layout it answers with. `Named` satisfies `Presentation` structurally, so `registry.open` takes
it where it took the `Scene`. Names settle at the deal and never change, which is what makes it correct: a
layout answers for the match and a page reads it once as it joins.

### Identity

The adapter maps a credential to a **seat index** for a given table, behind a `SeatPolicy` protocol. The
domain sees `int` and a spectator is `observer=None`; users, sessions, accounts and authentication are the
adapter's vocabulary. This keeps the `zones` and `views` layers testable with plain integers and keeps
identity policy where it changes without touching game logic.

**The gathering *is* that policy**, which is what lets a table be played without accounts. A token is
`token_urlsafe(32)`, minted as a person arrives on the code and under the name the company will read them by,
and `Gatherings.seat` answers the six playing endpoints out of the room: **a token holds the seat its guest has
taken, holds none while they are standing, and belongs nowhere when it was minted at no gathering here.** So
watching is standing at the gathering, playing is having taken a seat, and play is authorised by the same
arrival that seated it — no endpoint of the table needed a line changed. A deployment with accounts writes its
own policy and changes nothing else.

Who may settle what is played is a second question, and it stands behind a `SayPolicy` of its own. The shipped
`SeatedSay` asks only that a guest is sitting at the table, which is the whole of what a friendly table asks: a
guest standing by is told rather than obeyed. A deployment holding groups or owners answers the same call out
of what it knows of them.

**Plain HTTP on a LAN means a token crosses the local network in the clear.** That is the accepted condition of
play among people in one room; TLS is out of scope here. It also settles what a page may reach for: a plain
address is no secure context, so the browser holds back `crypto.randomUUID` and `crypto.subtle` there. The one
thing the page draws at random is the name a command carries, and `play/sending.ts` draws it through
`getRandomValues`, which answers at every address.

One check bridges identity and the domain, and §6 step 2 is the whole of it: the seat behind the
credential must equal `move.player`, and a spectator holds no seat to act from. The engine trusts
`move.player` because a seat number is all it knows about identity, so the number is settled here, where a
credential is all the server knows about who is asking. Without it, `move.player` would be a claim rather
than a fact, and every rules check downstream would be enforcing the turn order of whoever asked most
recently.

An arrangement makes no such claim to check, so the same reading answers a shorter question — *is a seat
asking at all* — and the seat it reads is handed to the engine. The spectator half is one answer for both
commands, which is what keeps a client holding no seat from reaching either.

### Publication

The publication mark advances **as a commit lands**, inside the lock, rather than after the frames have
been written. That instant is the earliest a concurrent read can see the new position, and P5's mark has
to be true from the moment a client *could* have read a transaction. So on a served table the mark equals
the head and undo is mechanically unavailable there (§8).

### The grace window

Settlement is held back by a configurable delay, and each move restarts the wait. This is the whole of
§4.4's "too late", and it lives here because P1 keeps clocks out of the core.

Restarting on every move is what gives each seat its moment: the last seat to act does not close the
round on the seat before it, which under simultaneous play would make the window a race between clients.
An arrangement restarts nothing and opens nothing, since a seat sorting its own cards commits nothing for
anyone to ask back — a table where the seats have only sorted their hands holds no timer at all, and one
sorting inside an open window leaves the moment the last move opened where it stood. Sorting a hand
therefore cannot hold a round open, which a restart would let it do for as long as a player kept dragging.
A window that passes over a round still in play settles nothing, since `advance` owes nothing until the
last seat has acted — so the timer is free to fire whenever, and correctness rests on the rules rather
than on the clock. A grace of zero still yields to the event loop before settling, which lets a test wait
for the window rather than sleep through it.

Ending service cancels every timer still in hand, so a table that closes mid-window closes cleanly.

### The sealed record

The journal endpoint is the post-game reveal. Served mid-game it would hand every client every concealed
card, because effects name the cards they touch (§7) — a journal is the one shape in the system that
discloses everything at once.

So the record is closed until the host calls the game over, and until then the endpoint answers `403`.
Deciding when a game is over is the host's, since the phase that means "finished" is a game's own word
(§9) and the adapter reads no rules. The record then reads the same to every client, seat and spectator
alike, so the request needs no seat at all.

### The host

Two contracts say a game class and FastAPI may not meet inside `cardgames` or inside `cardserver`, so they
meet in `cardtable`, which nothing names. It is a composition root and holds one module per concern:

| module | states |
|---|---|
| `cli` | the file a run is configured from, every value of it a command line states instead, and the announcement a run opens with |
| `catalogue` | which games this host offers, the deck and scene each is dealt with, and the lobby that gathers them |
| `hosting` | one table gathered and then in service: a registry, a lobby, an application, and the page beside it |
| `config` | the whole of one run: the table gathered, the choice it opens on, the pack it draws with, and where it answers |
| `reaching` | the addresses a run is reached at, which is where a person is handed a line to open |
| `settings` | what one table is opened with: the name it answers under, the code it gathers on, its seed, its window |
| `service` | where a table listens, where it says it is reached, and how much of what it does reaches a log |
| `interface` | a built player interface served from the root of the same application |
| `artwork` | the pack of pictures a table draws with, served beside the page |
| `games` | the names a person asks for a game by, which the catalogue turns into rules |
| `paths` | where the checkout keeps what a host reads off disk: the configuration, the artwork, the page |

`catalogue.opened(settings, choice, artwork)` is the whole of it, and `catalogue` is the one module of the
repository naming `cardgames`. It builds the registry, the `Deals` that satisfies `Opening`, and the
`Gatherings` that is both the lobby and the seat policy, then hands the lobby to `hosting.serve` whole — one
object arriving twice at `create_app`, since the playing routes ask only for a seat where the gathering routes
ask for the room. The state type of a game is bound inside `Deals.open` and stays there: `Hosted` names an
application, a table name, the code and the page, none of which is generic, which is what lets one host deal
games whose cursors are of different shapes through the one entry point.

**What the host offers and what the rules deal are two statements, and a test holds them together.** An
`Offering` is built from each game's own `Game.capacity`, its `Scene.title` and the deck counts its
`_validate_initial_deck` accepts, all of which already existed with no way out over HTTP. Every table an
offering promises is settled in a test — each count of decks at each seating it names — and each of them either
deals or is refused with a sentence a company can act on, which is what rules out the third answer: a promise
that hangs or one the server meets as a defect. The game keeps the last word, since a seating and a count of
decks state something apart and a rule may turn on both: `climbing` reads a hand of at most twenty-six cards, so
two decks halved between two seats are refused where they are asked for. What would keep such a choice out of a
company's hands altogether is an offering stating the counts a deck is dealt at per seating, which is a wider
answer than one deck list per game.

**One file states a run, and a command line states where a run departs from it.** `config.yaml` beside the
repository holds the table gathered, the choice it opens on, the pack it draws with and where it answers, and
`Configuration.read` validates the whole of it as it is read: every field is asked for outright, so a value
left out is refused at the file rather than met as a surprise at the table, and a key the configuration holds
no field for is refused with it. The port stands at a settled number, since a local run answers at the same
address until it is told otherwise, and a run stating no seed or no code draws one, so each table deals a match
of its own behind a hand of its own and the announcement names both — the seed for a run that wants that match
again, the code for the people about to join. What the file states of the choice is where the gathering opens
rather than what it plays, since the company settles that: a seating the game seats nowhere is refused as the
room opens, and what config refuses is a table of nobody and a game this host holds no rules for. Each option
of the command line stands empty until it is given, and an option left alone is answered by the file — so a
value a person turns lives in one place, and `make play` passes on only what it was handed.

**Where a run listens and where it is reached are two questions.** A run bound to `0.0.0.0` answers on every
interface and at none: printing the bind address hands a person `http://0.0.0.0:8421`, which nobody can open.
So `reaching.py` answers the second question — the advertised address where one is stated, the machine's own
address beside the loopback where the bind is a wildcard, and the bind address otherwise. The machine's own
address is read off the route to an RFC 5737 documentation address on a UDP socket that sends nothing, and a
machine holding no route out answers with the loopback alone. The announcement then prints one line per address,
each carrying the table and the code, so play across a room is opening the line you were handed.

**Every path a run reads is stated in `paths`, at the foot of the host.** One module climbs from its own
file to the checkout, and the artwork, the interface and its build are named from there — so a directory
moved is one line changed, and a test holds the climb honest by reading the manifest at the top of it. The
host is the one package that names a place on disk at all: the rules and the adapter answer from memory, and
a fetch script takes the artwork's path from here rather than counting the directories over again.

**The page is served from the application the table answers on**, so the two are one origin: a client
reaches `/tables/...` with no cross-origin arrangement, and the seat token stays in a header rather than in
a query string a log would keep. The mount goes on last, which leaves every endpoint matching ahead of it,
and a checkout holding no build serves the endpoints alone.

**A table lives as long as the process.** A position is held in memory and a restart deals a fresh one, so
the host runs under no reloader and `uv run cardtable` is the whole of starting one. Ending the process ends
the service through the application's own lifespan, which drops every timer still in hand.

### The page

`frontend/` is the interface a table is played through: React and TypeScript, built by Vite into the directory
the host mounts. It holds three layers of its own, and each names only what is below it:

| layer | states |
|---|---|
| `api` | what a table and its gathering answer and what a client sends: the layout vocabulary, the room vocabulary, the projections, the seat, the refusals, and the request and stream plumbing the two clients are built on |
| `play` | what a client makes of those answers: where an address leaves a tab standing, the hand of ranks a code reads as, the places at a gathering and what holds its deal up, the choice a company may settle, the view a commit leaves, one card read against another, the figures a readout reads, the boundary a commit pauses at |
| `table` | what appears on screen: the table named, the arrival, the room, the company, the choice, the standing, the three groups of zones, a station, a slot, a card, a card carried by hand, the places a carry may land on, the line saying where play stands, the report a boundary is read at |

**Three states carry a person from an address to a seat**, and `App.tsx` is the whole of the routing: a tab
standing at no table names one, a tab at a table with nothing to speak through arrives on the code, and a tab
holding a token is in the room — the gathering until the company deals it, the table from then on. One reading
of the gathering carries the page across, since `dealt` turns true once: the guest who called for the deal
crosses on the answer to their own command and the guests watching cross on the frame the stream closes with.

**The page draws a lobby while holding the name of no game.** Every control of the choice is drawn from an
`Offering` — the games listed by their titles, the tables by each game's own seating, the deck counts where a
game admits more than one — so a fifth game reaches the page as another option and no line of it names a game.
`play/company.ts` and `play/choosing.ts` hold the decisions as pure functions: which places stand empty, whether
this guest holds a say, what the deal button reads, and what a choice becomes when it is carried onto another
game. `play/codes.ts` mirrors `cardserver/codes.py` so the page can read a code back to a person as they type
it and send the arrival once a whole one stands there; whether a code admits them stays the server's answer
alone.

**The types come from the document where a document exists, and by hand where one cannot.** `/layout` is the
one answer that stands apart from a game's own state, so it publishes a schema and `openapi-typescript`
generates the whole layout vocabulary from it — a slot, a gesture, a plaque, a readout, a move and the six
closed vocabularies besides. `/view` and `/events` are generic in the state a game declares, which leaves
FastAPI nothing to build a schema from, so `api/views.ts` mirrors them: a page reading a game's own cursor
reads fields the framework never declared, which is exactly what a readout names for it. `make types` writes
the document and regenerates the vocabulary, so a field added to a layout reaches the page as a compile error
rather than as a blank space.

**A projection is drawn by index, and a placeholder is a card in every way but its face.** `ZoneView.cards`
holds `null` at the true position of each card the observer may not read (§7), so a slot draws a back there
and a move addressing that position still lands where the player aimed — which is what makes showdown's
blind holding playable at all. A card an observer *is* served draws its face whichever way up it lies, since
being served it is the entitlement: a hand of four dealt face down is four cards its owner reads and four
counts to everybody else, and the interface marks the face-down lie rather than concealing what the projection
already disclosed.

**The stream is read over `fetch`, not through an `EventSource`.** A seat is held by the `X-Seat-Token`
header and an `EventSource` sends no headers, so putting the token in a query string is the only way to use
the browser's own stream — and a token in a query string is a token in every log the request passes through.
`@microsoft/fetch-event-source` carries what is given up in exchange: the retry, and the `Last-Event-ID` that
`streams.py` already resumes from. A client joins at `?since=<view.seq>` and resumes from the header
thereafter, so the position on screen and the sequence a move quotes stay in step whether the stream held or
dropped. A commit carries the cursor and the moves it opened alongside the zones it changed, so applying one
takes no further request.

**A stream is held for the page in front of the player.** A browser allows about six connections to one
address at a time, and an open stream spends one of them for as long as it stands. One tab per seat — which is
how a single machine seats several players, and the only way a seating of seven is read at all — spends every
connection on streams, and what a tab wants next waits its turn: the `POST` carrying a move sits in the
browser's queue, and a tab that joined once the rest were streaming holds the position it joined on and reads
a table that stands still. So `play/viewing.ts` holds the stream while the page is in view and lets it go
while the page is out of view, and `useTable` opens the next one at the commits the tab already holds. The
journal behind the stream is what makes that exact: a tab coming back into view is served every commit it
missed out of the record itself, so looking away costs a player the watching of what happened and nothing else.
A client says `Live` once its stream has opened rather than once it has joined, which leaves a tab that is
waiting for a connection saying so. A deployment reached over HTTP/2 multiplexes one connection per origin and
the limit lifts; the gate costs it a request per tab switch.

**A tab is told which table it stands at, and as whom, in the fragment of its own address.** The host prints
the address of the table it gathers, carrying the table and the code, and a browser sends a fragment to nobody:
the page reads both out of it as it loads, offers the code once on arrival, and speaks through the token from
then on. A token supersedes the code it was minted against, so the code leaves the address the moment one
exists and a reload rejoins as the same guest with no name asked again. So a person joins by opening the line
they were handed, and no address the server writes down holds a credential.

**A move is built by pointing, and a selection alone sends nothing.** `play/selection.ts` reads each move the
table says is open through the gesture matching it (§9), which yields the zone the move's positions address
and the place it commits onto. From there, one selection resolves into what the player sees: with nothing
picked up, every position any move names is *open*, and picking one narrows the open set to the positions a move
holding it could still name, which is the further narrowing a two- and three-card discard needs. What a player
reads of that is the cards left out of it — a card no move could name is drawn quiet, drained of its colour and
its light, so the cards in play are the ones lying plainly there and nothing is ever lit for being playable. A
quiet card is as solid as any other, since a card is paper and a card lying over another covers it, so a fan
reads as a fan whichever of its cards have gone quiet. A move whose positions are exactly those in hand is
*armed*, and the places the armed moves land on are the ones that light up. Clicking such a place commits, and
carrying the cards onto it says the same move by the same reading (below), so a click on a card is a card picked up
and nothing else; clicking a card in hand puts it back down, clicking a card no move names puts the selection
down, and clicking the page clears it. The renderer holds no
count and no rank in any of it: multi-card selection is the general case and a one-card move is where it
happens to stop.

**Whether the table is asking anything of this seat is read where the player is already looking.** The moves a
view serves are the whole of what a seat may do, so a seat served none is a seat with nothing to do: its own
panel lowers every card it holds and keeps their colour, which reads as a turn standing somewhere else. A turn
arriving marks that panel with the yellow a plaque and a station take at the same moment, so where the turn is
says the same thing in the middle of the table and at the near edge of it. The two quiets a hand can read in are
two statements rather than one twice over: a card drained of its colour is a card the moves in play name no use
for, and a hand lowered whole is a hand nothing is being asked of. A spectator holds a panel of nobody's and
reads the table as it stands.

**A zone is a drawing rather than a passage of text.** A pointer travelling across one carries cards, so the
sheet takes the browser's own selection off the zones and its drag off the artwork: a run dragged through paints
no highlight the page did not draw, and what a player is left holding after a carry is cards. The line under the
cards and the reports over them stay text, since those are the words a reader may want to take away.

**A move landing on no place is said where its words are drawn.** A pass names no card and no destination (§9),
and the arming rule reads it by itself: the cards in hand are exactly the cards it names, which is none of them,
so it stands ready the moment a turn arrives and stands down the moment a card is picked up. What the panel
draws for one is a card-sized place at the end of the hand, lettered with the caption the gesture carries and
labelled as the zones beside it are: it takes the room of a card in the width the cards are drawn to and keeps
that room while the cards in hand stand against it, going quiet where it stands. So the hand lies where it lay
through a turn played out instead, and the move a player makes rather than playing a card reads as somewhere on
the table. A turn standing ready to say one such move and one alone carries the space bar as well, which a
stroke resting on a control leaves to the browser, so a move said either way is sent a single time.

**A command is pinned to the position it was weighed against, and named so it lands once.** A commit sends
`base_seq = view.seq` with a name of its own, so a table that has moved on refuses it under `409` and one
request arriving twice commits a single time. A refusal a table answered stands, and a request that reached no
answer at all is sent again under the same name — the two are told apart by whether the table spoke. A refused
position is read afresh and the selection put down with it; a refused move keeps the cards in hand and the
sentence the game phrased reaches the line under them.

**A selection is held against the cards it was made on, not against the sequence.** A move quotes positions, so
what a selection stands for is the cards lying at those positions: `play/cards.ts` reads them out of the zone at
the moment of the picking, and every commit that follows is read against them. A table moves on for reasons of its
own — another seat plays, another seat sorts the cards it holds, the rules settle a round — and a selection
outlives every one of those, since none of them touched the cards a player is holding. Those cards moving is what
puts it down, which is the moment its positions would otherwise come to name other cards. A run of cards nobody at
this seat reads is the same run however it is permuted, which is what a position of a stock names anyway: the
place, rather than whichever card happens to lie in it. A command that lands puts the cards in hand back down
either way, since a move played takes them out of the zone and an order laid down leaves them lying elsewhere in
it.

**A hand is laid out by hand.** `ZoneView.arrangeable` is the table's word on whether this seat orders this zone
(§3.4), and where it says so every card of the run is taken hold of where it lies and carried to another place in
it. What the player reads while carrying is the run as it is about to lie — the cards it passes over close up
behind it and open at the place it is being let go over — and letting go sends exactly that reading, since
`table/dragging.ts` answers with one run that serves both the drawing and the order. The run drawn whole is what
may be ordered, so a spread reading a zone by the card on top of it says its depth in a figure and leaves the
ordering to the zones a player sees whole. The table settles it like any other command: the cards lie as the table
holds them until the commit carrying the new order arrives, which is also what tells every other seat nothing — a
permuted run of placeholders reads the same as it read (§6).

**A hand is put in order by asking for one as well.** Two presses stand at the end of the name of any zone this
seat lays out that holds a card and another to stand beside it — one reading the run by rank, one by suit — and
each lays the whole run down in the order it names. Which end the next press reads from is read off the run in
front of the player rather than remembered: a press sorts from the low card up unless the run already reads that
way, in which case it turns the run round, and each press letters the direction it is about to apply. So one
press per ordering carries both readings of it, and a command the table refuses leaves no button lettered with a
direction the cards deny. `play/ordering.ts` holds the order those readings are made against — the ranks as the
deck spells them, the suits as `Suit` declares them, each figure breaking the other's ties, and a card the order
can tell no way apart from its neighbour left lying where it lay. It is a display order the page owns rather
than a ranking a game states,
since sorting a hand is the player's convenience and two of these games rank no card at all; a game whose hand
wanted its own reckoning would state it on the scene. What a press sends is a permutation of the zone's own
positions, which is the command a carry through the run sends, so the optimistic order, the retry and the
refusal are the ones already described.

**A move is sent by carrying its cards onto the place it goes to, which is one gesture with the ordering of a
run.** Where the cards are taken is what says which of the two a hand is doing, and the whole of it is seven rules:

1. A press takes hold of cards: the ones already in hand where the pressed card is one of them, and that card
   alone otherwise. So a pair a player picked up travels as a pair.
2. The cards stay where the run draws them until the hand has travelled a few pixels from where it pressed. Below
   that the press is the click it has always been, which picks a card up.
3. Past that it is a carry, until the press ends.
4. **Within the run the cards came out of**, a carry sets the order: the block of them lies at the place the
   pressed card's own middle stands nearest, the rest of the run closes up around it, and letting go lays down the
   order the player is reading.
5. **Out over the table**, a carry sends them: the run stands as the table holds it, the cards travel from where
   they lie, and the carry picks them up as a click would — so the places the armed moves land on light up, and
   the one under the hand is marked more brightly still. Letting go there sends that move.
6. Letting go anywhere else puts the cards back down, which `Escape` and the browser taking the pointer away do as
   well.
7. A card let go under the hand that laid it is drawn already raised, and arrives there in one step.

**The reading follows the card rather than the pointer.** A card lies over its run while its own middle lies over
it, so a card pressed anywhere along its face reads as a card at the place it is drawn at — which is what a fan asks
for, since the near edge of a card is the part of it lying over the card before it, and a hand takes hold of a card
by whatever part of it shows. A lift of half a card's height is what carries cards out over the table, so a hand
chooses between the two readings by where it takes the cards and the table offers both at every moment. Every card a
move picks in is offered a grip, whether or not the order of that zone is this seat's own: a card is drawn off a
heap by carrying it onto the hand exactly as a card is played by carrying it onto a pile, and a run whose order the
table keeps is carried out of rather than through.

**Where a carry may land is the page's to answer, since the pointer belongs to the card that was pressed.** A
press holds every later event to that card, so what lies under a hand halfway across the table is a question the
card has no way to answer: `table/landings.tsx` holds the places for the whole page instead. Each of them states
its own drawing as it is drawn and takes it back as it goes, and the room one takes is read at the moment of the
asking, so a table redrawn under the hand is answered as it stands. The places lie one inside another — a seat's
corner of the table holds the zones drawn at it — so the smallest of the ones a point stands over is the one a hand
there means. Letting go comes to one of four things, which is the whole of what the gesture says: the place the
cards are sent to, the order the run has come to lie in, the cards put back down, or the press that carried them
nowhere.

**The page is held to the same standard as the Python.** Prettier formats it, ESLint reads it with the types
in hand — the strict type-checked rules, the React and hook rules, and three house rules carried over from the
guidelines: imports in a settled order, a signature stating its types, a figure that means something given a
name — Stylelint reads the sheet, `tsc --noEmit` checks it, and Vitest runs it. `make format`, `make lint`,
`make typecheck` and `make test` each run both languages, and pre-commit runs the page's formatter and type
check on every commit touching `frontend/` with its tests at push, which is the shape the Python hooks already
had.

**The page fits the window.** One screen high, `overflow: hidden`, three rows of `auto 1fr auto`: the
standing of every seat across the top, the table in the middle, the seat's own holdings and the line
saying where play stands at the bottom. Every card is measured from one height at the proportions of a real one,
and each group of zones takes the lesser of two heights: the one the window's own height affords it, and the one
the width leaves the cards it lies as many wide as. The script counts that width in cards — a heap as one, a row
as all of them, a fan as its overlap — and the sheet turns it into a height, so the panel a player plays from
draws a hand of three as large as the page has room for and a holding beside a row of five as large as the two of
them fit, at any size of window and without a scrollbar anywhere. Every card on the table is drawn at one height,
a holding read from across it at the height of the card on the pile, since both of them are cards lying on the
same table; and how many seats stand one above another at a side of it is the figure that height gives way to, so
a table of eight draws its cards smaller than a table of four does and all of them alike. A card is read by its
corner, which is the part
of it the card lying over it leaves showing, and a fan closes up as it fills: a handful lies open enough to read
every face and a holding of a dozen and more tightens to the room its zone has, so a hand of four and a hand of
seventeen are the same drawing at two overlaps.

**The felt divides its own height between the middle of the table and the seats round it.** How much room the felt
has is a fact about the page as it stands, so the felt is what states it: `container-type: size` makes it the
container its own contents are measured against, the zones at the centre take up to half of what it holds, and the
seats round the edge take the rest and divide that again by however many of them stand one above another at a side
and by however many lines each of them stands in. The width goes the same way — a quarter of it to each side that
holds seats, and what is left down the middle to the seats facing the near edge and to the cards they share. So the
two shares add to the felt's own room at every seating: the table stays inside it, the panel below keeps the room it
was given, and a card at another seat is drawn at the height of the card on the pile or at the height that seat's
own share affords, whichever is the lesser.

**Every player sits somewhere, and the page works out where.** `table/placing.ts` reads a layout's slots by the
seat each one belongs to and yields the groups the page draws: the shared zones in the middle, the observer's own
in the panel below, and a station for every other seat whose cards the table draws. The stations are gathered
into the three sides of a table by `ringOf`, ordered by `turn = (seat - observer + players) % players` from the
near edge the observer holds: the seats it plays into first up the left, the ones facing it across the top, and
the rest down the right, two facing where the seats beside them pair off and one where they do not. So a table of
four reads left, across and right, a table of seven two seats up each side and two across, and a spectator reads
the ring from the first seat instead. Each side is a run of its own between the middle of the felt and the edge of
it, so the room one seat takes is room its neighbours give way by: no seat is drawn over another and no name is
covered, whatever the cards at either of them come to. A seat the layout draws no cards for takes no
station: its holding is a figure on its plaque, which is how a game keeps a zone off the table altogether.

**A group of zones lies in lines, and a seat across the table lies in two of them.** The room round the edge of a
table is deeper than it is wide, so `linesOf` reads a station off the spreads the layout already states: the
holdings the table reads of that seat lie side by side under its name, and the single places it seals a card in lie
beneath them. The panel a player plays from and the shared middle each have the width of the page to lie along, so
they lie in one line. The sheet is handed the widest line and how many there are, which is what shares the group's
height out among them, one line of lettering to a line of cards. So a station is drawn half as wide, reads in two
glances, and draws its cards to the room its corner of the table has rather than to the width one line of them
would want. The three placements carry three names of their own — the shared middle, the seat's own panel, another
seat's station — and the box a seat is drawn in carries a fourth, so a rule of the sheet reaches one of the two and
a station is sized as a station rather than as a group of zones.

**A move onto a player lands on that player's cards.** A `Commit.SEAT` gesture arms the station of the seat the
move names, so a pass reads as picking a card up and laying it on the cards of the player it goes to — by clicking
there, or by carrying the card there. The plaque keeps the same landing for a seat the table draws nowhere, which
leaves the move reachable in the one place left to point at.

**A heap reads by its top card, and opens for as long as an arrival takes to read.** `play/arrivals.ts` counts
what one commit laid in each zone — the cards lying at the positions it grew by, which leaves a zone that gave
cards up, traded one for another or had them shuffled reading as receiving none. A heap draws those cards
beside the one they came to rest on, each arriving from the direction of the holding it was played out of, and
a moment later closes back to the card on top and the count of those beneath. So showdown's settlement turns
one card per seat over as the group it is and passing's exchange shows the card given up before the stack takes
it, out of one rule and no game's name. The newest commit is the one that shows, since that is the arrival a
player is watching, and a reader who asks for stillness is given the same table arrived at in one step.

**A round closes where the players can read it, and the reading is taken off the stream rather than off the
table.** A boundary is two transactions and a settlement commits both in one burst (§6), so the round scored and
the round dealt reach a client together and a render may only ever draw the last of them. `play/interludes.ts`
therefore reads each commit as it arrives: a commit whose phase the layout keyed as an `Interlude` is applied and
raises a report holding that cursor, and every commit behind it waits until the report is dismissed — at which
point they land in order, stopping again at the next boundary among them. So the last round of a match is read as
a round closed and then as a match decided, one press apiece, and the cards a round was won on are still lying
where it was won while its report stands over them. `table/Curtain.tsx` is that report: the standing seat by seat,
the figures the game keeps of the table beneath, the seat a decided match belongs to read off the end of the
standing `Layout.award` points to, and one press onward — dismissed by the button, by `Escape` or by a click away
from it, which are the three presses that put a selection down. Readiness is each player's own and no message to
the table: a turn waits at the seat it belongs to whether that player has read the round or not, so nobody can
hold the table up by looking away. What the line under the cards says once a match is played out is the same
reading, which leaves a decided table naming its winner rather than waiting for a move that will never come.

---

## 11. A round, end to end

A three-seat game where each seat commits one card face down and the round resolves when the last of them
has committed. It is the smallest shape that exercises every mechanism above: a simultaneous phase, a
sealed commitment, a refusal, a take-back and a settlement.

The layout: `hand:p` and `tray:p` per seat, both `HAND` and owned by `p`; a `draw` pile and a `discard`,
both `PILE`. `zones` returns them populated, with the undealt deck already in `draw`.

**The deal is transaction 0.**

```python
Transaction(
    seq=0,
    move=None,
    effects=(
        Reorder(
            zone="draw", order=(7, 2, 11, 0, ...)
        ),  # RNG consulted once, result recorded
        MoveCards(source="draw", indices={0, 1, 2}, target="hand:0", face_down=True),
        MoveCards(source="draw", indices={0, 1, 2}, target="hand:1", face_down=True),
        MoveCards(source="draw", indices={0, 1, 2}, target="hand:2", face_down=True),
        # ---- above: _deal_cards.  below: advance(dealt position, None, rng) ----
        SetState(state=GameState(phase="play", to_act=frozenset({0, 1, 2}))),
    ),
)
```

Each deal says `{0, 1, 2}` because removing cards re-indexes what remains — the same re-indexing that
makes `base_seq` necessary. `to_act` holding all three seats *is* the declaration that this phase is
simultaneous: no flag, no phase-type enum. The two halves arrive in one transaction, so no observer reads
a table where the cards are dealt and nobody is to act.

**A seat seals a card.** Player 1 acts; the rules route their card into their own tray.

```python
Transaction(
    seq=1,
    move=Move(player=1, action=Play(group="tray:1", indices={0})),
    effects=(
        MoveCards(source="hand:1", indices={0}, target="tray:1", face_down=True),
        SetState(state=GameState(phase="play", to_act=frozenset({0, 2}))),
    ),
)
```

One `project_transaction` call per observer:

| Observer | Receives |
|---|---|
| **Player 1** | the card that left `hand:1` and the same card now in `tray:1`, plus their own action echoed back |
| **Player 0** | `hand:1` down to two placeholders, `tray:1` holding one placeholder, `to_act` now `{0, 2}` |
| **Player 2** | the same as player 0 |
| **Spectator** | the same again — `HAND` grants `Audience.OWNER` on face-down cards, and a spectator owns nothing |

Player 1's own view shows their tray as a real card; every other view shows one placeholder, so an index
means the same thing on both sides (§7). Player 0 reads that the hand is one shorter and not which card
left, because the action reaches the acting seat alone.

**Refusals change nothing.** A move naming two cards where the rules take one stops at step 7: no effect
was constructed, the engine holds the position it held before the request arrived, and the adapter answers
`422`. A move built against `seq=1` and submitted after another seat has acted stops at step 5 with `409`,
and the client refetches its view and resubmits against the head. Were it applied, it would have succeeded
against contents that had shifted — sealing the wrong card, quietly.

**A take-back inside the window.** Players 0 and 2 seal at `seq=2` and `seq=3`, `to_act` empties, and the
rules owe the reveal. The adapter restarts the grace window instead of asking for it, and inside that
window player 1 changes their mind:

```python
Transaction(
    seq=4,
    move=Move(player=1, action=Take(group="tray:1", indices={0})),
    effects=(
        MoveCards(source="tray:1", indices={0}, target="hand:1", face_down=True),
        SetState(state=GameState(phase="play", to_act=frozenset({1}))),
    ),
)
```

`authorize` admits it although `to_act` was empty, because this game widens `authorize` to let a
retraction through; `validate` admits it because `phase` is still `"play"`. The card is back in the hand,
the tray is empty, and player 1 owes an action again. Opponents read `tray:1` losing a placeholder and
`hand:1` gaining one — a count moving between two zones, which is all they were ever told. The window
restarts, since a command has landed.

**Settlement resolves the round.** Player 1 seals a different card at `seq=5`, `to_act` empties again, and
this time a window passes over a closed round:

```python
Transaction(
    seq=6,
    move=None,
    effects=(
        MoveCards(source="tray:0", indices={0}, target="discard", face_down=False),
        MoveCards(source="tray:1", indices={0}, target="discard", face_down=False),
        MoveCards(source="tray:2", indices={0}, target="discard", face_down=False),
        SetState(state=GameState(phase="score", to_act=frozenset(), points=(1, 0, 2))),
    ),
)
```

`move=None` says no seat asked for this. The reveal is *just* laying cards face up: `PILE` grants
`Audience.ALL` on face-up cards, so every player's next projection contains every card that was sealed.
Nothing about secrecy was special-cased; it followed from the table in §3.3.

A retraction arriving now is refused — `validate` reads `phase == "score"` and raises `IllegalMove`, which
the adapter answers `422`. That is the whole of "too late", and it is a rules predicate rather than a
clock.

**Reconnect and hindsight** close the loop. A client that dropped at `seq=5` and returns at `seq=9`
fetches its view for the board and opens a stream with `Last-Event-ID: 5` to animate what it missed; both
come from the same projection function, so they agree. And afterwards, `replay(upto=n)` plus
`project_position(..., observer=1)` answers what player 1 knew at move *n* — a tray reading `(None,)`
before the round resolved and a real card after — which is what makes post-game analysis honest: whether a
play was good **given what the player knew**.

---

## 12. Boundaries

| Boundary | Enforced by | Violated when |
|---|---|---|
| Rules vs. mechanism | `boards` sits below `effects`; `Board` has no game methods | a `Board` method cannot be written without knowing which game it is |
| Reading a table vs. changing one | `Board` and `Position` answer; the four effects write, and neither reader raises a refusal | a game reaches into `board.zones` or a zone's own cards for an answer, or a reader words a rule |
| A seat's zone vs. its name | `Family.of(seat)` states the name; `Zone.owner` carries the seat | a game writes `f"hand:{seat}"`, or a seat is parsed back out of a zone id |
| Domain vs. transport | the `Rules are transport-free` contract; the `Table` protocol lives in `cardserver` | `cardserver`, `fastapi` or `asyncio` appears under `cardwork/` or `cardgames/` |
| Truth vs. knowledge | `project_position` and `project_transaction` are the only paths from a position to the wire | a handler serializes a `Position`, a `Board`, or a `Transaction` |
| Truth vs. knowledge, in a game's own state | `GameState.project` narrows the cursor by the game's own rule | a game declares a private field and leaves `project` inherited |
| Identity vs. seats | the adapter maps a credential to a seat and binds it to `move.player` | a handler passes a client's `move.player` through unchecked |
| Determinism vs. randomness | `rng` is a parameter of `_deal_cards`, `expand` and `advance` only | an `Effect.apply` consults an RNG or a clock |
| Data vs. code | `kind`-discriminated unions on effects and actions | a wire-facing field is typed as an abstract base and loses every subclass field |
| A word on the wire vs. the rule it names | `Pattern.kind` claimed by writing the class; `AnyPattern` reads a word back to it | a pattern travels as the parts it is made of and no rule can be read back, so a ranking may not sit in a cursor |
| Validation vs. assignment | `with_changes` and `revalidate_instances`; effects construct rather than `model_copy` | a `model_copy(update=...)` writes a value nothing has checked |
| Physical vs. derived | `_deal_cards` moves cards; `advance` decides turns and phases | opening state is computed in a constructor and never reaches the journal |
| One seat's move vs. the round's resolution | `submit` runs `advance` once; `settle` runs it to rest with `move=None` | a seat's event carries the scoring of everyone else's round |
| History vs. working state | one commit method mutates; `history[n] == journal.replay(n)` | the snapshot memo and the journal move separately |
| Published vs. provisional | `undo` requires a head above the mark, which the adapter advances as it commits | a client is told to forget a transaction it has already read |
| Timeless rules vs. real latency | the grace period lives in the adapter; "too late" is a `validate` predicate | a rules hook reads a clock, or the window decides legality |
| Engine vs. rules | rules take `position`; only engine methods read `self` | a rules method reads the cursor and search silently evaluates the wrong board |
| Adapter layers | the `Adapter layers` contract over `cardserver` | `sessions` imports `registry`, or `protocol` imports anything above it |
| Framework vs. games | the `The framework knows no game` contract; `cardgames` is a distribution of its own | a mechanism under `cardwork/` names a game, or a handler branches on which game it serves |
| What a game states vs. how it looks | `presentation` holds zone ids, kinds of move and fields of the cursor | a layout carries a measurement, or an interface branches on a zone id or a phase |
| A game's rules vs. its layout | the `Rules know no presentation` contract; `backend` and `frontend` per game | a rules module names a slot or a caption, or a zone id is written twice |
| A rule over cards vs. the table it is played on | the `Rules read cards rather than tables` contract | a `rules` module names a zone, an effect or a cursor, so a card rule can be read only against a dealt table |
| A mechanism vs. the choice of game | the `Nothing names the host` contract; `cardtable.catalogue` is the only module naming `cardgames` | a registry, a handler or a scene is reached for by a game's name outside the catalogue |
| A shape stated once vs. a shape restated | the layout vocabulary is generated from the published document; only the projections carrying a game's own state are written by hand | a field of a slot, a gesture or a move is typed in TypeScript by hand |
| A credential vs. an address | the table, the code and the token ride in the fragment; the token reaches the endpoints in a header | a seat token or a join code appears in a path, a query string or a log line |
| A room vs. a table | `gathering.py` holds the company and reaches the registry through `Opening`; the six playing endpoints are unchanged | a gathering opens a game itself, or a table endpoint reads the company |
| Who someone is vs. what they may do | a token minted at arrival holds a seat through `SeatPolicy`; a say over the choice stands behind `SayPolicy` | a name authorises anything, or a handler decides who may deal |
| One table in service vs. the state its game declares | `InService` erases the cursor at the storage boundary; `registry.open` stays generic per call | the registry names a state type, so one process serves one rule set |
| What a host offers vs. what the rules admit | an `Offering` is built from `Game.capacity`, `Scene.title` and the deck counts `_validate_initial_deck` accepts, and every one of them is dealt in a test | a company settles a table the rules refuse, and meets it at the deal |
| Where a run listens vs. where it is reached | `reaching.py` answers the second; `Service.advertise` states it outright | an announcement prints the bind address, so a wildcard is handed out as an address to open |
| Cards in hand vs. a move sent | a selection resolves through the gestures; a press at an armed place or on the words of an armed move is what submits | a card click sends a move, or a selection is read as a command |
| What the table offers vs. what the page knows | `selection.ts` reads `view.legal` through `layout.gestures` and nothing else | the page counts cards, reads a rank, or names a zone to decide what may be picked |
| A position vs. what has just happened to it | a view is the cards as they lie; `arrivals.ts` reads a commit for what it laid down | a heap is animated from a difference between two views, or a zone is drawn from a move's intent |
| A value a person turns vs. one the code settles | `config.yaml` states a run; `Configuration` asks for each field outright | a default sits in a flag, a Makefile and a file at once, and a run reads whichever was edited last |
| A round vs. a match | `rounds` sits above `games`; a game states one round and the layer states the match | a game deals its own next round, or adds its own tally into the standing |

---

## 13. Invariants under test

Most of the suite is ordinary unit coverage. Ten properties are the ones worth naming, because each
stands in for a class of bug rather than a case:

| Property | Guards |
|---|---|
| A projection survives any **substitution** of what it conceals (§7) | every information leak, including the ones nobody thought to look for |
| An event view names exactly the zones its observer reads differently, and the action reaches no other seat | a delta that discloses more than a pair of views would |
| A view and an event offer their observer its own moves and no others | a simultaneous phase disclosing the shape of another seat's holding through the options it opens |
| `history[n] == journal.replay(n)` for every `n`, after a random legal sequence | the memo and the record drifting apart, which would make `base_seq` name a position that never existed |
| A `Transaction` survives a JSON round-trip with every effect field intact | the discriminated unions degrading to their abstract bases |
| A pattern, a compound of patterns, a `Combination`, a `Ranking` and a game's own pattern nested in a built-in one each survive a JSON round-trip to an equal value | a rule that cannot be read back, which would keep a ranking or a combination out of a cursor and off the wire |
| The places a `Ranking` offers over a generated hand are exactly the places it reads as a combination, under Hypothesis | a move list and the ranking it is drawn from drifting apart, so a pattern added to the rules is never offered |
| Card conservation over `starting_deck` on every dealt table | a zone layout that loses or duplicates a card |
| Every move a game offers an observer is made by exactly one gesture of the layout that observer is served, picking in a zone its projection holds and committing onto one it reads | a scene and the rules drifting apart, so a move the rules admit reaches a player as a card that arms nothing |
| A stream resumed from `Last-Event-ID` delivers exactly what a client missed | the resumption path, which a dropped stream and a tab coming back into view both travel |

The adapter's suite drives the real routes in-process — through an HTTP transport for the
request/response endpoints and through a direct-ASGI harness for the streams (§10, *Why FastAPI*) — and
covers the refusal table case by case, the idempotent retry, the take-back accepted inside the window, and
the same take-back refused after the round has settled. An arrangement is held to the pair of facts that
make it the commit it is: the other seats read the same run of placeholders they read before, and the
window stands where the last move left it.

Each game in `cardgames` carries a suite of its own, which plays full matches in-process and holds every
position they pass through to card conservation and to `history[n] == journal.replay(n)`. Each is also put
into service through `create_app` and played over the endpoints: a game's own state fields reach a client's
view, its own refusals arrive as the statuses of §6, and a blind holding stays unread by the seat that owns
it over the wire as it does on the table.

The host is held to the same standard from the other end, over each of the four games it opens. A table
opened through `cardtable.catalogue` is served the layout the game's own module states, a token speaks for the
seat it was issued for and for no other, and a move read out of a seat's own `legal` lands through the
endpoints — so the wiring of rules, scene and transport is a test rather than a first run in a browser.
