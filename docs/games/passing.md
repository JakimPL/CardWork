# Passing

`cardgames.backend.passing` is a game of four cards: three in every hand, a fourth travelling round the table, and a
win falling to the seat the moment three of the four it holds read as one rank or one suit. It seats two to
eight, plays over any number of whole standard decks and any number of jokers, and runs until one seat leads
the next best by two points.

It is the first game written on this framework, so what it needs and what it inherits are worth reading
together: it states four modules of its own — the cursor, the table, the rules, the hooks — and asks
`cardwork.rounds` for the match, `cardwork.combinations` for the reading of a hand, and the engine for
everything else.

```python
game = PassingGame(players=4, deck=standard_decks(1, black_jokers=1, red_jokers=1), rng=Random(7))
```

---

## 1. The rules

**A round deals three cards to every seat and a fourth to the seat leading it**, from the pile that holds the
gathered deck. Exactly one seat holds four cards at a time, and the turn travels with that card.

**A turn admits one exchange and closes on a pass.** The seat on turn may give one held card up for the top of
the pile, the card it gives up going face up on the stack. It then passes one card to the seat next round the
table, which closes the turn.

**A hand of four wins where some three of it read as one rank or as one suit, while the four do not.** A joker
stands in for whatever the three asks of it. That single sentence settles every hand:

| the hand | reads |
|---|---|
| three sevens beside a king | a win |
| three spades beside a heart | a win |
| four sevens, or four spades | four alike, which holds the win back |
| two sevens beside a joker and a king | a win, the joker standing as the third seven |
| three sevens beside a joker | four alike, since the spare joker joins them |
| two cards sharing neither rank nor suit beside two jokers | a win |
| one card beside three jokers, or four jokers | four alike |

So "every joker a winning hand holds sits inside the three" follows from the rule rather than standing beside
it: a joker left over reads alike with the other three, and four alike hold the win back. Three jokers and four
declare nothing, since the lone natural card — or none — leaves the four reading alike.

Cards from different decks count as themselves, so three spade cards are three of a suit where two of them are
the same spade. `rules.PASSING_EVALUATION` states that as `Duplicates.COUNT`.

**A win takes the round and scores its seat one point, and needs no claim to do it.** A seat holding a win has
nothing to gain by passing it on, so there is no decision here for a move to carry: the rules award the win the
moment the cards read one, and the hand turns face up so the table reads what took the round. **An exhausted pile
draws the round** as the turn it ran out on closes, and scores nobody — the seat that took the last card is still
awarded the win it drew.

The award travels in the transaction that dealt or completed the hand, so a seat is never offered a move while
holding a win and no stretch of latency comes between holding one and being given it. Because a hand reading a
win ends its round at once, a pile of forty-odd cards outlives no run of play, which leaves the drawn round a
rule the game keeps rather than one it reaches.

**The match belongs to the first seat leading the next best by two points.** The first round is led by a seat
drawn at random, each later round by the seat after the previous leader, which is what `RoundGame` arrives
with.

---

## 2. The table

| zone | holds | read by |
|---|---|---|
| `hand:p` | the three cards a seat holds, four while it has the turn | its owner, and the whole table once a win shows it |
| `pile` | the rest of the deck, face down | nobody, its size besides |
| `stack` | every card given up in an exchange, face up | everybody |

A hand lies face down under the `HAND` policy, so its owner reads it and every other seat reads its size. The
pile and the stack share the `PILE` policy and differ in the face their cards lie at, which is the whole
difference between what a seat may take and what it has given up.

---

## 3. The intents

| intent | means |
|---|---|
| `Take(group="pile", indices={i})` | the exchange: give up card *i*, take the top of the pile |
| `Give(target_player=p, indices={i})` | the pass: hand card *i* to the seat next round the table |

Both name positions in the seat's own hand, and the group or the seat they name is the other side of the move.
Two intents are the whole vocabulary, because the third thing a seat could do with a hand — say that it wins —
is a thing the cards say for themselves. A refusal names the rule it comes from:

| the move | the refusal |
|---|---|
| an exchange naming another zone | `Seat 2 exchanges with the pile, and named 'stack'` |
| an exchange with the pile run out | `Seat 2 exchanges with a pile that has run out` |
| a second exchange in one turn | `Seat 2 exchanges once in a turn, and has exchanged in this one` |
| a pass to any seat but the next | `Seat 2 passes to seat 3, and named seat 0` |
| a card the hand does not hold | `Seat 2 named position 4 of a hand holding 4` |
| any other intent | `Seat 2 exchanges or passes, and offered play` |

`legal_moves` lists every exchange and pass the turn admits, which is every move there is to make, so a solver
reading the list plays by the rules alone, and the seat on turn is offered the same list in its view.

---

## 4. What the phases say

`PassingPhase` names the two stages of a round beside the two `MatchPhase` keeps for the match, both read
against the one `phase` field:

| phase | the table stands |
|---|---|
| `PassingPhase.PASSING` | in a round, the turn with one seat |
| `PassingPhase.DECIDED` | in a round with its outcome, awaiting the boundary that scores it |
| `MatchPhase.BETWEEN_ROUNDS` | between two rounds |
| `MatchPhase.MATCH_OVER` | at rest, the match decided |

`PassingState` adds the two things a round tracks beyond the cursor every match keeps: `swapped`, which states
that the turn has spent its exchange and reads False again as the turn passes on, and `winner`, which names the
seat the round belongs to.

**A move carries every change it causes, and a deal is answered on the settlement that follows it.** The exchange
a turn spends, the turn a pass hands on, the win the hand left behind reads, the draw an exhausted pile settles:
each lands in the transaction of the move that prompted it, which is what keeps a window of latency out of an
award nobody chose. The one win no move puts on the table is the one a fresh deal lays out, and `advance_round`
answers for that on a settlement pass — so a game built here settles once before service, leaving a round in
play with a seat on turn.

What the boundary then does — the round scored into the standing, the gather, the shuffle, the next deal, the
next leader — is `cardwork.rounds`, written once for every game.

---

## 5. The table on screen

`cardgames.frontend.passing` states the `Scene` a player reads this game through, and states nothing of how it
looks (`presentation.md`). Which zone lies where:

| zone | lies | as |
|---|---|---|
| `hand:me` | in the observer's own region, fanned out | the cards it picks from |
| `hand:other` | on that seat's plaque, as a count | what the table reads of another hand |
| `pile` | on the shared table, a heap read by its count | a stack of backs |
| `stack` | on the shared table, a heap read by its top card | every card given up |

A turn is two gestures, one for each intent of §3:

| gesture | picks in | commits onto |
|---|---|---|
| `Take(group="pile")` | the observer's own hand | the pile, which is what the exchange is with |
| `Give(target_player=...)` | the observer's own hand | the seat the move names |

Both pick in the hand, because the positions either intent names address the cards the seat holds: the pile's
own positions are named by no move at all. So a card is chosen in one place and sent by pointing at where it
goes — the pile to trade it, the next seat's plaque to pass it — and a selection alone commits nothing.

The standing, the round in play and the seat a round was won by are readouts over `PassingState`. The four
phases of §4 are captioned there as well, which is what a player reads in place of `"between_rounds"`.

---

## 6. What it asked the framework for

Two things this game needed that the layers below it gained for every game after it:

- **`deal_round(position, leader, rng)`** takes the leader, because a deal that gives one seat a card the others
  do not get has to know which seat leads. The seat is drawn before the cards go out, so the leader is there to
  be handed over.
- **`standard_decks(count, *, black_jokers, red_jokers)`** builds a deck of several standard decks, and
  **`standard_multiplicity(deck)`** counts the whole decks the suited cards of one make, which is what
  `_validate_initial_deck` reads to accept the deck it was handed.

Everything else it consults as it stands: `Redeal` for the gather and the deal, `contains` and `matches` for the
reading of a hand, the `HAND` and `PILE` visibility presets for the table, and the engine for the journal, the
projection and the wire.
