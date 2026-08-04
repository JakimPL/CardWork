# Showdown

`cardgames.backend.showdown` is a game of ten sealed turns: five cards a seat reads, five that lie face down to the
whole table its owner included, and one card from every seat committed at once each turn and turned over
together. It seats two to five, plays over one standard deck, and runs to the ending its table states, which is
a count of rounds where it is played as it was written.

It is the second game written on this framework and the first played simultaneously, so the two things worth
reading it for are the sealed commitment and the turn that settles itself: every seat owes an action at the
same time, and the reveal belongs to the settlement that follows the last of them.

```python
game = ShowdownGame(players=4, deck=standard_deck(), conclusion=Conclusion(rounds=3), rng=Random(7))
```

---

## 1. The rules

**A round deals every seat five cards to read and five blind**, from the stock that holds the gathered deck.
The blind five lie face down to everybody, their owner as much as the rest of the table, and every seat reads
the size of both holdings.

**Each of ten turns, every seat commits one card at once.** A commitment names the hand or the blind and a
position within it, so a card is chosen by what it is or by where it lies. It goes face down into the seat's
own tray, where it stays sealed while the rest of the table acts. A commitment stands once it is sent, which
the vocabulary states by holding one intent and no retraction.

**The cards turn over together as the last of them lands.** They go face up on the discard from the leader
round the table, so the order they lie in states which seat played which and the whole table reads every one.

**The strongest card takes what every other one revealed is worth.**

| the reading | states |
|---|---|
| strength | rank first, and a tie of rank settled by ♠ ♥ ♦ ♣ |
| worth | a pip at its face value, and a jack, queen, king or ace at ten |

The order is total, so exactly one card of any turn stands above the rest and the turn has one winner. The
card that takes the turn brings nothing of its own to the tally: a seat scores what it took from the others.
`rules.STRENGTH` and `rules.POINTS` name the two readings, and both come from `cardwork.cards` as they stand.

**Ten turns run both holdings out and close the round**, whose tally is added into the standing. **The match
belongs to the standing once the clauses its table was opened with are met**, which is a count of rounds where
this is played as it was written and any of `Conclusion`'s three where a table asks for something else
(`docs/rounds.md` §1). The first round is led by a seat drawn at random, each later round by the seat after the
previous leader, which is what `RoundGame` arrives with.

---

## 2. The table

| zone | holds | read by |
|---|---|---|
| `hand:p` | the five cards a seat reads | its owner, and its size by everybody |
| `blind:p` | the five that lie face down | nobody, their size besides |
| `tray:p` | the card a seat has committed to the turn | nobody, its size besides |
| `stock` | the cards a round left undealt, face down | nobody, its size besides |
| `discard` | every card the round has revealed, face up | everybody |

A hand lies under the `HAND` policy, which reads a face-down card to its owner. A blind and a tray lie under
`HIDDEN`, which reads a card to nobody at either face — so the five a seat plays blind stay unknown to it
until they turn, and a commitment is legible as a size alone while the turn is open. The stock and the discard
share the `PILE` policy and differ in the face their cards lie at, which is the whole difference between what
is still to come and what the turn has shown.

A tray reading to nobody is what makes the commitment sealed: while a seat has acted and the rest have yet
to, the table reads that it acted and reads its card as the turn turns over.

---

## 3. The intent

| intent | means |
|---|---|
| `Play(group="hand", indices={i})` | commit the card at position *i* of the five this seat reads |
| `Play(group="blind", indices={i})` | commit the card at position *i* of the five lying face down |

One intent covers the game, and `Holding` holds the two words it carries, so the vocabulary a client sends is
closed and read by a `match`. A refusal names the rule it comes from:

| the move | the refusal |
|---|---|
| a commitment naming another holding | `Seat 2 commits from its hand or its blind, and named 'sleeve'` |
| a commitment of several cards | `Seat 2 commits one card at a time, and named 2` |
| a position the holding has run past | `Seat 2 named position 0 of a hand holding 0` |
| any other intent | `Seat 2 commits one card, and offered take` |
| a second commitment in one turn | `NotYourTurn`, since the turn stands with the seats that have yet to act |

`legal_moves` lists every card of both holdings for each seat still to commit, so a solver reading the list
plays by the rules alone, and a seat that has committed leaves the list to the seats that have not. A seat
served that list in its view reads its own commitments out of it, since the projection narrows the moves to
their owner as it narrows the cards (`architecture.md` §7).

Every seat owing an action at once meets the engine's optimistic commit: a client pins its move to the
sequence it read, so two seats committing at the same moment leave the later one reading the position again
and sending on the sequence it now finds. `architecture.md` §6 states that exchange, and §4.1 and §4.3 state
what this game is the first to play: a simultaneous turn is a `to_act` holding every seat, and a sealed
commitment is a zone policy.

---

## 4. What the phases say

`ShowdownPhase` names the one stage of a round beside the two `MatchPhase` keeps for the match, both read
against the one `phase` field:

| phase | the table stands |
|---|---|
| `ShowdownPhase.COMMITTING` | in a round, the turn with every seat that has yet to commit |
| `MatchPhase.BETWEEN_ROUNDS` | between two rounds |
| `MatchPhase.MATCH_OVER` | at rest, the match played out |

A round runs in one stage because a turn is one simultaneous commitment: the reveal is what closes a turn
and opens the next, so a table at rest is always a table owing commitments.

`ShowdownState` adds `turn_number` alone, which names the turn in play and stands at the tenth once that turn
has been revealed. How long the match runs stands on `RoundState` as the clauses its table was opened with, so
a replayed position describes the ending it was always running to without this game keeping a field for it.

**A commitment answers for itself, and the turn settles itself.** The card sealed into a tray and the seat
taken out of the turn land in the transaction the commitment commits; the reveal, the points it awards and
the turn that follows land in the one settlement transaction after the last commitment. So an observer reads
one seat's action, then reads a turn whole:

```python
Transaction(seq=31, move=Move(player=2, action=Play(group="blind", indices={1})), effects=(
    MoveCards(source="blind:2", indices={1}, target="tray:2", face_down=True),
    SetState(state=ShowdownState(phase="committing", to_act=frozenset(), turn_number=4, ...)),
))
Transaction(seq=32, move=None, effects=(
    MoveCards(source="tray:1", indices={0}, target="discard", face_down=False),   # the leader first,
    MoveCards(source="tray:2", indices={0}, target="discard", face_down=False),   # then round the table
    MoveCards(source="tray:0", indices={0}, target="discard", face_down=False),
    SetState(state=ShowdownState(phase="committing", to_act=frozenset({0, 1, 2}), turn_number=5,
                                round_points=(14, 31, 9), ...)),
))
```

What the boundary then does — the round scored into the standing, the gather, the shuffle, the next deal, the
next leader — is `cardwork.rounds`, written once for every game.

---

## 5. The table on screen

`cardgames.frontend.showdown` states the `Scene` a player reads this game through (`presentation.md`):

| zone | lies | as |
|---|---|---|
| `hand:me` | in the panel the observer plays from, fanned out | the five it reads and picks by what they are |
| `blind:me` | beside it, in a row of whole cards | five backs it picks by where they lie |
| `tray:me` | beside those, in a single place | the card it has sealed this turn |
| another seat's three | at that seat's station | a hand fanned under its count, a blind as a heap under its own, and a tray saying whether that seat has committed |
| `stock` | on the shared table, a heap read by its count | what is still to be dealt |
| `discard` | on the shared table, a heap read by its top card | every card the round has revealed |

A blind lies in a row for the seat picking by position and as a heap for everybody else, since what a blind says
across the table is how many cards are still to come out of it.

Both holdings commit the same way, one gesture apiece:

| gesture | picks in | commits onto |
|---|---|---|
| `Play(group="hand")` | `hand:p` | `tray:p` |
| `Play(group="blind")` | `blind:p` | `tray:p` |

The positions either intent names address the zone the intent names, which is the other way round from the
game before this one, where they address a zone no move mentions. That pair of games is the reason a layout
states the pairing rather than a rule deriving it (`presentation.md` §1).

**The blind is playable because the projection keeps positions.** A blind card reaches its own seat as a
placeholder standing at its true index (`architecture.md` §7), so a player picks the third of five backs and
the commitment lands on the card lying there.

**A round is read out at the two phases the match itself stands in**, which `presets.match_interludes` states in
one line: the ten turns of a round add up to a figure worth stopping over, so what each seat took of the round and
the standing it was added into stand over the table until the player has read them. The match belongs to the seat
holding the most points, which the scene states as `Award.HIGHEST`.

---

## 6. What it asked the framework for

Two primitives this game shares with the one before it, lifted into the layers below rather than written
twice:

- **`rounds/seating.py`** holds `rotation(leader, players)` and `next_seat(seat, players)`, the seats a round
  deals, plays and reveals in. This game reveals from the leader round the table; the game before it deals
  and passes that way.
- **`zones/zone.py::cards_of(zone)`** reads the cards of a zone as the rules read them, apart from the face
  they lie at.

It is also the first game to lay a zone under the `HIDDEN` visibility preset, which is what a blind five and
a sealed commitment are made of. Everything else it consults as it stands: `Redeal` for the gather and the
deal, `REGULAR_ORDER` and `REGULAR_POINTS` for the strength and the worth of a card, `RoundGame.match_over`
reading the `Conclusion` its table was opened with, and the engine for the journal, the projection and the
wire.
