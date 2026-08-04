# Shedding

`cardgames.backend.shedding` is a game of matched sets laid down: a turn sheds two cards or more reading as one
rank, or draws one card off the stock, and the round goes to the seat left holding the fewest cards. It seats
two to six, plays over one standard deck, and runs the number of rounds it was built for.

It is the third game written on this framework and the first whose move names several cards at once, so the two
things worth reading it for are the multi-card intent and the choice a turn carries: a pair goes down now, or it
waits for the third of its rank to arrive.

```python
game = SheddingGame(players=3, deck=standard_deck(), rounds=3, rng=Random(7))
```

---

## 1. The rules

**A round deals four cards to every seat**, from the stock that holds the gathered deck. A hand lies face down,
which its owner reads and the rest of the table reads the size of.

**A turn either sheds or draws.**

| the turn | does |
|---|---|
| a shed | lays two cards or more of one rank face up on the discard |
| a draw | takes the card at the end of the stock into the hand, face down |

Either way the turn passes to the next seat. `rules.reads_alike` holds the shed rule whole: `SameRank` at as
many places as there are cards, so a pair, a triplet and four of a rank all answer to it and cards of two ranks
answer to none of them.

**That is the whole of the choice, and it is a real one.** A seat holding a pair may lay it down or hold it back
and fish for the third of its rank, which is worth doing only while the stock has cards left to hand over — and
every card drawn is a card that may never find a partner. A hand holding three of a rank offers both of its
pairs beside the three of them, so a set is chosen as well as found.

**The round goes to the seat left holding the fewest cards.** A seat that sheds its last card holds none, which
is the fewest a hand runs to, so going out takes the round on the spot and closes it. Otherwise the round runs
until the stock has run out and no seat holds a set — a seat with neither is passed over, since it has nothing
it may do — and the shortest hand at the table takes it, every one of them where several stand equally short.
`rules.taken_by` reads the award off the hands as they lie, so one rule scores either close.

**The match belongs to the standing once it has played the rounds it was built for.** The first round is led by
a seat drawn at random, each later round by the seat after the previous leader, which is what `RoundGame`
arrives with.

---

## 2. The table

| zone | holds | read by |
|---|---|---|
| `hand:p` | the cards a seat holds, four at the deal and as many as its draws make | its owner, and its size by everybody |
| `stock` | the cards a round left undealt, face down | nobody, its size besides |
| `discard` | every set the round has shed, face up | everybody |

A hand lies under the `HAND` policy, which reads a face-down card to its owner. The stock and the discard share
the `PILE` policy and differ in the face their cards lie at, which is the whole difference between what is still
to come and what has been laid down.

**The stock is dealt from one end of its run and drawn from the other**, which a shuffled pile of backs is
indifferent to: every card in it reads to nobody, so neither end is the readable one. `rules.drawn_from` names
the end a turn takes, and it is the end a player points at — an interface reads a heap by the last card of the
run (`presentation.md` §6), and a rule stated that way puts the card a seat clicked and the card it draws in one
place.

**A hand is the first zone in this repository that grows while a round runs.** A passing hand stands at three
cards and four, a showdown holding only ever shrinks; a shedding hand takes whatever its draws give it and runs
past a dozen in an unlucky round, which is the case a fan of cards had to be drawn for (`architecture.md` §10).

---

## 3. The intent

| intent | means |
|---|---|
| `Discard(group="hand", indices={i, j, …})` | shed the cards at those positions of this seat's own hand |
| `Take(group="stock", indices={n})` | draw the card at position *n*, the end of the stock |

This is the first game to speak `Discard`, and the first whose indices name more than one card. A refusal names
the rule it comes from:

| the move | the refusal |
|---|---|
| a shed naming another group | `Seat 2 sheds from its hand, and named 'sleeve'` |
| a shed of one card | `Seat 2 sheds 2 cards or more, and named 1` |
| a position the hand has run past | `Seat 2 named position 5 of a hand holding 4` |
| a shed of two ranks | `Seat 2 sheds cards reading as one rank, and named 2♠ 7♦` |
| a draw naming another zone | `Seat 2 draws from the stock, and named 'discard'` |
| a draw from an exhausted stock | `Seat 2 draws from a stock that has run out` |
| a draw naming another position | `Seat 2 draws position [39] of the stock, and named [0]` |
| any other intent | `Seat 2 sheds or draws, and offered play` |
| a move out of turn | `NotYourTurn`, since one seat holds the turn at a time |

`legal_moves` lists every set the hand holds and the draw beside them, so a triplet lists both of its pairs and
the three of them and a client reading the list reads the whole choice. The list runs empty for one position
only — a seat holding no set with the stock run out — and that is the seat a settlement pass hands the turn past,
so a table at rest always stands with a seat that has something to do.

The sets come from the ranks of the hand rather than from its positions: `rules.sets_in` files each position
under the rank standing there and takes the subsets of two and more, which lists eleven sets for four of a rank
and never walks the 2ⁿ subsets of a hand of any size.

---

## 4. What the phases say

`SheddingPhase` names the one stage of a round beside the two `MatchPhase` keeps for the match, both read
against the one `phase` field:

| phase | the table stands |
|---|---|
| `SheddingPhase.SHEDDING` | in a round, the turn with a seat that may shed or draw |
| `SheddingPhase.DECIDED` | on a round closed, its award read off the hands |
| `MatchPhase.BETWEEN_ROUNDS` | between two rounds |
| `MatchPhase.MATCH_OVER` | at rest, the match played out |

`SheddingState` adds `winner`, which names the seat that went out and reads None through a round in play and
through a round the stock ran out of, and `rounds`, the number of rounds the match was built for — kept on the
state so a replayed position describes how long it was ever going to run.

**A turn answers for itself, and a turn nobody can take is answered by the settlement.** The cards a move moves
and the seat the turn travels to land in the transaction the move commits; the round it closes lands there too,
so a seat is awarded the round in the moment it goes out. What belongs to the settlement is the one turn that
falls to nobody:

```python
Transaction(seq=57, move=Move(player=1, action=Discard(group="hand", indices={0, 3})), effects=(
    MoveCards(source="hand:1", indices={0, 3}, target="discard", face_down=False),
    SetState(state=SheddingState(phase="shedding", to_act=frozenset({2}), ...)),
))
Transaction(seq=58, move=None, effects=(                       # seat 2 holds no set and the stock has run out
    SetState(state=SheddingState(phase="shedding", to_act=frozenset({0}), ...)),
))
```

A draw is the same shape with the cards running the other way, and a round the stock ran out of closes in a
settlement of that kind whose `SetState` reads `phase="decided"` and carries the award.

---

## 5. The table on screen

`cardgames.frontend.shedding` states the `Scene` a player reads this game through (`presentation.md`):

| zone | lies | as |
|---|---|---|
| `hand:me` | in the panel the observer plays from, fanned out | the cards it holds, read by rank to find what goes with what |
| another seat's hand | at that seat's station, fanned out under its count | how close that seat is to going out |
| `stock` | on the shared table, a heap read by its count | what is still to be drawn |
| `discard` | on the shared table, a heap read by its top card | the last set shed |

Two gestures, running opposite ways:

| gesture | picks in | commits onto |
|---|---|---|
| `Discard(group="hand")` | `hand:p` | `discard` |
| `Take(group="stock")` | `stock` | `hand:p` |

**The draw is the first gesture that takes a card rather than lays one down**, so it picks on the shared table
and commits onto a zone of the seat's own. The layout vocabulary needed nothing new for it: a gesture names the
zone its indices address and the place a player points at to send it, and which of the two belongs to the seat
was never part of the pairing.

**Multi-card selection reads the rules straight off the list.** A hand of 5♠ 5♥ 5♦ 9♣ offers four sets, and the
interface narrows them as the selection grows (`architecture.md` §10):

| picked up | lit further | armed |
|---|---|---|
| nothing | the three fives, and the stock | nothing |
| 5♠ | 5♥ and 5♦ | nothing |
| 5♠ 5♥ | 5♦ | the pair, so the discard lights up |
| 5♠ 5♥ 5♦ | nothing | the three of them |

The nine never lights, since no move names it. So a player reads what is playable without being told the rule,
and a selection of one card commits nothing — the discard is the place that sends it.

**A round is read out at the two phases the match itself stands in**, which `presets.match_interludes` states in
one line: the hands as they finished, what the shortest of them took, and the standing it was added into stay on
the table under a panel until the player has read them. A round that turns on one card is the round most worth
stopping at, so the seat that went out is named rather than replaced by a fresh deal. The match belongs to the
seat holding the most round wins, which the scene states as `Award.HIGHEST`.

---

## 6. What it asked the framework for

**Nothing.** This is the first game to add no primitive to any layer below it, which is the claim the two before
it were written to make good on. What it does is put what stands there under a load none of it had carried:

- **`Discard`** was in the vocabulary from the start and unspoken until now (`moves/actions.py`).
- **A move naming several cards** travels the projection, the wire, `legal_moves` and the interface's selection
  unchanged, since `indices` was a set the whole way along.
- **`SameRank(places=n)`** is read at a size the cards decide rather than a pattern the rules fix, which is what
  `matches` over a pattern built per question is for (`combinations.md` §6).
- **A gesture committing onto the observer's own zone** exercises the pairing in the direction neither earlier
  game took (`presentation.md` §1).
- **A zone that grows through a round** is what the interface's fan was measured against, at seventeen cards.

Everything else it consults as it stands: `Redeal` for the gather and the deal, `rotation` and `next_seat` for
the seats a round deals and travels in, `cards_of` for reading a zone as the rules read it, the `HAND` and `PILE`
visibility presets, and `RoundGame` for the match around the round.
