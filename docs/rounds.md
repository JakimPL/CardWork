# Rounds

`cardwork.rounds` plays a match as a series of rounds: each one dealt afresh, led by a seat in turn, scored
into a standing as it closes, until the standing meets the ending the table was opened with. Every game written
on this framework is that shape, and so is nearly every game worth writing — a hand of poker, a deal of bridge,
a leg of cribbage.

The layer sits above `games` and adds no cursor, no second journal and no rule of play. A game states what
one round *is*; this states the match around it.

```python
class ShowdownGame(RoundGame[ShowdownState]):
    def initial_state(self, players): ...          # the cursor the table opens on
    def deal_round(self, position, leader, rng): ...    # the cards a fresh round gets
    def opening_state(self, position, leader): ... # the cursor it opens on
    def advance_round(self, position, move, rng): ...  # everything inside it
    def round_over(self, position): ...            # whether it has run out
```

---

## 1. Who owns what

**A round belongs to the game; the match belongs to the layer.** The five hooks above are the whole of what a
game states, and every one of them but the first is about a single round. Opening the first one, closing a
finished one into the standing, seating the next leader and calling the match over are the same four steps in
every game, so they are written once here.

**One cursor, two tallies.** `RoundState` extends `GameState` rather than standing beside it, so a round
boundary is an ordinary settlement transaction and projection, replay, events and the adapter need nothing
new.

| field | states |
|---|---|
| `phase` | inherited: the phase of play, or one of the two this layer reserves |
| `to_act` | inherited: the seats that owe an action |
| `points` | inherited: the standing, which is the score a match is won on |
| `round_number` | how many rounds have opened, standing at `BEFORE_THE_FIRST_ROUND` before the first deal |
| `leader` | the seat the round in play opened on, read as `led_by` once a round is open |
| `round_points` | what the round in play has scored, added into `points` as it closes |
| `award` | which end of the standing this match is won at, which the game stamps |
| `rounds`, `target`, `lead` | the clauses the match ends on, which the table states |

Two tallies rather than one, because a client watching a round wants both: the standing it is playing for and
the round it is playing. `led_by` is the leader read as the integer it is inside an open round, and it raises
before the first round, where no seat leads.

**How long a match runs is the table's to state; which end wins it is the game's.** `Conclusion` is what a
table is opened with, and it holds the three clauses a match played in rounds can end on:

```python
game = SheddingGame(players=3, deck=standard_deck(), conclusion=Conclusion(rounds=3), rng=Random(7))
```

| clause | ends the match once |
|---|---|
| `rounds` | that many rounds have been played |
| `target` | some seat holds that score, whether reaching it wins the match or loses it |
| `lead` | the seat at the winning end of the standing leads the next best by that margin |

A conclusion states at least one of them and refuses to be built stating none, so a match with no ending to
reach is unconstructible rather than discovered at the table. Several stated together end it on the first the
standing meets — five hundred points or ten rounds, whichever arrives first. `RoundGame.__init__` stamps them
onto the cursor its game's `initial_state` returns, so **the clauses travel in the record**: a replayed position
describes the ending it was always running to, like everything else about it, and every game shares one route
to a client for it, since `Readout` names a field of the cursor by name.

The direction is the other half and belongs to the game, which is why it is `award` on the state rather than a
clause of the conclusion: `Award.HIGHEST` where a seat scores what it wins and `Award.LOWEST` where it scores
what it is caught with. Only `lead` reads it to end a match — a target is reached by whichever seat gets there
first either way — but a winner is named by it in every case, which is why `Award` lives in `cardwork.states`
beside the `points` tuple it is about, low enough for these rules and for `cardwork.presentation` both.

**`match_over` therefore arrives with an answer.** `RoundState.concluded(standing)` reads the clauses against
the standing, and a game states nothing at all unless its match ends on something a standing cannot say — a
seat left holding every card, a contract made — in which case it overrides the hook as before.

**Phases are named, and two of them are reserved.** `MatchPhase` holds the two this layer runs the table in, and
every phase beside those two says a round is in play, which leaves a game free to name its own — as a `StrEnum`
of its own, so both vocabularies read against the one `phase` field:

```python
class TossPhase(StrEnum):
    TOSSING = "tossing"
    COUNTING = "counting"


def initial_state(self, players: int) -> MatchState:
    return MatchState(phase=MatchPhase.BETWEEN_ROUNDS, points=(0,) * players, award=AWARD)
```

A member carries its value, so a phase read back from the journal or arriving off the wire compares against
either enum, and a `match` reads it as the situation it names.

---

## 2. How a match runs

`RoundGame.advance` answers a move and a settlement differently, and that split is the whole sequence:

```python
if move is not None:
    return self.advance_round(position, move, rng)
```

**A move is answered by the round alone.** The scoring of a round and the deal of the next never join the
transaction one seat's move commits, so an observer reading that event reads one seat's action (§6 of
`architecture.md`). Everything else happens while the table settles, where this reads the round as it stands:

| the table stands | what the rules owe |
|---|---|
| in `MatchPhase.MATCH_OVER` | nothing; the table is at rest |
| in `MatchPhase.BETWEEN_ROUNDS` | `finish_match` when `match_over`, else `open_round` |
| in a round that owes something | whatever `advance_round` answers with |
| in a round owing nothing | `close_round` when `round_over`, else nothing |

So a round boundary is two transactions, each carrying no move: one closing the round that ran out, one
opening the round that follows.

```python
Transaction(seq=7, move=None, effects=(
    SetState(state=MatchState(phase="between_rounds", to_act=frozenset(), points=(4, 9, 3), ...)),
))
Transaction(seq=8, move=None, effects=(
    MoveCards(source="discard", indices={0, 1, 2}, target="stock", face_down=True),   # gathered,
    MoveCards(source="hand:0", indices={0}, target="stock", face_down=True),          # zone by zone
    MoveCards(source="hand:1", indices={0}, target="stock", face_down=True),
    Reorder(zone="stock", order=(11, 3, 0, ...)),                                     # then shuffled
    MoveCards(source="stock", indices={0, 1}, target="hand:0", face_down=True),       # then dealt
    MoveCards(source="stock", indices={0, 1}, target="hand:1", face_down=True),
    SetState(state=MatchState(phase="tossing", round_number=3, leader=1, to_act=frozenset({1}), ...)),
))
```

Splitting them keeps what a round scored legible apart from what the next was dealt, and both stay legible
apart from what a seat did.

**The first deal is the first round's.** `_deal_cards` is concretely empty here, since a table comes out of
the box with its cards where `zones` laid them and the first round is simply the first boundary. Transaction 0
therefore carries the same effects every later opening carries, and `__init__` needs no line for it: the
constructor already runs `_deal_cards` and folds `advance(dealt, None, rng)` into transaction 0.

**A round may owe steps of its own.** `advance_round` is asked again on every settlement pass, so a round that
reveals what was sealed or hands a trick to the seat that won it does that in its own transactions before the
boundary sees it. Answer with an empty run once the round owes nothing: that is what hands the table on to
`round_over`.

**Three hooks arrive with an answer.** `next_leader` draws a seat at random before the first round and takes the
seat after the leader thereafter, which is the rotation every game here wants. `score_round` awards the tally the
round kept. `match_over` reads the conclusion off the cursor. A game that seats its rounds by the standing, or
counts rounds won rather than points scored, overrides one of the three:

```python
def score_round(self, position: Position[MatchState]) -> Points:
    """The round goes to its highest tally, and a tie takes one each."""
    tally = position.state.round_points
    highest = max(tally)
    return tuple(int(scored == highest) for scored in tally)
```

---

## 3. Randomness where no seat has acted

A second round needs a fresh shuffle, and the point it is needed at is one only settlement reaches. So
`advance` takes a generator, exactly as `_deal_cards` and `expand` do, and the two draws a round boundary
makes are the shuffle that opens the round and the seat that leads it.

P2 holds unchanged, because a draw is recorded rather than repeated: the shuffle travels as a `Reorder` and
the leader as a field of the `SetState` that opens the round. `Journal.replay` consults no generator, and

```
history[n] == journal.replay(n)     for every n
```

still holds across a boundary — which is the property worth naming here, since it is what proves a shuffle
made inside `settle` replays. One consequence follows the generator rather than the record: undoing the
transaction that opened a round and settling again deals that round afresh, as `Game.undo` states.

---

## 4. Re-dealing

`Redeal` is the deal of a fresh round made out of the cards the last one left where they lay:

```python
def deal_round(self, position: Position[MatchState], leader: int, rng: Random) -> Effects[MatchState]:
    counts = {hand_of(seat): HAND_SIZE for seat in rotation(leader, position.players)}
    return Redeal(position, pile=STOCK, face_down=True).effects(counts, rng)
```

The leader arrives with the deal because the round's seat is drawn before its cards go out, which is what
lets a game deal from the seat it opens on and give that seat a card the others do not get.

`rounds/seating.py` names the seats a game counts round the table: `rotation(leader, players)` is the order a
round deals, plays and reveals in, and `next_seat(seat, players)` is the seat a turn hands on to.

Three steps, separately available for a game that keeps part of the table standing between rounds:

| step | does |
|---|---|
| `gather()` | every card on the table into the pile at one face, zone by zone in the order their names sort |
| `shuffle(rng)` | the gathered pile laid out in an order drawn once and recorded |
| `distribute(counts)` | the top of the pile dealt out, each zone taking the count it is owed |

`gather` sorts the zones so that the arrangement the pile comes to hold is settled, which leaves the shuffle
the only thing deciding where a card ends up. It names only the cards that do turn, so a pile already lying
at that face asks for nothing. `distribute` follows the order the counts are stated in, so a game deals round
the table from its leader by naming the zones in that order, and a zone owed nothing takes nothing.

Card conservation covers the rest: a re-deal moves cards and creates none, so `validate_board` holds at every
position of every round.

**A game that asks something of the round it opens on states it as a predicate, and the deal is drawn until the
predicate holds.** `admitted(counts, rng, admits)` stands beside `effects` for that — a seat holding a hand
still to be played for, a hand with a move to make in it:

```python
return Redeal(position, pile=PILE, face_down=True).admitted(counts, rng, self._still_to_be_won(leader))
```

Each draw is a shuffle of the whole pile, so the deal that is kept stands uniformly among the deals the game
admits: every one of them is as likely as every other, and no card is favoured beyond what was asked for. This
is why a refused draw is dropped whole. Repairing one instead — swapping the offending card for the top of the
pile, or redrawing a hand and keeping the rest of the table — favours some deals over others, and a player who
knows the repair can read the deal through it.

The accepted draw alone becomes effects, and the order it settles on is what the journal keeps, so a replay
deals the same round and a run of the same seed reaches the same table. Drawing again costs replay nothing
precisely because a shuffle is recorded as the order it produced rather than as the seed it came from. A
predicate no draw satisfies is answered after `DRAWS_MOST` draws with a `ValueError` naming the counts, which
stops a table rather than drawing at it for ever.

---

## 5. What a game states for itself

**A game of four cards** (`cardgames.backend.passing`) is played to a lead of two, which its table states as
`Conclusion(lead=2)`. Its round writes its own outcome — a hand that wins, or a pile run out — into a phase of
its own as the move that settles it lands, and `round_over` reads that phase. A round scores one point to its
winner and nothing to anybody in a draw, which its `round_points` states as the win lands.
`docs/games/passing.md` states the game whole.

**A game of ten turns** (`cardgames.backend.showdown`) is played to a count of rounds, which its table states as
`Conclusion(rounds=n)`. Each of its ten turns adds what the turn was worth into `round_points`, and its
`round_over` reads the two holdings of every seat, which the tenth turn leaves run out. A turn of it is the
settlement step §2 describes: every seat commits at once, and the reveal that scores the turn and opens the next
answers no move of its own. `docs/games/showdown.md` states the game whole.

**A game of matched sets** (`cardgames.backend.shedding`) is played to a count of rounds as well, and reads its
round out of the hands: `round_over` reads a phase of its own, which the move that empties a hand writes, and
which a settlement writes where the stock has run out with no seat holding a set. The award is read off the
hands as they lie rather than accumulated as the round runs, so `round_points` is written once, in the
transaction that closes the round. `docs/games/shedding.md` states the game whole.

Between them they override none of `next_leader`, `score_round` and `match_over`: a seat drawn for the first
round and the next seat after, with the round's tally added into the standing and the ending read off the
clauses the table stated, is what all three of them wanted. The three clauses are one vocabulary, so any of
these games runs to any of the three endings — a two-round `passing` match and a `shedding` match to fifty
points are both a line of configuration, not a line of code.
