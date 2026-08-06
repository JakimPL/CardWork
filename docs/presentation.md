# Presentation

`cardwork.presentation` states how a game is laid out for one player: which zones show, where they sit, how
their cards lie against each other, which move a click sends, and what each player's plaque reads. All of it
is data. A game states one `Scene`, the layer draws one observer's `Layout` out of it, an interface reads
that, and the three meet over a vocabulary that names neither a particular game nor a particular screen.

The layer sits at the head of the framework, and the framework itself is a stranger to it: the engine plays a
game whether or not anybody is watching. It names four layers below — `zones` for a zone to lay out, `moves`
for a kind of move to make, `states` for a field of the cursor to show and the end a standing is won at,
`rounds` for the two phases a match of them pauses at — and stops there.

```python
Scene(
    title="Passing",
    table=(...),        # the zones of the table, which every observer reads alike
    seated=(...),       # the zone families the seats hold, each stated once for all of them
    gestures=(...),     # the moves a seat makes, and how each one is sent
    readouts=(...),     # the fields of the cursor worth showing
    phases={...},       # what each phase is called in words
    interludes={...},   # which of those phases play pauses at
    award=Award.HIGHEST,  # which end of the standing the match is won at
).layout(players=3, observer=1)
```

---

## 1. The part a game has to say

Two zones and a set of positions make a move, and which is which differs by game:

```python
Take(group="pile", indices={2})     # passing: position 2 of the seat's own hand, exchanged with the pile
Play(group="hand", indices={2})     # showdown: position 2 of the named hand, sealed into the seat's tray
```

In the first the indices address a zone the action never names, and the zone it does name is the other side of
the exchange. In the second the indices address the named zone, and the zone the cards land in appears nowhere.
A rule over `Action` alone tells the two apart in no way at all, which is why a game states the pairing itself:

| a game states | so an interface knows |
|---|---|
| the zone a move's indices address | which cards a player selects to build that move |
| the place the move commits onto | where to click to send it |

That pairing is a `Gesture`, and it is the whole reason this layer exists. Everything else in a layout is the
same question asked of zones and seats rather than of moves.

---

## 2. What a layout holds

A layout is what one observer is served, so every piece of it is settled for that observer: a concrete zone
id, a bound seat, a gesture that seat may make. What a game writes is the scene behind it, which §3 states.

| piece | states |
|---|---|
| `Slot` | one zone laid out: the seat it belongs to, the place it takes among that owner's zones, how its cards lie, what it is called, whether its size shows |
| `Gesture` | one kind of move as a player makes it: the zone its cards are picked in, and how it is sent |
| `Plaque` | one player: the seat, the name it plays under, and the zones of theirs the table counts |
| `Tally` | one of those counts, under the word the game calls that zone by |
| `Readout` | one field of the cursor shown, under a word, speaking about the table or about each seat |
| `Layout` | the whole of it for one observer, checked against itself as it is built |

**A slot names its owner rather than a place on the page.** `Slot.seat` is a seat of the table, or None for a
zone the seats share and every one of them reads the same way. Where an owner's zones sit on the page follows
from that and belongs to the interface: the seat reading the layout holds the panel it plays from, each of the
others a station round the table, and the shared zones the middle of it. So a game states whose cards are whose
and the page states what that looks like, which is the same division the spreads draw.

Five closed vocabularies carry the choices:

| vocabulary | members | decides |
|---|---|---|
| `Spread` | `SLOT`, `STACK`, `FAN`, `ROW` | how the cards of a zone lie: one place, a heap, overlapped, side by side |
| `Commit` | `ZONE`, `SEAT`, `WORD` | whether a move is sent by clicking a zone, clicking a player, or saying it |
| `Scope` | `TABLE`, `SEAT` | whether a field of the cursor holds one value or one per seat |
| `Interlude` | `ROUND`, `MATCH` | what a phase play pauses at has come to |
| `Award` | `HIGHEST`, `LOWEST` | which end of the standing a match is won at — `cardwork.states`, read here |

**A spread says how the cards of a zone lie, and a page reads where they lie off the same word.** `SLOT` is one
place holding a card or standing empty, which is what a game states for a card sealed or a card turned. A single
place is also the narrowest thing a zone can be, and the room round the edge of a table is deeper than it is wide, so
a seat drawn across the table takes that word a second way: the holdings the table reads of it lie side by side under
its name, and its single places lie beneath them, which is the two lines a station stands in (`architecture.md`
§10). So the word a game says about how cards lie against each other carries what a page needs in order to work out
where they go, and the geography stays the interface's own.

**A boundary is a phase, and a game says which of its phases are ones to stop at.** A round scored, the cards
gathered and the next hand dealt settle in a single burst, so a player watching the table alone reads one round
becoming another with nothing said about what the first was worth. `Layout.interludes` keys those phases against
the `Interlude` each has come to, which is the whole of what an interface needs to hold the table open and read it
out; the figures it reads out are the layout's own readouts, and the words are the interface's. A phase keyed
there is captioned like any other, since it is a phase a player reads in the ordinary way as well.

**A standing has an end a match is won at, and `points` alone does not say which.** Whether the seat holding the
most of it or the fewest holds the match is a rule of the game, so `Layout.award` states which end and an
interface names the seat by reading the standing there — a page saying who won holds no rule of its own about what
winning is. `Award` is the one vocabulary here that this layer reads rather than declares: `cardwork.states` holds
it beside the `points` tuple it is about, because the rules settle a match on a lead by the same reading
(`docs/rounds.md` §1). Each game states it once and its scene points at that, so the seat the rules end a match
for and the seat the page names are the same seat by construction.

**A readout is how a number reaches the screen, and the only how.** The standing is
`Readout.of(PassingState, "points", "Points", scope=Scope.SEAT)`; the round in play is the same call over
`round_number` at table scope. So an interface reads every figure it shows through one shape, and the name of a
field a particular game declares lives in that game. `Readout.of` reads the name against the state class as it
builds, so a field renamed refuses the layout rather than leaving a blank on the screen. The state class is a
second thing to read against, and it belongs to the game rather than to the layout a client receives, so it
arrives as an argument to the constructor and stays off the model: a `Readout` on the wire is three strings.

**A zone is read twice: once by the seat holding it, and once by everybody else.** The cards in an opponent's
hand are theirs to read and the size of it is the table's to know, so the same zone takes a `Slot` showing every
card of it at the seat it belongs to, and a `Slot` of backs carrying its size at every other seat. A `Tally` on
the plaque is how a zone the table draws nowhere still says how much of it there is, which is what a game states
for a holding kept off the table altogether. The three readings are one statement where a game writes them: a
`Setting` holds all of them for a zone family at once (§3).

---

## 3. What a game states

`observer` is a seat or a spectator, and every zone id in a layout is concrete for that observer:
`picked="hand:1"` rather than a stand-in resolved on arrival. So the interface looks nothing up, and the
layout falls in step with the projection (`architecture.md` §7), which is also per observer, and with the
moves a view carries, which are that seat's own.

A game states one `Scene` all the same, because a table has one arrangement and its observers differ only in
where they sit:

```python
PASSING_SCENE.layout(players=3, observer=1)     # -> Layout(observer=1, ...)
PASSING_SCENE.layout(players=3, observer=None)  # -> every seat as the table reads it, and no gesture
```

Five pieces state that arrangement, and every one of them is data. A game writes values and the layer binds the
seat:

| piece | states |
|---|---|
| `Lay` | one zone from one side of the table: the word it is called by, how its cards lie, whether its count shows |
| `Fixture` | a zone of the table, under the one lay every observer reads it through |
| `Setting` | one zone family: how its owner reads it, how the rest of the table reads it, what its count is called |
| `Making` | one kind of move as any seat makes it: where its cards are picked up, and how it is sent |
| `Scene` | the whole of it for a table, checked against itself as the module stating it loads |

**A zone laid out is stated once and read as many times as it has readers.** `Family` is how the layers below
address the zone one name gives every seat, and a `Setting` is that family laid out: `held` is the lay its owner
reads, `seen` the lay the rest of the table reads, `tally` the word its count carries on a plaque. Showdown's
blind is the one arrangement in these games that wants all three of them different:

```python
Setting(
    family=BLINDS,
    held=Lay(label="Your blind", spread=Spread.ROW, counted=False),
    seen=Lay(label="Blind", spread=Spread.STACK, counted=True),
    tally="Blind",
)
```

A setting states at least one of the three, since a family reaches a player laid out or counted: with no `seen`
it is a family the table draws nowhere, with no `held` one its owner reads as everybody else does, and with a
tally alone a holding kept off the table and counted on the plaques. A zone of the table takes one lay instead,
as a `Fixture`, since a zone belonging to nobody says the same thing to everybody.

**A move names a family as well, so a gesture states no seat either.** An `Address` is a `Family` or a zone of
the table; `at(address, seat)` is the zone it names there, and `word_of(address)` the word a client names the
group by — a family under its own name, a zone of the table under its id, which are the two words the rules
read a group back against. So one `Making` is stated and every seat is offered the `Gesture` built from it:

```python
Making(
    kind=ActionKind.DISCARD,
    group=HANDS,
    picked=HANDS,
    commit=Commit.ZONE,
    target=DISCARD,
    caption="Shed these cards as one rank",
)
```

**A place is where a zone is stated.** `Slot.place` orders the zones of one owner and says nothing else, so it
is the index of the declaration in its tuple, counted within `table` and within `seated`. A game that wants a
hand drawn before a blind moves the line; a family the table draws nowhere leaves a gap in the run every other
seat stands in, which sorts the same.

**A count is what the arrangement says, and the arrangements come built.** `counted` stays a field a lay
states, since a pile whose depth is nobody's business is a real thing for a game to want. What keeps a game
from deciding it twice is that the three arrangements every game reaches for arrive whole, each a classmethod
of the piece it builds:

| builder | is |
|---|---|
| `Setting.hand(family, label, mine=..., tally=...)` | a holding its owner picks from, fanned and read by its cards at that seat, fanned under its size at every other, counted on the plaques |
| `Setting.sealed(family, label)` | a single place a card is committed into, which reads alike from every side of the table |
| `Fixture.heap(zone, label)` | a stack the seats share, read by the card on top of it and by how many lie beneath |

A game spells a `Lay` out where the arrangement is its own — showdown's blind, climbing's stack — and a second
game wanting the same one turns it into a builder beside these, which is the rule `zones.presets` follows for
the visibility policies.

**`presets` states what every match played in rounds restates.** `match_interludes()` keys the two `MatchPhase`
pauses against what each has come to, `match_phases()` captions them, and `match_readouts(state)` is the three
figures every such game shows — the standing, what the round in play has scored, and which round that is — read
against the cursor the game actually carries. So a game states the words that are its own and inherits the rest.

What `Scene.layout` states so that no game states it again: a seat reads the zones it holds, the seats around it
as the table reads them and the shared ones besides, and is offered the gestures of its own turn; a spectator
reads every seat as the table reads it and makes no move; every seat of the table takes a plaque, named by where
it sits until a host holds a name for it. That is the same entitlement the projection gives an observer over the
cards, and it lives in one place rather than in every game that would have to remember it.

The title, the readouts, the captions, the interludes and the award travel to every observer unchanged: what a
match comes to and where play pauses on the way are one table's business, so every seat and every spectator reads
them alike.

**A scene answers for itself as the module stating it loads.** Three of the claims a layout is held to a scene
makes unconstructible, and the rest it checks as each piece is built:

| refusal | met |
|---|---|
| a zone laid out for one seat belongs to another | unconstructible — the layer builds the slot from the family and the seat |
| a zone the table shares names a seat | unconstructible — a `Fixture` has no owner |
| two zones of one owner take one place | unconstructible — the place is the declaration's index |
| a setting reaching a player in no way at all | as the `Setting` is built |
| a commit and a target saying different things about where a move lands | as the `Making` is built |
| two gestures answering one move | as the `Scene` is built |
| a gesture naming a zone the scene lays out nowhere | as the `Scene` is built |
| a field of the cursor read twice | as the `Scene` is built |
| a phase play pauses at left uncaptioned | as the `Scene` is built |

`Layout` holds the last four of its own besides, because it stands alone whoever built it: the port below
admits any implementation, so a layout leans on no scene having built it. Stating them on the scene as well is
what lets a game read a refusal where it wrote the mistake, and the words are the same either way.

**A scene is a port the adapter asks for by shape.** A table is put into service with the arrangement it is
read through beside the game itself, and `GET /tables/{id}/layout` answers the layout of the seat behind the
credential — the same seat its view is projected for (`architecture.md` §10). It is the one answer whose type
is not generic in a game's state, so it is the one an interface can generate its types from. A layout stands
for the whole match rather than for a position, so a client asks once as it joins and holds it while the cards
move underneath.

---

## 4. A layout answers for itself

Every claim a layout makes is checked as it is built, which leaves an interface free to trust it:

| checked | so an interface may assume |
|---|---|
| the observer is one of the seats, or a spectator | a plaque exists for whoever is watching |
| one slot per zone | a card lies in one place on the screen |
| every slot belongs to a seat of the table, or to the table | a slot has somewhere on the page to be drawn |
| one slot per place among one owner's slots | the zones of one owner fall in a settled order |
| one plaque per seat | the standing reads across the table in one row |
| one gesture per kind and group | a move resolves to a single gesture |
| a gesture over every group of a kind stands alone | that resolution is unambiguous |
| every zone a gesture names takes a slot | a player can reach the cards and the target |
| one readout per field | a figure shows once |
| every phase play pauses at is captioned | a report has a phase to name and words to name it by |

The last five rows are the ones a scene holds as well, so a game stating one meets them as its module loads
(§3). The rows above them are claims a scene makes by construction, and a layout built by hand is where they
earn their keep.

---

## 5. How a move meets its gesture

An interface holds the moves the view served it (`architecture.md` §7) and matches each one:

```
a move is made by the gesture whose kind is its kind, and whose group is its group or is stated for every group
```

`Gesture.matches(action)` is that rule, and `moves.group_of(action)` is the group read off an intent — a play,
an exchange and a discard name one, and the four intents beside them carry a seat, a claim or their word alone.
A layout admits no second answer, so an interface calling it reads one gesture or a bug in the game that stated
the layout.

The gesture then says the rest: `picked` is the zone whose cards the player selects, the move's own `indices`
are which of them, and `commit` with `target` is how the move leaves — onto a zone the gesture names, onto the
seat the move names in `Give.target_player`, or said by its word alone. `caption` states in words what the
gesture does.

**An intent naming no card is made in no zone and lands on none.** A pass names its turn and nothing else, so
`picked` reads None and there is no zone to hold cards open in; `commit` reads `WORD`, so there is no place to
point at either. What an interface draws for one is a place to press, captioned by the gesture, and what arms
it is the same rule that arms every other move: the cards in hand are exactly the cards the move names, which
for this one is none of them. So a pass stands ready the moment a turn arrives and stands down as soon as a
card is picked up, and the two states need no rule of their own. The caption of such a gesture is lettered on
the place a player presses rather than read as a title over one, so a game states it in words that carry at the
size of a card — climbing letters its own with the word that game is played by, which is *Pass*.

That is the whole of the contract. Which cards light up as a selection grows, when a heap collapses to its top
card, how a highlight looks and how large a card is drawn: all of it is the interface's, and none of it is a
game's to state.

---

## 6. What arrives the day it is wanted

Seven places where the vocabulary stops at what the games ask for, each following the line `Visibility` takes
(`architecture.md` §3.3), and one that grew the day a game wanted it:

- **`Commit` says how a move is sent, and two of its three answers are places.** A move naming cards is sent by
  pointing at where those cards go, which is what keeps a button standing apart from the game out of the
  interface. `WORD` is the third answer and the newest: `Pass` names no card and no destination, so pointing
  states nothing about it and a seat says it instead. That is the one member this vocabulary has grown, and it
  arrived the way the others will — with the intent that had no way to be made. `Declare` reaches the page by
  the same answer the day a game states one, since a bid is said rather than pointed at as well.
- **`Spread.STACK` reads by the last card**, since that is the end a game lays on. A heap dealt from its other
  end holds cards nobody reads, and a heap of backs reads alike from either end, so the field naming which end
  faces up arrives with the first game that deals readable cards from position zero. A game whose players draw
  off a heap states the end they draw from instead, which is what `cardgames.backend.shedding` does
  (`docs/games/shedding.md` §2).
- **A slot names an owner and no place**, because a game states which zones a player owns and the interface
  states where the page puts them: the three placements it derives — the panel below, a station round the table,
  the shared middle — are one reading of `Slot.seat` against `Layout.observer`, and a page that wanted a fourth
  would derive that too. The lines a station stands its cards in are derived the same way, off the `Spread` each
  slot already carries. A field naming the page's own geography arrives the day a game needs a zone drawn
  somewhere the owner of it cannot say.
- **An interlude names what a pause has come to and not what to say about it.** `ROUND` and `MATCH` are the two
  things a game played in rounds ever stops at, and a game stopping somewhere of its own — a trick taken, a hand
  revealed — keys that phase against one of the two rather than asking for a third: what the panel then reads out
  is the readouts already stated, so the pause needs no vocabulary of its own. A member arrives the day a pause
  wants reading out in a shape the two of these are not, and the words each one is titled by stay the interface's.
- **An award names an end of the standing and no rule about reaching it.** The two members are the whole of what a
  direction can be, and both are needed for either to say anything: a field with one value states nothing, and an
  interface reading `points` has no way to guess which way a particular game counts. So this is one place the
  vocabulary is complete on the day it arrives — and complete enough that it outgrew this layer: the rules ask the
  same question of the same standing to settle a match on a lead, so `Award` moved down to `cardwork.states` and
  the layout points at what the game already states. What still waits is a match won on something other than a
  standing — a contract made, a seat left holding every card — which the rules state as their own `match_over`
  before it is anything for a layout to point at.
- **A setting gives every seat the zones every other seat has.** A family stands one zone at each of them, which
  is what a game means by a hand, and a table where the dealer keeps a pile of its own is the shape that wants
  more. It arrives as a lay stated per seat, which is how `Family.visibility` already answers a question of
  exactly that kind (`architecture.md` §3.3), the day a game deals one seat something the others have no
  counterpart to.
- **A lay carries one word, and a gesture one caption.** What a zone is called is a fact about the zone, so it
  stands the same at every seat that holds one; a word about where play stands is a readout, and a word about a
  particular player is the interface's. A label that varied by seat would be a game reaching for both at once.
- **A tally belongs to a plaque, so a zone of the table carries none.** A plaque is one seat's, and a count of a
  shared zone put on one would print the same number across the table; the zone is laid out in the middle
  instead, where its lay says whether it counts. What arrives the day it is wanted is a figure about the table
  standing somewhere of its own, and a readout is already that.

---

## 7. The four worked examples

`cardgames.frontend.passing`, `cardgames.frontend.showdown`, `cardgames.frontend.shedding` and
`cardgames.frontend.climbing` state a `Scene` apiece — data throughout, with no function, no place ordinal and
no seat in any of them — and each lays out every observer from one statement, with every zone id concrete.
Between them they exercise both addressings §1 sets out and all three answers `Commit` gives, and §5 of each
game's own document reads its scene out zone by zone.

The third of them commits onto a zone the observer owns: its draw picks a card on the shared table and sends it
onto the seat's own hand, which is the pairing read in the direction the two before it never took. The
vocabulary needed nothing for it, since a gesture names the zone its indices address and the place a player
points at, and whose zone either one is was never part of what it states.

The fourth is the first to state a gesture sent by its word: a seat gives its turn up over the combination
standing on the table, and the caption is lettered on the place it presses (§5). It is also the game that
spells a lay out where a builder would have read wrong — the stack it plays onto is fanned rather than heaped,
since the combination a seat has to climb over is what a heap would put away, and uncounted, since the cards
lying there are the count (`docs/games/climbing.md` §5).

They are held to their own rules by test: every move a game's `legal_moves` offers a seat is matched against
the layout that seat is served, and the gesture it resolves to has to pick in a zone the projection holds and
commit onto one the observer reads. So a layout naming a zone the rules dropped, or missing a gesture for a
move the rules admit, fails as a broken game rather than as a blank on a screen.
