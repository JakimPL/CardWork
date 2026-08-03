# Passing

`cardgames.passing` is a game of four cards: three in every hand, a fourth travelling round the table, and a
win claimed the moment three of the four a seat holds read as one rank or one suit. It seats two to eight,
plays over any number of whole standard decks and any number of jokers, and runs until one seat leads the
next best by two points.

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

**A turn admits one exchange and closes on a pass or a claim.** The seat on turn may give one held card up for
the top of the pile, the card it gives up going face up on the stack. It then either claims a win or passes one
card to the seat next round the table, which closes the turn.

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

**A confirmed claim wins the round and scores its seat one point.** The hand turns face up as the claim lands,
so the table reads the win the rules confirmed. **An exhausted pile draws the round** as the turn it ran out on
closes, and scores nobody — which leaves the seat that took the last card free to claim the win it drew.

**The match belongs to the first seat leading the next best by two points.** The first round is led by a seat
drawn at random, each later round by the seat after the previous leader, which is what `RoundGame` arrives
with.

---

## 2. The table

| zone | holds | read by |
|---|---|---|
| `hand:p` | the three cards a seat holds, four while it has the turn | its owner, and the whole table once a claim shows it |
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
| `Declare(claim="win", indices=set())` | the claim: this whole hand is a win |

Every one of them names positions in the seat's own hand, and the group or the seat it names is the other side
of the move. A claim is of the whole hand, which an empty set of indices states and a full set states as well.

`PassingClaim` holds the word a claim carries, so the vocabulary a client sends is closed and read by a
`match`. A refusal names the rule it comes from:

| the move | the refusal |
|---|---|
| an exchange naming another zone | `Seat 2 exchanges with the pile, and named 'stack'` |
| an exchange with the pile run out | `Seat 2 exchanges with a pile that has run out` |
| a second exchange in one turn | `Seat 2 exchanges once in a turn, and has exchanged in this one` |
| a pass to any seat but the next | `Seat 2 passes to seat 3, and named seat 0` |
| a claim in another word | `Seat 2 claims a win, and claimed 'bluff'` |
| a claim of part of the hand | `Seat 2 claims a win of its whole hand, and named [0]` |
| a claim the hand holds back | `Seat 2 claims a win its hand holds back: three cards read alike, and the four do not` |

`legal_moves` lists every exchange and pass the turn admits, and a claim where the hand does declare, so a
solver reading the list plays by the rules alone and a refused claim is one a client made up.

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
seat whose claim the rules confirmed.

**Every change a round makes answers a move.** The exchange a turn spends, the turn a pass hands on, the outcome
a claim or an exhausted pile settles: each lands in the transaction of the move that prompted it, so
`advance_round` finds nothing owed on a settlement pass and hands the table straight to the boundary. What the
boundary then does — the round scored into the standing, the gather, the shuffle, the next deal, the next leader
— is `cardwork.rounds`, written once for every game.

---

## 5. What it asked the framework for

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
