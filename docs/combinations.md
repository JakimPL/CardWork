# Combinations

`cardwork.combinations` reads a run of cards and answers what it is: whether these four cards are three of
a suit, whether a seven-card hand holds a full house, which of two hands wins, and what a combination is
worth in points. It works on cards alone — no zones, no seats, no turn — so a game consults it wherever it
needs to know, and two games with different rules consult it with different readings.

The package is the answer to one question asked five ways:

```python
matches(cards, pattern, evaluation)  # are these cards that combination, all of them?
contains(cards, pattern, evaluation)  # do these cards hold it somewhere?
find(cards, pattern, evaluation)  # the strongest instance of it they hold
find_all(cards, pattern, evaluation)  # every instance, strongest first
selections(cards, pattern, evaluation)  # every set of places among them that reads as it
```

---

## 1. Who owns what

Three statements settle where every rule lives, and the rest of the package follows from them.

**A pattern carries its rule whole.** `Pattern` is the abstraction, and a pattern states three things about
itself: how many cards it takes, which readings it admits, and where an instance of it stands among the
others. Everything a rule means is one of those three answers, so a game reaches a rule of its own by
writing a pattern rather than by teaching the search a new word.

```python
class Pattern(BaseFrozen, ABC):
    kind: str

    @property
    @abstractmethod
    def size(self) -> int: ...

    @abstractmethod
    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]: ...

    @abstractmethod
    def strength(self, reading: Reading, evaluation: Evaluation) -> Key: ...

    @abstractmethod
    def __str__(self) -> str: ...
```

**A pattern states its rule as the readings it admits, rather than as a test a set of cards passes.** A
test would answer for the cards it is handed and leave the rest to a search over their subsets; the
readings answer for the pattern alone. That is what keeps a question's cost with the pattern rather than
with the hand, and it is what gives a joker a place to stand in for.

**The reading of the deck belongs to the game, and it is passed in.** Which ranks run in which order,
whether the wheel turns, whether a joker stands in, and whether a card held twice counts twice are an
`Evaluation` a game states once and hands to every question it asks. A pattern is the same rule under any
reading of the deck.

The search below these statements — the tally, the filling, `detect`, `Ranking`, `Scoring` — reads shapes
and strength keys, and knows no rule by name.

**A rule travels under a word, and the word reads it back.** `kind` is that word: a concrete pattern states
it as the default of the field, and writing the class is what puts it in play. `AnyPattern` is the annotation
every field holding a pattern carries, and it reads a word back to the class that stated it, so a rule
arrives off the wire as itself — the parts a compound is made of included, each read back by its own word. A
game's own pattern travels the way the ones stated here do, since a word is claimed by writing the class
rather than by joining a list in this package.

What that buys is a rule in a cursor. A game may carry a `Combination` in its own state — the combination a
trick stands on, held as its pattern, its cards and its place, rather than as a count of cards to be read
off the table again — and a `Ranking` settled at the table, a bid contract or a rank named wild mid-hand,
travels and replays as the ranking it was.

**Models where a value is validated or sent, records where it is working material.** `Pattern`, `Combination`,
`Evaluation`, `Ranking` and `Scoring` are Pydantic models: each holds an invariant to check or travels in game
state, so `SameRank(places=1)` is refused at the boundary and a dump of a ranking carries its rules. `Demand`,
`Shape`, `Tally` and `Filling` are frozen dataclasses: they are built by this package out of values already
checked, they answer one question and are dropped, and a question about a full house builds nine hundred of
them, which a model's validation would double the cost of. The one invariant a reading carries of its own — a
place reading apart one way — `Shape.__post_init__` holds it to, at the cost of one pass over the spreads the
reading states.

---

## 2. The vocabulary

### Four rules that stand on their own

| pattern | the rule | shapes it admits |
|---|---|---|
| `SameRank(places=n)` | *n* places one rank fills | one per rank |
| `SameSuit(places=n)` | *n* places one suit fills | one per suit |
| `Run(places=n)` | *n* places consecutive ranks fill | one per stretch, the wheel besides |
| `AnyCards(places=n)` | *n* places any card fills | one |

Each of them states its rule in a module of its own under `combinations/patterns/`, so a rule is read, changed
or added one file at a time.

### Two ways to make a rule of others

`Together(parts=...)` reads one set of places by every part at once, so each place asks what all the parts
ask of it. `Beside(parts=...)` holds the places of every part one after another, each part keeping ranks and
suits of its own — which is what makes three of a rank beside two of a rank a full house rather than five
of one rank.

Poker then reads as the rules of poker:

```python
HIGH_CARD = AnyCards(places=1)
PAIR = SameRank(places=2)
TRIPLET = SameRank(places=3)
QUADRUPLET = SameRank(places=4)
TWO_PAIR = Beside(parts=(PAIR, PAIR))
FULL_HOUSE = Beside(parts=(TRIPLET, PAIR))
STRAIGHT = Run(places=5)
FLUSH = SameSuit(places=5)
STRAIGHT_FLUSH = Together(parts=(STRAIGHT, FLUSH))
```

A pattern says itself in words, so `str(FULL_HOUSE)` reads `3 of a rank beside 2 of a rank`. Several decks
in play let a rule reach further, and `SameRank(places=5)` is five of a rank.

### A rule whose places read apart

Several decks also let one card answer two places asking alike, so `SameRank(places=2)` reads the king of
spades held twice as a pair. Many games want the pair to hold two *suits*: same rank, cards of their own.
`Apart` states the rule of another pattern with each of its places taking a facing of its own, and poker reads
a second time:

```python
APART_PAIR = Apart.of_suit(PAIR)  # two of a rank, showing two suits
APART_TRIPLET = Apart.of_suit(TRIPLET)
APART_QUADRUPLET = Apart.of_suit(QUADRUPLET)
APART_TWO_PAIR = Beside(parts=(APART_PAIR, APART_PAIR))
APART_FULL_HOUSE = Beside(parts=(APART_TRIPLET, APART_PAIR))
APART_FLUSH = Apart.of_rank(FLUSH)  # five of a suit, showing five ranks
```

The size, the strength and the readings are the part's own, so `str(APART_PAIR)` reads `2 of a rank apart by
suit` and a pair of kings is placed by its rank as ever. `STRAIGHT` and `STRAIGHT_FLUSH` stand as they are,
each of their places asking for a rank of its own already. `APART_POKER` and `APART_POKER_ORDER` are the ranking
of these rules, beside `POKER`, which stays the single-deck canon — so a game states which of the two it is
played by, and a hand whose triplet leans on a card held twice answers the apart ranking with the two pair its
suits reach.

**A facet is what a place holds of its own.** `Apart.of_card` holds each place to a card the other places of
the rule left, `of_rank` to a rank of its own and `of_suit` to a suit of its own. Over one rank a card of one's
own and a suit of one's own ask the same thing, and over one suit a card of one's own and a rank of one's own
do. They part where a rule reaches over several ranks and several suits at once, which is what tells two pair
holding four suits from two pair each of whose four cards is its own card.

**A spread by rank or by suit reads over places asking alike.** Where the places ask alike, every card of one
facing answers every one of them and the filling settles which card takes which place. So `Apart.of_suit(PAIR)`
stands and `Apart.of_suit(TWO_PAIR)` is refused where it is written, two pair asking one rank of two places and
another rank of the other two: the rule that holds four suits across both pairs is
`Beside(parts=(APART_PAIR, APART_PAIR))`, each pair holding two of its own. Reading apart by card holds a place
to a card of its own whatever that place asks for, so `Apart.of_card(TWO_PAIR)` stands as well, and it reads
four cards each of them its own. A rule already holding places apart is refused a second spread over them,
since a place reads apart one way.

### A rule read back by its word

Seven words are in play — `any_cards`, `apart`, `beside`, `run`, `same_rank`, `same_suit`, `together` — one per
concrete pattern above, and a game writing an eighth puts its own word in play by writing the class:

```python
FULL_HOUSE.model_dump()
# {"kind": "beside", "parts": ({"kind": "same_rank", "places": 3}, {"kind": "same_rank", "places": 2})}

APART_PAIR.model_dump_json()
# {"kind": "apart", "part": {"kind": "same_rank", "places": 2}, "facet": "suit"}

Ranking.model_validate_json(POKER.model_dump_json()) == POKER  # True
```

Three refusals hold a word to one rule. A concrete pattern stating no word of its own is refused as the
class is written, and so is one claiming a word another pattern already travels under — both as a
`TypeError`, since a rule that cannot be read back is a mistake in the code rather than in the data. A wire
form naming a word no pattern in play states is refused where it arrives, saying which words are known.

`Pattern.named(kind)` is the same lookup, for a game that reads a word a client sent.

### Shape and Demand

A `Shape` is one reading a pattern admits, stated as what each of its places asks for. A `Demand` is that
question at one place: a rank alone asks for any card of that rank, a suit alone for any card of that suit,
both together for the one card holding both, and neither for any card at all.

Demands meet: `Demand.of_rank(KING).meet(Demand.of_suit(SPADE))` asks for the king of spades, and two ranks at
one place meet nowhere, which is how a run read together with a flush of another suit comes to admit no
reading. `Shape.together` is that meeting place by place and `Shape.beside` is concatenation, which is the
whole of what the two compound patterns do with the shapes of their parts.

A `Spread` is the other thing a reading states: the places it holds apart, beside the `Facet` each of them
takes of its own — the card, its rank or its suit. A demand asks a place for a card of the deck and a spread
holds a place to what the other places of that spread left, so the two together are the whole of what a
reading says, and `Apart` is the pattern that states one. A reading carries its spreads the way it carries its
demands: `Shape.beside` shifts each part's spread onto the places that part takes in the run of them, and
`Shape.together` carries them as they stand, every part reading the same places. Every place reads apart in
one spread at the most, which a reading is held to where it is built, and `spreading()` reads that back the
way the filling asks it — the spread standing at each place.

### Evaluation

| field | what it states |
|---|---|
| `ranks` | the sequence a run follows and the strength a rank carries, lowest first |
| `suits` | the strength a suit carries, lowest first |
| `wheel` | whether a run turns at the top rank and continues from the lowest |
| `wild_jokers` | whether a joker stands in for what a combination asks |
| `duplicates` | whether one card held twice counts twice |

`REGULAR_EVALUATION` is the common reading: two up to ace, clubs up to spades, the wheel admitted, jokers
wild, and copies counted.

**Several decks in play.** `Duplicates.COUNT` reads each copy as itself, so two two of diamonds beside one
three of diamonds are three diamonds. `Duplicates.COLLAPSE` reads a repeated card once, so the same three
cards are two diamonds. A repeated rank lengthens no run either way, since a run asks each of its places
for a rank of its own.

Which of the two a game reads by is a statement about the whole deck, and a rule may hold its own places apart
besides: a game where a pair shows two suits while a triplet still admits three copies of a card counts copies
and states the pair as `Apart.of_suit(PAIR)`, which §2 is about. Where a reading collapses repeats, every card
of a hand faces apart from every other and a rule read apart asks what the rule it reads asks.

**The runs a reading admits.** `stretches(size)` lists every run of that many consecutive ranks, the
highest-topped first, and the wheel stands among them where the reading turns — ten of them at five cards
over the regular deck. A game enumerating runs of its own reads them from there, so the wheel and the rank
order stay one statement.

### Combination

A `Combination` is one instance: the cards that make it beside what each of them reads as.

```python
found = find((SEVEN_OF_SPADES, SEVEN_OF_HEARTS, RED_JOKER), TRIPLET, REGULAR_EVALUATION)

found.cards  # (7♠, 7♥, *♥)
found.reading  # (7♠, 7♥, 7♦)
found.strength  # (5,) — the place of the seven
found.low_ace  # False
```

`reading[place]` answers for `cards[place]`, so a game can tell which card played which part.

---

## 3. How a question is answered

The cards are tallied once — indexed by rank and by suit, strongest first — and then each shape the pattern
admits is *filled* rather than searched for. Filling a shape is one question: can the held cards take these
places, and which of them where?

**Every card that can hold a place holds one.** The cards and the places make a table of who answers what,
and the filling gives out as many places as any assignment could give out: a card takes a place already
held whenever its holder can move on to another, and that chain of moves reaches every place such a
rearrangement opens. So a pair of kings beside three spades is read out of `K♦ K♥ K♠ Q♠ J♠` — the king of
spades gives its place in the pair to the king of diamonds and joins the flush.

**The strongest cards are the ones held.** The cards are offered from the strongest downwards and a card
once placed keeps a place, so the reading holds the strongest cards the shape can hold at once.

**A joker covers what the cards leave, and improves what they hold.** Each place the cards cannot reach
falls to a joker, and the shape falls short exactly where the jokers run out. A joker to spare then takes a
place from the card standing there wherever the reading it makes stands stronger by the pattern's own
measure — which is what turns two low spades and two jokers into an ace-high flush and what leaves two
natural kings holding their own pair.

A joker reads as the strongest card its place admits and the reading has yet to name, so two kings and two
jokers read `K♠ K♥ K♦ K♣` and three jokers read three aces.

**Places that read apart take cards facing apart.** A place inside a spread is reached through the gate that
spread keeps for the facing a card shows, and a gate carries one card at a time, so two copies of the king of
spades reach one place of a pair read apart by suit between them and the filling settles which of them takes
it. Gates are a second resource of the same matching, so the two statements above stand as they are: as many
places are filled as any assignment could fill, and the strongest cards are the ones held. A joker at an open
place of a spread reads as the strongest card its demand admits whose facing the spread leaves free, and the
shape falls short where those facings run out — which is what four suits do to five of a rank read apart by
suit, however many jokers stand behind it.

### What a question costs

| pattern | shapes |
|---|---|
| loose places | 1 |
| a pair, a triplet, a quadruplet | 13, one per rank |
| two pair | 78, one per pair of ranks |
| a full house | 156, one per ordered pair of ranks |
| a flush | 4, one per suit |
| a run of *n* | 14 − *n*, and the wheel besides |
| a suited run of *n* | four times that |
| a pair beside loose places | 13 |
| any of them read apart | the same count |

A spread leaves that count as it stands: a pair holding two suits is the thirteen shapes a pair is, and reading
places apart is a question the filling answers as it hands out the places.

Filling one shape reads the cards once for each place and rearranges no further than the places reach, so a
hand of seven cards and a hand of fifty-two cost the same question. No subset of a hand is ever enumerated,
which is what makes the answer affordable where a game asks on every move.

`find_all` returns one instance per shape, which is what makes it a list a person can read: three kings
hold *the pair of kings*, once, rather than one pair per way of choosing two of them.

```python
find_all((KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS), PAIR, REGULAR_EVALUATION)
# one instance, reading (K♠, K♥)
```

A set of cards answers to every pattern it forms: five spades in a row are a straight, a flush and a
straight flush alike. Which of the three a hand counts as is what a ranking states.

---

## 4. Strength and ranking

Strength is the pattern's own statement, and it reads the ranks of an instance:

- `SameRank` reads the rank it holds, so a pair is settled by its rank;
- `SameSuit` and `AnyCards` read their ranks from the highest down, which settles a flush by the high cards
  it shows and a run of loose places by its cards in turn;
- `Run` reads the card that tops it, and the wheel is topped by its five, so it stands below a six-high
  straight;
- a pattern made of parts keys on its parts **in the order it names them**;
- `Apart` reads as the rule it holds apart, so a pair of two suits is settled by its rank as any pair is.

That last rule is why a full house of twos over aces stands below one of threes over kings: `FULL_HOUSE`
names its triplet first. It is also why `Beside(parts=(PAIR, AnyCards(places=3)))` compares two hands by
their pair and then by the cards standing around it, which is what poker calls kickers.

Two instances reading one key stand alongside each other — two pairs of kings are equal, and a game that
separates them by suit states that rule itself.

A `Ranking` lists the patterns a game recognises, weakest first, beside the reading it finds them by:

```python
POKER = Ranking(
    patterns=(
        HIGH_CARD,
        PAIR,
        TWO_PAIR,
        TRIPLET,
        STRAIGHT,
        FLUSH,
        FULL_HOUSE,
        QUADRUPLET,
        STRAIGHT_FLUSH,
    ),
    evaluation=REGULAR_EVALUATION,
)
```

`APART_POKER` names the same nine rules with each rule that asks alike of its places read apart (§2) — the pair,
the triplet, the quadruplet and the flush — so two pair and the full house are built of those, and the high
card, the straight and the straight flush stand as they are. It is the ranking a game of several decks holds up
where a pair means two suits, and a hand answers whichever of the two it is held to. The count it answers at
follows: five cards whose triplet leans on a card held twice are a full house under `POKER` and two pair under
`APART_POKER`, so they stand in the contest of four cards there.

**`strongest` takes cards and `order` takes combinations.** A hand is a run of cards, and `strongest`
reads one and answers with the `Combination` it forms — the pattern it answers, the cards that make it, and
its strength within that pattern. That combination is what the order compares, since a run of cards alone
says nothing about which of the patterns it is being counted as:

```python
mine = POKER.strongest((SEVEN_OF_SPADES, SEVEN_OF_HEARTS, TWO_OF_CLUBS))  # 2 of a rank: 7♠ 7♥
yours = POKER.strongest((KING_OF_SPADES, QUEEN_OF_HEARTS))  # any card: K♠

POKER.order.compare(mine, yours)  # 1 — a pair over a high card
POKER.order  # a Preorder[Combination]: pattern first, strength within it
```

A hand forming none of the patterns a ranking names answers `None`, so a table is read into combinations
before it is ordered:

```python
best = [POKER.strongest(seat) for seat in table]
POKER.order.argmaxima(best)  # every seat that shares the top
```

`order` is a `Preorder` from `cardwork.ordering.preorder`, so comparing two combinations and picking the
winners out of a table are calls it already carries. A combination whose pattern the ranking leaves out
raises `KeyError`, which keeps a ranking's answer to the patterns it names.

### One winner every time

`order` holds two pairs of kings alongside each other, since strength is stated in ranks. A game that needs
a winner out of every contest asks `total_order`, which refines that order with `ByReading` — the cards a
combination reads as, the strongest first, each placed by rank and then by suit as the evaluation places
them:

```python
POKER.total_order  # pattern, then strength, then the cards themselves
POKER_ORDER  # the same order over the regular reading of the deck

mine = POKER.strongest((KING_OF_SPADES, KING_OF_HEARTS, TWO_OF_CLUBS))
yours = POKER.strongest((KING_OF_DIAMONDS, KING_OF_CLUBS, THREE_OF_CLUBS))

POKER.order.compare(mine, yours)  # 0 — two pairs of kings
POKER_ORDER.compare(mine, yours)  # 1 — the spade settles it
```

This runs the fifty-two single cards by rank and then by suit, the seventy-eight pairs above them the same
way, and so on up the patterns: every one of the 22175 combinations a standard deck forms under `POKER`
takes a place of its own. Reading is what a place answers to, so a joker standing in for the king of hearts
takes the place the king of hearts takes, and several decks in play let two combinations read the same cards
and stand alongside each other.

Being a refinement, it settles ties and leaves the ranking's own rule standing: a pair of fives still beats
the ace of spades alone, and a full house of twos over aces still stands below one of threes over kings.

### The questions a table asks

A ranking is what a game holds up against the table in front of it, so the questions a round asks of the
cards are asked of the ranking:

| asked | answers |
|---|---|
| `sizes()` | the counts a combination of this ranking takes, fewest first |
| `sized(size)` | the ranking made of the patterns taking that many cards |
| `strongest(cards)` | the best combination the cards form, cards to spare admitted |
| `exactly(cards)` | the combination the cards *are*, every one of them taking a place |
| `climbs(challenger, held)` | whether the challenger takes as many cards and stands above |
| `ceilings(deck)` | the strongest combination each count reaches out of a deck |
| `selections(cards)` | every set of places among the cards that reads as a combination |

**`exactly` holds the cards to being the whole of it.** `strongest` welcomes cards to spare, so four kings
read there as the triplet of a ranking that lists one, and a game admitting the combination a seat played and
nothing besides would take four of a kind for three. `exactly` asks only the patterns of the count it was
handed, and answers `None` where the run is a combination with a card left over.

**A count is a contest of its own.** `climbs` carries that clause: a combination of another count stands
beside the one held rather than over it, and standing above means above in `total_order`, so every contest
between two of a count is settled. `sized(size)` is the ranking a seat answering that count is held to, and
`sizes()` is what a count arriving from a client is read against — `sized` refuses a count no pattern takes,
saying which counts are taken.

**`ceilings` answers what cannot be climbed over.** The strongest combination each count reaches out of a
whole deck. A game asking whether the best of a count has already been played reads it from here:

```python
POKER.ceilings(standard_deck())
# 1: any card: A♠
# 2: 2 of a rank: A♠ A♥
# 3: 3 of a rank: A♠ A♥ A♦
# 4: 4 of a rank: A♠ A♥ A♦ A♣
# 5: a run of 5 together with 5 of a suit: 10♠ J♠ Q♠ K♠ A♠
```

### Every combination a hand can play

`selections` is the question a list of legal moves is made of. A move names its cards by where they stand in
the hand the seat was shown, so what a game enumerating moves needs is sets of *places*:

```python
POKER.selections((KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS))
# {0, 1, 2}, {0, 1}, {0, 2}, {1, 2}, {0}, {1}, {2}
# the triplet, then its three pairs, then its three high cards
```

This is the one question in the package that counts a hand's subsets rather than a pattern's readings, and
the cards left behind are the reason. `find_all` reads three kings as *the pair of kings*, once, because one
instance per reading is what a person wants to read; three pairs are three moves, since each leaves a
different king in hand and that is the whole of the decision. The strongest patterns lead, and each set of
places comes out once however many patterns it answers.

A rule read apart offers the places whose cards face apart, which is the same rule the filling reads by: a hand
holding the king of spades twice beside the king of hearts offers a pair read apart by suit two ways, each copy
of the spades standing beside the hearts.

What a game gets by asking is that its move list and its rules are one statement: a pattern added to the
ranking is offered from the next move onwards, with no enumerator of its own to keep in step.

---

## 5. Points

`Scoring` counts what a combination is worth. Pips count their face and jack through ace count ten, which
`cardwork.cards.points` states; the one rank that changes worth with its company is the ace of a run:

```python
REGULAR_SCORING.of(find(wheel, STRAIGHT, REGULAR_EVALUATION))  # 1 + 2 + 3 + 4 + 5
REGULAR_SCORING.of(find(broadway, STRAIGHT, REGULAR_EVALUATION))  # 10 × 5
```

Counting reads the combination's reading, so a joker standing in for the four of hearts is worth four.

---

## 6. What a game states for itself

**A game of four cards** (`cardgames.backend.passing`) declares a win on three cards of one rank or one suit while
the four are not alike. That is four questions over the same hand:

```python
TRIPLET = SameRank(places=3)
THREE_OF_A_SUIT = SameSuit(places=3)

contains(hand, TRIPLET, evaluation) or contains(hand, THREE_OF_A_SUIT, evaluation)
matches(hand, SameRank(places=4), evaluation) or matches(
    hand, SameSuit(places=4), evaluation
)
```

Its evaluation counts copies, since several standard decks are in play and three spade cards are three of a
suit even where two of them are the same spade. A game wanting three ranks of the suit instead states that in
the rule — `Apart.of_rank(THREE_OF_A_SUIT)` — and keeps the reading of the deck as it is.

**A game of single cards** (`cardgames.backend.showdown`) compares one card against another and needs one winner
every time, so it reads `REGULAR_ORDER` from `cardwork.cards.order` and asks this package nothing.

**A game of matched sets** (`cardgames.backend.shedding`) asks one question of a selection a player made, at a
size the selection decides:

```python
matches(
    named, SameRank(places=len(named)), evaluation
)  # two of a rank, three of one, four of one
```

A pattern built per question is what lets one line stand for a pair, a triplet and four of a rank alike, and
`matches` is the reading that holds the cards to being the whole of it — a selection with a card of another rank
in it answers to no size at all. Its evaluation leaves jokers unwild, since the one standard deck it is played
with holds none.

**A game of climbing combinations** (`cardgames.backend.climbing`) recognises eight patterns across four
counts — one card, a pair, a triplet, and five cards reading as a straight, a flush, a full house, four of a
rank beside any card, or a straight flush — and a seat answering the table is held to the count standing on it.
Four of the questions above are the whole of its card rules:

```python
CLIMBING_RANKING.selections(hand)  # every combination a seat on lead can put down
CLIMBING_RANKING.sized(on_table.pattern.size).selections(hand)  # the answers to what stands there
CLIMBING_RANKING.exactly(played)  # the combination those cards are, or none
CLIMBING_RANKING.climbs(played, on_table)  # whether it stands above what it answers
```

**A ranking answers for the patterns it names, at the counts those take.** This one names nothing of four
cards, so four cards read as a combination in no way at all: `sizes()` answers `1, 2, 3, 5`, `sized(4)` says
which counts are taken instead of guessing at one, and a play of four is refused as a combination this game is
played by. The counts it does name reach these:

```python
CLIMBING_RANKING.ceilings(standard_deck())
# 1: any card: A♣
# 2: 2 of a rank: A♣ A♠
# 3: 3 of a rank: A♣ A♠ A♥
# 5: a run of 5 together with 5 of a suit: 10♣ J♣ Q♣ K♣ A♣
```

It reads the deck by the German suit order — diamonds, hearts, spades, clubs, weakest first — with the wheel
admitted, jokers unwild since its one deck holds none, and copies collapsed. So the ace of clubs stands at the
head of every count it names, and the two of diamonds is the one card every other card in the deck climbs over,
which is the card that game opens on (`docs/games/climbing.md` §1).

A game states its own evaluation, its own patterns and its own ranking. What it inherits is the reading:
one tally per question, one instance per shape, and a strength it can compare, order and score.
