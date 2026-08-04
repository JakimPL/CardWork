# Presentation

`cardwork.presentation` states how a game is laid out for one player: which zones show, where they sit, how
their cards lie against each other, which move a click sends, and what each player's plaque reads. A layout is
data. A game states one, an interface reads it, and the two meet over a vocabulary that names neither a
particular game nor a particular screen.

The layer sits at the head of the framework, and the framework itself is a stranger to it: the engine plays a
game whether or not anybody is watching. It names three layers below — `zones` for a zone to lay out, `moves`
for a kind of move to make, `states` for a field of the cursor to show — and stops there.

```python
Scene(
    title="Passing",
    shared=(...),       # the zones every observer reads alike
    held=slots_of,      # seat -> the zones it holds of its own
    gestures=...,       # seat -> the moves it makes, and how
    counts=...,         # seat -> the zones of its own the table counts
    readouts=(...),     # the fields of the cursor worth showing
    phases={...},       # what each phase is called in words
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

| piece | states |
|---|---|
| `Slot` | one zone laid out: the seat it belongs to, the place it takes among that owner's zones, how its cards lie, what it is called, whether its size shows |
| `Gesture` | one kind of move as a player makes it: the zone its cards are picked in, and the place clicked to send it |
| `Plaque` | one player: the seat, the name it plays under, and the zones of theirs the table counts |
| `Tally` | one of those counts, under the word the game calls that zone by |
| `Readout` | one field of the cursor shown, under a word, speaking about the table or about each seat |
| `Layout` | the whole of it for one observer, checked against itself as it is built |
| `Scene` | the whole of it for a table: what every observer reads alike, and what each seat holds |

**A slot names its owner rather than a place on the page.** `Slot.seat` is a seat of the table, or None for a
zone the seats share and every one of them reads the same way. Where an owner's zones sit on the page follows
from that and belongs to the interface: the seat reading the layout holds the panel it plays from, each of the
others a station round the table, and the shared zones the middle of it. So a game states whose cards are whose
and the page states what that looks like, which is the same division the spreads draw.

Three closed vocabularies carry the choices:

| vocabulary | members | decides |
|---|---|---|
| `Spread` | `SLOT`, `STACK`, `FAN`, `ROW` | how the cards of a zone lie: one place, a heap, overlapped, side by side |
| `Commit` | `ZONE`, `SEAT` | whether a move is sent by clicking a zone or a player |
| `Scope` | `TABLE`, `SEAT` | whether a field of the cursor holds one value or one per seat |

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
for a holding kept off the table altogether.

**`presets` names the three arrangements every game reaches for**, as `zones.presets` names the visibility
policies: `presets.hand(zone, label, seat=..., place=...)` is a holding as the seat holding it reads it,
overlapped and showing its cards; `presets.holding(zone, label, seat=..., place=...)` is the same zone as the
rest of the table reads it, lying the same way and carrying its size; and `presets.heap(zone, label, place=...)`
is a stack the seats share, read by its top card and its size. Each fixes a `counted` a game would otherwise
decide twice. Anything else is spelled out as a `Slot`, and becomes a preset when a second game wants the same
arrangement.

---

## 3. A layout is built for one seat, from a scene built for the table

`observer` is a seat or a spectator, and every zone id in a layout is concrete for that observer:
`picked="hand:1"` rather than a stand-in resolved on arrival. So the interface looks nothing up, and the
layout falls in step with the projection (`architecture.md` §7), which is also per observer, and with the
moves a view carries, which are that seat's own.

A game states one `Scene` all the same, because a table has one arrangement and its observers differ only in
where they sit. A scene holds the zones every observer reads alike, and four functions of a seat — the zones it
holds as it reads them, the same zones as the rest of the table reads them, the gestures it makes, the counts the
table reads of it:

```python
PASSING_SCENE.layout(players=3, observer=1)     # -> Layout(observer=1, ...)
PASSING_SCENE.layout(players=3, observer=None)  # -> every seat as the table reads it, and no gesture
```

What `Scene.layout` states so that no game states it again: a seat reads the zones it holds, the seats around it
as the table reads them and the shared ones besides, and is offered the gestures of its own turn; a spectator
reads every seat as the table reads it and makes no move; every seat of the table takes a plaque, named by where
it sits until a host holds a name for it. That is the same entitlement the projection gives an observer over the
cards, and it now lives in one place rather than in every game that would have to remember it.

A scene answers for the ownership it states as it lays a table out: a zone the table shares belongs to no seat,
and the zones a scene is asked for at one seat all belong to that seat. So a game that reads `hand_of(seat)`
under the wrong seat fails at the layout rather than drawing one player's cards in front of another.

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
| every zone a gesture picks from or commits onto takes a slot | a player can reach the cards and the target |
| one readout per field | a figure shows once |

---

## 5. How a move meets its gesture

An interface holds the moves the view served it (`architecture.md` §7) and matches each one:

```
a move is made by the gesture whose kind is its kind, and whose group is its group or is stated for every group
```

`Gesture.matches(action)` is that rule, and `moves.group_of(action)` is the group read off an intent — a play,
an exchange and a discard name one, and the three intents beside them carry a word of their own or none. A
layout admits no second answer, so an interface calling it reads one gesture or a bug in the game that stated
the layout.

The gesture then says the rest: `picked` is the zone whose cards the player selects, the move's own `indices`
are which of them, and `commit` with `target` is where the click that sends it lands — a zone the gesture
names, or the seat the move names in `Give.target_player`. `caption` states in words what the gesture does.

That is the whole of the contract. Which cards light up as a selection grows, when a heap collapses to its top
card, how a highlight looks and how large a card is drawn: all of it is the interface's, and none of it is a
game's to state.

---

## 6. What arrives the day it is wanted

Three places where the vocabulary stops at what the games ask for, each following the line `Visibility` takes
(`architecture.md` §3.3):

- **`Commit` names places on the table.** A move is sent by pointing at where it goes, which is what keeps a
  button standing apart from the game out of the interface. A game whose move carries a decision no place on
  the table stands for — a bid, a trump chosen, a contract announced — gains a member here the day it is
  written, and `Declare` is the intent waiting for it (`architecture.md` §5.3).
- **`Spread.STACK` reads by the last card**, since that is the end a game lays on. A heap dealt from its other
  end holds cards nobody reads, and a heap of backs reads alike from either end, so the field naming which end
  faces up arrives with the first game that deals readable cards from position zero. A game whose players draw
  off a heap states the end they draw from instead, which is what `cardgames.backend.shedding` does
  (`docs/games/shedding.md` §2).
- **A slot names an owner and no place**, because a game states which zones a player owns and the interface
  states where the page puts them: the three placements it derives — the panel below, a station round the table,
  the shared middle — are one reading of `Slot.seat` against `Layout.observer`, and a page that wanted a fourth
  would derive that too. A field naming the page's own geography arrives the day a game needs a zone drawn
  somewhere the owner of it cannot say.

---

## 7. The three worked examples

`cardgames.frontend.passing`, `cardgames.frontend.showdown` and `cardgames.frontend.shedding` state a `Scene`
apiece — constants for what the table shares and four functions of a seat for what it holds — and each lays out
every observer from it, with every zone id concrete. Between them they exercise both addressings §1 sets out,
and §5 of each game's own document reads its scene out zone by zone.

The third of them commits onto a zone the observer owns: its draw picks a card on the shared table and sends it
onto the seat's own hand, which is the pairing read in the direction the two before it never took. The
vocabulary needed nothing for it, since a gesture names the zone its indices address and the place a player
points at, and whose zone either one is was never part of what it states.

They are held to their own rules by test: every move a game's `legal_moves` offers a seat is matched against
the layout that seat is served, and the gesture it resolves to has to pick in a zone the projection holds and
commit onto one the observer reads. So a layout naming a zone the rules dropped, or missing a gesture for a
move the rules admit, fails as a broken game rather than as a blank on a screen.
