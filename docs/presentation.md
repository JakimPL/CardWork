# Presentation

`cardwork.presentation` states how a game is laid out for one player: which zones show, where they sit, how
their cards lie against each other, which move a click sends, and what each player's plaque reads. A layout is
data. A game states one, an interface reads it, and the two meet over a vocabulary that names neither a
particular game nor a particular screen.

The layer sits at the head of the framework, and the framework itself is a stranger to it: the engine plays a
game whether or not anybody is watching. It names three layers below — `zones` for a zone to lay out, `moves`
for a kind of move to make, `states` for a field of the cursor to show — and stops there.

```python
Layout(
    title="Passing",
    observer=1,
    players=3,
    slots=(...),        # the zones this seat sees, and where
    gestures=(...),     # the moves this seat makes, and how
    plaques=(...),      # every player, and the counts the table reads of them
    readouts=(...),     # the fields of the cursor worth showing
    phases={...},       # what each phase is called in words
)
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
| `Slot` | one zone laid out: the region it sits in, the place it takes there, how its cards lie, what it is called, whether its size shows |
| `Gesture` | one kind of move as a player makes it: the zone its cards are picked in, and the place clicked to send it |
| `Plaque` | one player: the seat, the name it plays under, and the zones of theirs the table counts |
| `Tally` | one of those counts, under the word the game calls that zone by |
| `Readout` | one field of the cursor shown, under a word, speaking about the table or about each seat |
| `Layout` | the whole of it for one observer, checked against itself as it is built |

Four closed vocabularies carry the choices:

| vocabulary | members | decides |
|---|---|---|
| `Region` | `TABLE`, `SEAT` | whether a zone belongs to the whole table or to the observer |
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

**A count is what another seat's zone says about itself.** The cards in an opponent's hand are theirs to read
and the size of it is the table's to know, so a zone belonging to another seat reaches the screen as a `Tally`
on their plaque, and a zone of the observer's own reaches it as a `Slot` holding cards.

---

## 3. A layout is built for one seat

`observer` is a seat or a spectator, and every zone id in the layout is concrete for that observer:
`picked="hand:1"` rather than a stand-in resolved on arrival. A game builds a layout per observer, so the
interface looks nothing up.

This falls in step with the projection (`architecture.md` §7), which is also per observer, and with the moves a
view carries, which are that seat's own. A spectator's layout states the slots and plaques of the shared table
and no gestures at all, which is exactly the seat's entitlement written in the same place its cards are.

---

## 4. A layout answers for itself

Every claim a layout makes is checked as it is built, which leaves an interface free to trust it:

| checked | so an interface may assume |
|---|---|
| the observer is one of the seats, or a spectator | a plaque exists for whoever is watching |
| one slot per zone | a card lies in one place on the screen |
| one slot per place in a region | the slots of a region fall in a settled order |
| one plaque per seat | the standing reads across the table in one row |
| one gesture per kind and group | a move resolves to a single gesture |
| a gesture over every group of a kind stands alone | that resolution is unambiguous |
| every zone a gesture picks from or commits onto takes a slot | a player can reach the cards and the target |
| one readout per field | a figure shows once |

---

## 5. How a move meets its gesture

An interface holds the moves the view served it (`architecture.md` §7) and matches each one:

```
a move matches the gesture whose kind is its kind, and whose group is its group or is stated for every group
```

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
  faces up arrives with the first game that deals readable cards from position zero.
- **`Region` names two places**, because a game states which zones a player owns and the interface states where
  the page puts them. A third region arrives with a game that wants one.
