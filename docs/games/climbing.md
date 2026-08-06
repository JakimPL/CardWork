# Climbing

`cardgames.backend.climbing` is a game of combinations answered by stronger ones: a seat on lead puts down any
combination the game is played by, the seats after it climb over what stands on the table or give their turn
up, and the round closes on the first hand to run out. It seats two to five, plays over one standard deck dealt
out in equal shares, and runs to the ending its table states, which is a count of rounds where it is played as
it was written.

It is the fourth game written on this framework and the first whose contest lives in the cursor: what a seat
may play is read off the combination lying on the table rather than off a rule about cards, so the four things
worth reading it for are the `Combination` a state carries, the seat a match opens on read off the cards the
deal handed out, the turn a seat gives up by word alone, and a standing of penalties won at the low end.

```python
game = ClimbingGame(players=4, deck=standard_deck(), conclusion=Conclusion(rounds=3), rng=Random(7))
```

---

## 1. The rules

**A round deals the deck out in equal shares.** Every seat takes as many cards as the table divides the deck
into — thirteen at four seats, ten at five — and what the shares leave over is set aside face down, so a table
of five puts two cards out of play for the round. A hand lies face down, which its owner reads and the rest of
the table reads the size of.

**The match opens on the seat holding the two of diamonds, and that seat leads a combination holding it.**
`rules.OPENING_CARD` names the card, which is the one card every other card in the deck climbs over under the
German suit order this game reads by (`docs/combinations.md`). Which seat holds it stands in the cards rather
than in the shuffle, so it is read off the hands once they are dealt and lands in the journal as a transaction
of its own (§4). A deck dividing unevenly could set that card aside, so the first round is dealt again until
some seat holds it — one deal in fifty-two at three seats and one in twenty-six at five, while two seats and
four take the whole deck between them and hand it out every time.

**A seat on lead puts down any combination this game is played by.** `rules.CLIMBING_RANKING` holds that
vocabulary whole — eight patterns across four counts:

| cards | reads as |
|---|---|
| one | any card |
| two | a pair |
| three | a triplet |
| five | a straight, a flush, a full house, four of a rank beside any card, or a straight flush |

Four cards read as a combination in no way at all, which follows from the patterns the ranking names and takes
no rule of its own (`docs/combinations.md` §6).

**Every seat after the lead climbs over what stands there, or gives its turn up.** A combination climbs when it
takes as many cards as the one on the table and stands above it in the ranking's order, which is what
`CLIMBING_RANKING.climbs` answers. So a pair is answered by a higher pair and by nothing else: a count is a
contest of its own, and a triplet put down against a pair stands beside that contest rather than over it.

**The table holds the combination there is to answer, and everything beaten is out of play.** A combination
lies there for as long as it is the one to climb over, and leaves the moment another lands on it or the contest
it stood in closes: what it was is a count of cards face down beside the table rather than a run to read back
(§2). So a seat reads its answer off the table itself, and a lead is put down on a bare one.

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
else. Each round after the first is led by the seat that went out of the one before, which is the one hook this
game answers where `RoundGame` arrives with an answer (`docs/rounds.md` §5): a round is led by the seat that won
the last, and the seat drawn before the first round is the seat its deal begins at.

---

## 2. The table

| zone | holds | read by |
|---|---|---|
| `hand:p` | the share of the deck a seat was dealt, face down | its owner, and its size by everybody |
| `stack` | the combination the contest stands on, face up | everybody |
| `discard` | everything out of play: the cards the shares left over and every combination beaten, face down | nobody, its size besides |

A hand lies under the `HAND` policy, which reads a face-down card to its owner. The stack and the discard share
the `PILE` policy and differ in the face their cards lie at, which is the whole difference between the
combination in play and the cards out of it.

**The stack is the one pile of this game, and it does two jobs.** It holds the gathered deck a round is dealt
from and it holds the combination the contest stands on, so a play lands there face up for the whole table to
read and the deal of the next round gathers everything back into it. It holds one combination at a time: the
play landing carries whatever stood there out of play first, in the same transaction, so the run lying on the
stack is the combination just made and the whole of what a seat has to climb over. A hand is the seat's to
arrange and the stack is the table's (`architecture.md` §3.4): what a combination reads as is a question of the
cards it holds, so a player sorts its hand to find what goes with what, and the stack keeps the run its play
landed in.

**The discard is everything the round has spent.** The cards nobody was dealt open it — an equal share is the
whole of what this game deals, so a deck that divides unevenly leaves a remainder that no seat may hold and no
seat may read — and every combination beaten joins them face down as the next one lands. So the count of it
reads as how much of the deck has gone by, and the cards themselves are past reading by anybody.

`_final_validation` reads the deal at the moment the table stands up, where the discard holds the remainder
alone: a hand holding another share and a remainder of another size are each refused there. What holds through
the round instead is card conservation, which every effect the sweep emits is held to like any other
(`docs/rounds.md` §2).

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
| an opening lead leaving the card the match opens from out | `Seat 1 opens with a combination holding the 2♦, and played 5♥ 5♠` |
| a combination that fails to climb | `Seat 0 climbs over any card: 3♥, and played any card: 2♦` |
| a play once the round stands decided | `Seat 2 plays on lead or in answer, and the round stands in the decided phase` |
| a pass on lead | `Seat 2 passes over a combination on the table, and the round stands in the lead phase` |
| a second pass over one combination | `Seat 3 passes once over a combination, and has passed over this one` |
| any other intent | `Seat 2 makes a pass or a play, and offered a take`, which `intents` states and the engine answers |
| a move out of turn | `NotYourTurn`, since one seat holds the turn at a time |

**A move list is a reading of the ranking, and the phase decides which reading.** On lead, `selections` lists
every combination the hand holds at every count, the strongest patterns first, so a hand of thirteen lists its
straight flushes before its singles. Opening the match, that same list is held to the combinations holding the
card the match opens from, and a hand holding that card holds the combination made of it alone, so the seat
that opens always has a move. In answer, the ranking is narrowed to the count on the table and each selection
is held to climbing over what stands there, so a seat answering a pair is offered its higher pairs and the
pass, and a seat with nothing higher is offered the pass alone.

```python
CLIMBING_RANKING.selections(hand)                                # on lead
OPENING_CARD in named(hand, places)                              # opening the match, over each of those
CLIMBING_RANKING.sized(on_table.pattern.size).selections(hand)   # in answer, before the climb is read
```

A seat that has passed is offered nothing until the lead reopens, and the turn walks past it: `followed` carries
the turn to the next seat round the table still in the contest, so the rule states which seats it is looking for
and reads one back.

---

## 4. What the phases say

`ClimbingPhase` names the two stages of a round, the pair a match opens on and the close beside them, all read
against the one `phase` field:

| phase | the table stands |
|---|---|
| `ClimbingPhase.CHOOSING` | on the first round dealt, the seat that opens still to be read off the hands, nobody to act |
| `ClimbingPhase.OPENING` | on an empty table, the turn with the seat that leads a combination holding the card the match opens from |
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

**The seat a match opens on is a transaction of its own.** The deal writes `choosing` with nobody to act, which
is the round dealt and the hands not yet read; the settlement pass that follows reads the seat holding the
opening card and writes the turn it takes:

```python
Transaction(seq=0, move=None, effects=(                        # the deal, begun at the seat drawn to deal from
    Reorder(zone="stack", order=(21, 14, 28, ...)),
    MoveCards(source="stack", indices={0, 1, ..., 12}, target="hand:2", face_down=True),
    ...                                                        # a share apiece, round the table from there
    SetState(state=ClimbingState(phase="choosing", to_act=frozenset(), round_number=1, leader=2, ...)),
))
Transaction(seq=1, move=None, effects=(                        # the hands read for the seat holding the 2♦
    SetState(state=ClimbingState(phase="opening", to_act=frozenset({1}), leader=1, ...)),
))
```

So the seat that opens is decided where every other decision is decided (`architecture.md` §9): it is journaled,
a replay reaches it by reading the position rather than a generator, and *why is seat 1 leading* is answered out
of transaction 1. The constructor settles once the deal is in, so a table stands up with a seat to act, which is
what every driver and adapter above it reads.

**The turn a play hands on and the round it closes land in the same transaction.** A play sweeps the table it
lands on, moves its cards and writes the cursor the contest continues on; where the hand it came out of is now
empty, the close is owed at once, so `advance` writes the decided state beside it in the same commit:

```python
Transaction(seq=61, move=Move(player=3, action=Play(group="hand", indices={0})), effects=(
    MoveCards(source="stack", indices={0, 1, 2, 3, 4}, target="discard", face_down=True),   # what stood there
    MoveCards(source="hand:3", indices={0}, target="stack", face_down=False),
    SetState(state=ClimbingState(phase="follow", to_act=frozenset({0}), on_table=..., ...)),
    SetState(state=ClimbingState(phase="decided", to_act=frozenset(), round_points=(35, 33, 19, 0), ...)),
))
Transaction(seq=62, move=None, effects=(                       # the standing takes the round's penalties
    SetState(state=ClimbingState(phase="between_rounds", points=(35, 33, 19, 0), ...)),
))
```

A pass is one `SetState` while the contest runs on, which is the whole of what giving a turn up does to the
table. The pass that closes one does the same and sweeps besides: the state it writes is a fresh lead — the
phase reads `lead`, `on_table` reads None, `passed` clears, and the turn goes to the seat whose combination the
rest of the table gave up on — and the combination it settled goes out of play with what came before it, so that
lead is put down on a bare table.

```python
Transaction(seq=7, move=Move(player=3, action=Pass()), effects=(
    MoveCards(source="stack", indices={0, 1, 2, 3, 4}, target="discard", face_down=True),
    SetState(state=ClimbingState(phase="lead", to_act=frozenset({0}), on_table=None, passed=frozenset(), ...)),
))
```

---

## 5. The table on screen

`cardgames.frontend.climbing` states the `Scene` a player reads this game through (`presentation.md`):

| zone | lies | as |
|---|---|---|
| `hand:me` | in the panel the observer plays from, fanned out | the cards it holds, read to find the combinations among them |
| another seat's hand | at that seat's station, fanned out under its count | how close that seat is to going out |
| `stack` | on the shared table, fanned out, called *On the table* | the combination the contest stands on, every card of it legible |
| `discard` | on the shared table, a heap under its count, called *Aside* | how much of the deck the round has spent |

**The stack is the one arrangement this game spells out.** A heap reads by the card on top of it, which suits a
pile whose depth is the whole of its news; here the news is the combination itself, and a five-card play read
by one card states nothing about the count or the pattern a seat has to beat. So the lay is written out — a fan,
uncounted — and every card of the run stays legible, which is the combination to climb over and nothing besides
(`presentation.md` §3). Its count is left off because the cards lying there are the count: a run of five under
the figure five states the same thing twice.

**Aside is where the round's spending shows.** It is a heap under its count and its cards lie face down, so what
has gone by reads as a figure growing while the table keeps to the one combination in play. A seat reading the
two of them together reads how far the round has run and what it has to answer, which is the whole of the
contest as the table states it.

Two gestures, and only one of them moves a card:

| gesture | picks in | commits onto |
|---|---|---|
| `Play(group="hand")` | `hand:p` | `stack` |
| `Pass()` | nothing | its own word |

**The pass is the first move any game here sends by word.** It names no card, so there is no zone to hold a
selection open in, and it names no destination, so there is no place to point at: `Commit.WORD` is the answer
the vocabulary kept for exactly this intent, and what an interface draws is a place to press lettered with the
gesture's own caption (`presentation.md` §5). It arms the moment a turn arrives and stands down as soon as a
card is picked up, which falls out of the rule arming every other move rather than out of a rule of its own. The
caption is *Pass*, which is the word this game is played by and reads at the size of a card.

**Every phase carries the line a player reads it by, and the opening carries the card it opens from.** *Put down
a combination holding the 2♦* is written off `rules.OPENING_CARD`, so the words a seat reads and the rule its
move is held to are one statement. *Finding the seat that opens* is the line the moment between the deal and
that turn carries: the table passes through it inside the burst that stands it up, so nobody waits at it, and it
reads as a reason wherever a journal is stepped through transaction by transaction.

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
that came before it, each piece written where a second game would find it — the two the variant asked for late,
a deal held to a condition and a leader of its own, among them:

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
- **`Redeal.admitted`** deals a round again until the game admits the draw, which passing asked for so that a
  hand still had something to be won with. Here the condition is a card in somebody's hand, and the draw that is
  kept stands uniformly among the deals holding it, so the deck this match opens from is an honest shuffle
  answering a question (`docs/rounds.md` §2).
- **`next_leader`** arrives with the rotation three of these games want, and states itself as a hook because a
  fourth might not. This is that fourth: the seat that went out leads the round after, and the answer is a field
  of the cursor read back rather than a rule the layer needed teaching.

Everything else it consults as it stands: `Redeal` for the gather and the deal, `rotation` for the seats a round
deals to, `Board.cards` and `Board.taken` for reading a zone as the rules read it, `position.held(HANDS)` for
the hands the opening card is looked for in, `position.holding(HANDS)` for the seat whose hand has run out,
`PointTable.total` for what a hand is caught with, the `HAND` and `PILE` visibility presets, and `RoundGame` for
the match around the round — including `match_over`, which reads the `Conclusion` its table was opened with.
