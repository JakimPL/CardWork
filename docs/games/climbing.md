# Climbing

`cardgames.backend.climbing` is a game of combinations answered by stronger ones: a seat on lead puts down any
combination the game is played by, the seats after it climb over what stands on the table or give their turn
up, and the round closes on the first hand to run out. It seats two to five, plays over one standard deck dealt
out in equal shares, and runs to the ending its table states, which is a count of rounds where it is played as
it was written.

It is the fourth game written on this framework and the first whose contest lives in the cursor: what a seat
may play is read off the combination lying on the table rather than off a rule about cards, so the three things
worth reading it for are the `Combination` a state carries, the turn a seat gives up by word alone, and a
standing of penalties won at the low end.

```python
game = ClimbingGame(players=4, deck=standard_deck(), conclusion=Conclusion(rounds=3), rng=Random(7))
```

---

## 1. The rules

**A round deals the deck out in equal shares.** Every seat takes as many cards as the table divides the deck
into — thirteen at four seats, ten at five — and what the shares leave over is set aside face down, so a table
of five puts two cards out of play for the round. A hand lies face down, which its owner reads and the rest of
the table reads the size of.

**A seat on lead puts down any combination this game is played by.** `rules.CLIMBING_RANKING` holds that
vocabulary whole — seven patterns across four counts:

| cards | reads as |
|---|---|
| one | any card |
| two | a pair |
| three | a triplet |
| five | a straight, a flush, a full house, or a straight flush |

Four cards read as a combination in no way at all, which follows from the patterns the ranking names and takes
no rule of its own (`docs/combinations.md` §6).

**Every seat after the lead climbs over what stands there, or gives its turn up.** A combination climbs when it
takes as many cards as the one on the table and stands above it in the ranking's order, which is what
`CLIMBING_RANKING.climbs` answers. So a pair is answered by a higher pair and by nothing else: a count is a
contest of its own, and a triplet put down against a pair stands beside that contest rather than over it.

**A seat that passes is out of the contest until a lead reopens.** The passes stand while the combination on
the table keeps changing hands, so a seat that gave its turn up over a pair is walked past however many times
that pair is climbed over. The contest ends once every seat but one has passed: the seat whose combination went
unanswered leads afresh, `state.passed` clears, and the table it leads onto stands empty.

**The round closes on the first seat to play its last card, and every other seat is caught with its hand.**

| the reading | states |
|---|---|
| worth | a pip at its face value, and a jack, queen, king or ace at ten |
| direction | the standing is won at the low end |

`rules.POINTS` is `REGULAR_POINTS` as it stands and `rules.AWARD` is `Award.LOWEST`. The seat that went out
holds nothing, so it is caught with nothing, and every other seat takes the worth of every card left in its
hand. It is the one game here scored on what a seat is left holding, which is why the direction of a standing is
a field a game states (`docs/rounds.md` §1).

**The match belongs to the standing once the clauses its table was opened with are met**, which is a count of
rounds where this is played as it was written and any of `Conclusion`'s three where a table asks for something
else. The first round is led by a seat drawn at random, each later round by the seat after the previous leader,
which is what `RoundGame` arrives with.

---

## 2. The table

| zone | holds | read by |
|---|---|---|
| `hand:p` | the share of the deck a seat was dealt, face down | its owner, and its size by everybody |
| `stack` | every combination the round has put down, face up | everybody |
| `discard` | the cards the shares left over, face down | nobody, its size besides |

A hand lies under the `HAND` policy, which reads a face-down card to its owner. The stack and the discard share
the `PILE` policy and differ in the face their cards lie at, which is the whole difference between what has been
played and what was never dealt.

**The stack is the one pile of this game, and it does two jobs.** It holds the gathered deck a round is dealt
from and it holds what the round puts down, so a combination played lands there face up for the whole table to
read and the deal of the next round gathers everything back into it. A hand is the seat's to arrange and the
stack is the table's (`architecture.md` §3.4): what a combination reads as is a question of the cards it holds,
so a player sorts its hand to find what goes with what, and the stack keeps the run its plays landed in.

**The discard is the cards nobody was dealt.** An equal share is the whole of what this game deals, so a deck
that divides unevenly leaves a remainder that no seat may hold and no seat may read. Setting it aside in a zone
of its own is what keeps the deal conserving the deck: `_final_validation` reads both counts, so a hand holding
another share and a remainder of another size are each refused as the table stands up.

---

## 3. The intents

| intent | means |
|---|---|
| `Play(group="hand", indices={i, j, …})` | put the cards at those positions of this seat's own hand down as one combination |
| `Pass()` | give this turn up over the combination standing on the table |

This is the first game to speak `Pass`, which the vocabulary held unspoken until now
(`architecture.md` §5.3). `intents: ClassVar[Intents[Pass | Play]] = Intents(Pass, Play)` states the two, so the
rules read a move as one of them and the engine refuses every other. A refusal names the rule it comes from:

| the move | the refusal |
|---|---|
| a play naming another group | `Seat 2 plays out of its hand, and named 'sleeve'` |
| a position the hand has run past | `Seat 2 named position 99 of a hand holding 13` |
| cards reading as no combination | `Seat 2 plays a combination this game is played by, and named 4♦ 6♣` |
| a combination that fails to climb | `Seat 0 climbs over any card: 3♥, and played any card: 2♦` |
| a play once the round stands decided | `Seat 2 plays on lead or in answer, and the round stands in the decided phase` |
| a pass on lead | `Seat 2 passes over a combination on the table, and the round stands in the lead phase` |
| a second pass over one combination | `Seat 3 passes once over a combination, and has passed over this one` |
| any other intent | `Seat 2 makes a pass or a play, and offered a take`, which `intents` states and the engine answers |
| a move out of turn | `NotYourTurn`, since one seat holds the turn at a time |

**A move list is a reading of the ranking, and the phase decides which reading.** On lead, `selections` lists
every combination the hand holds at every count, the strongest patterns first, so a hand of thirteen lists its
straight flushes before its singles. In answer, the ranking is narrowed to the count on the table and each
selection is held to climbing over what stands there, so a seat answering a pair is offered its higher pairs
and the pass, and a seat with nothing higher is offered the pass alone.

```python
CLIMBING_RANKING.selections(hand)                                # on lead
CLIMBING_RANKING.sized(on_table.pattern.size).selections(hand)   # in answer, before the climb is read
```

A seat that has passed is offered nothing until the lead reopens, and the turn walks past it: `followed` carries
the turn to the next seat round the table still in the contest, so the rule states which seats it is looking for
and reads one back.

---

## 4. What the phases say

`ClimbingPhase` names the two stages of a round and the close beside them, all read against the one `phase`
field:

| phase | the table stands |
|---|---|
| `ClimbingPhase.LEAD` | on an empty table, the turn with the seat that opens the contest |
| `ClimbingPhase.FOLLOW` | on a combination, the turn with a seat that may climb over it or pass |
| `ClimbingPhase.DECIDED` | on a round closed, the hands scored as they lie |
| `MatchPhase.BETWEEN_ROUNDS` | between two rounds |
| `MatchPhase.MATCH_OVER` | at rest, the match played out |

`ClimbingState` adds three fields. `on_table` is the combination played last, carried as the ranking read it —
its pattern, the cards it was made of and the places they took — so the whole contest is a reading the cursor
already holds and a seat answering is held to it rather than to a count of cards. It reads None on a lead.
`passed` holds the seats out of the contest the table stands in, and `winner` names the seat that played its
last card. A combination sits in a cursor because a pattern can be read back from the word it claims, which is
what makes a ranking serializable at all (`architecture.md` §12).

**The turn a play hands on and the round it closes land in the same transaction.** A play moves its cards and
writes the cursor the contest continues on; where the hand it came out of is now empty, the close is owed at
once, so `advance` writes the decided state beside it in the same commit:

```python
Transaction(seq=61, move=Move(player=3, action=Play(group="hand", indices={0})), effects=(
    MoveCards(source="hand:3", indices={0}, target="stack", face_down=False),
    SetState(state=ClimbingState(phase="follow", to_act=frozenset({0}), on_table=..., ...)),
    SetState(state=ClimbingState(phase="decided", to_act=frozenset(), round_points=(35, 33, 19, 0), ...)),
))
Transaction(seq=62, move=None, effects=(                       # the standing takes the round's penalties
    SetState(state=ClimbingState(phase="between_rounds", points=(35, 33, 19, 0), ...)),
))
```

A pass is one `SetState` and no card moves, which is the whole of what giving a turn up does to the table.
Where that pass is the last one owed, the state it writes is a fresh lead: the phase reads `lead`, `on_table`
reads None, `passed` clears, and the turn goes to the seat whose combination the rest of the table gave up on.

---

## 5. The table on screen

`cardgames.frontend.climbing` states the `Scene` a player reads this game through (`presentation.md`):

| zone | lies | as |
|---|---|---|
| `hand:me` | in the panel the observer plays from, fanned out | the cards it holds, read to find the combinations among them |
| another seat's hand | at that seat's station, fanned out under its count | how close that seat is to going out |
| `stack` | on the shared table, fanned out under its count, called *Played* | every combination the round has put down, the standing one at the open end |
| `discard` | on the shared table, a heap under its count, called *Aside* | the cards nobody was dealt |

**The stack is the one arrangement this game spells out.** A heap reads by the card on top of it, which suits a
pile whose depth is the whole of its news; here the news is the combination itself, and a five-card play read
by one card states nothing about the count or the pattern a seat has to beat. So the lay is written out — a fan
under its count — and every card of the run stays legible, with the combination played last lying whole at the
open end of it (`presentation.md` §3).

Two gestures, and only one of them moves a card:

| gesture | picks in | commits onto |
|---|---|---|
| `Play(group="hand")` | `hand:p` | `stack` |
| `Pass()` | nothing | its own word |

**The pass is the first move any game here sends by word.** It names no card, so there is no zone to hold a
selection open in, and it names no destination, so there is no place to point at: `Commit.WORD` is the answer
the vocabulary kept for exactly this intent, and what an interface draws is a place to press lettered with the
gesture's own caption (`presentation.md` §5). It arms the moment a turn arrives and stands down as soon as a
card is picked up, which falls out of the rule arming every other move rather than out of a rule of its own.

**Selection narrows to the count on the table.** A seat answering a pair reads its own pairs light up and
everything else go dull, since the moves it was served name those cards and no others — the page counts nothing
and reads no rank to do it (`architecture.md` §10). So the contest is legible without a word of it being written
into the interface.

The standing, what the round in play scored, the round in play, the rounds the match runs to and the seat that
went out are readouts over `ClimbingState`. The two fields left off are the two that are no figure: `on_table`
is a whole `Combination` and `passed` a set of seats, and a status line reads a field as the number or the word
it is. Both reach a player anyway — the combination lies face up on the table, and the turn says who is still
in the contest.

**A round is read out at the two phases the match itself stands in**, which `presets.match_interludes` states in
one line: a round decided by one seat going out leaves everybody else holding a figure they had no chance to
change, so the hands as they finished, what each seat was caught with and the standing it was added into stay on
the table under a panel until the player has read them. The match belongs to the seat caught with the least,
which the scene states as `Award.LOWEST` — the one game here whose page names a winner at the low end.

---

## 6. What it asked the framework for

**Nothing, and that is the point of it.** Everything this game wanted was put into the framework by the work
that came before it, each piece written where a second game would find it:

- **The ranking questions** (`docs/combinations.md`) are the whole of its card rules. `selections` reads a hand
  into the combinations it holds, `sized` narrows a ranking to one count, `exactly` holds a play to being the
  whole of a combination, and `climbs` settles the contest. Four calls, no rule about cards written here.
- **`Pass`** and **`Commit.WORD`** were stated as an intent with no game speaking it and a commit with no
  gesture using it. This game is what they were kept for, and neither needed a line changed to be spoken.
- **`following` and `followed`** carry the turn to the next seat a question admits, which is how a table walks
  past the seats that have passed. The rule states the condition and reads the seat back.
- **`Award.LOWEST`** was in the vocabulary from the day `Award` arrived, since a direction with one member
  states nothing. This is the first game to read a standing at that end, and the layer needed nothing for it:
  the same `points` tuple, the same `Readout`, the same panel naming a winner.
- **`confirm_standard_deck` and `confirm_dealt`** are the two setup conditions stated rather than written. What
  this game adds beside them is one count of its own — the cards its shares leave over — which is a check on
  the remainder rather than on a share.

Everything else it consults as it stands: `Redeal` for the gather and the deal, `rotation` for the seats a round
deals to, `Board.cards` and `Board.taken` for reading a zone as the rules read it, `position.holding(HANDS)` for
the seat whose hand has run out, `PointTable.total` for what a hand is caught with, the `HAND` and `PILE`
visibility presets, and `RoundGame` for the match around the round — including `match_over`, which reads the
`Conclusion` its table was opened with.
