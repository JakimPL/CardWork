# Combinations

`cardwork.combinations` reads a run of cards and answers what it is: whether these four cards are three of
a suit, whether a seven-card hand holds a full house, which of two hands wins, and what a combination is
worth in points. It works on cards alone — no zones, no seats, no turn — so a game consults it wherever it
needs to know, and two games with different rules consult it with different readings.

The package is the answer to one question asked four ways:

```python
matches(cards, pattern, evaluation)   # are these cards that combination, all of them?
contains(cards, pattern, evaluation)  # do these cards hold it somewhere?
find(cards, pattern, evaluation)      # the strongest instance of it they hold
find_all(cards, pattern, evaluation)  # every instance, strongest first
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

Because a pattern is a rule and not a record, a dump of one carries the parts it is made of, and reading a
pattern back out of a dump is the affair of whatever names the rules it uses. Game state holds the cards and
the score; a pattern is what a game consults about them.

**Models where a value is validated or sent, records where it is working material.** `Pattern`, `Combination`,
`Evaluation`, `Ranking` and `Scoring` are Pydantic models: each holds an invariant to check or travels in game
state, so `SameRank(places=1)` is refused at the boundary and a dump of a ranking carries its rules. `Demand`,
`Shape`, `Tally` and `Filling` are frozen dataclasses: they are built by this package out of values already
checked, they answer one question and are dropped, and a question about a full house builds nine hundred of
them — which validation would double the cost of for nothing to check.

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
HIGH_CARD       = AnyCards(places=1)
PAIR            = SameRank(places=2)
TRIPLET         = SameRank(places=3)
QUADRUPLET      = SameRank(places=4)
TWO_PAIR        = Beside(parts=(PAIR, PAIR))
FULL_HOUSE      = Beside(parts=(TRIPLET, PAIR))
STRAIGHT        = Run(places=5)
FLUSH           = SameSuit(places=5)
STRAIGHT_FLUSH  = Together(parts=(STRAIGHT, FLUSH))
```

A pattern says itself in words, so `str(FULL_HOUSE)` reads `3 of a rank beside 2 of a rank`. Several decks
in play let a rule reach further, and `SameRank(places=5)` is five of a rank.

### Shape and Demand

A `Shape` is one reading a pattern admits, stated as what each of its places asks for. A `Demand` is that
question at one place: a rank alone asks for any card of that rank, a suit alone for any card of that suit,
both together for the one card holding both, and neither for any card at all.

Demands meet: `Demand.of_rank(KING).meet(Demand.of_suit(SPADE))` asks for the king of spades, and two ranks at
one place meet nowhere, which is how a run read together with a flush of another suit comes to admit no
reading. `Shape.together` is that meeting place by place and `Shape.beside` is concatenation, which is the
whole of what the two compound patterns do with the shapes of their parts.

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

### Combination

A `Combination` is one instance: the cards that make it beside what each of them reads as.

```python
found = find((SEVEN_OF_SPADES, SEVEN_OF_HEARTS, RED_JOKER), TRIPLET, REGULAR_EVALUATION)

found.cards     # (7♠, 7♥, *♥)
found.reading   # (7♠, 7♥, 7♦)
found.strength  # (5,) — the place of the seven
found.low_ace   # False
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
- a pattern made of parts keys on its parts **in the order it names them**.

That last rule is why a full house of twos over aces stands below one of threes over kings: `FULL_HOUSE`
names its triplet first. It is also why `Beside(parts=(PAIR, AnyCards(places=3)))` compares two hands by
their pair and then by the cards standing around it, which is what poker calls kickers.

Two instances reading one key stand alongside each other — two pairs of kings are equal, and a game that
separates them by suit states that rule itself.

A `Ranking` lists the patterns a game recognises, weakest first, beside the reading it finds them by:

```python
POKER.strongest(hand)     # the best combination the hand forms
POKER.order()             # a Preorder[Combination]: pattern first, strength within it
POKER.order().compare(mine, yours)
POKER.order().argmaxima(hands)   # every seat that shares the top
```

`order()` is a `Preorder` from `cardwork.ordering.preorder`, so comparing two hands and picking the winners
out of a table are calls it already carries. A combination whose pattern the ranking leaves out raises
`KeyError`, which keeps a ranking's answer to the patterns it names.

---

## 5. Points

`Scoring` counts what a combination is worth. Pips count their face and jack through ace count ten, which
`cardwork.cards.points` states; the one rank that changes worth with its company is the ace of a run:

```python
REGULAR_SCORING.of(find(wheel, STRAIGHT, REGULAR_EVALUATION))     # 1 + 2 + 3 + 4 + 5
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
matches(hand, SameRank(places=4), evaluation) or matches(hand, SameSuit(places=4), evaluation)
```

Its evaluation counts copies, since several standard decks are in play and three spade cards are three of a
suit even where two of them are the same spade.

**A game of single cards** (`cardgames.backend.showdown`) compares one card against another and needs one winner
every time, so it reads `REGULAR_ORDER` from `cardwork.cards.order` and asks this package nothing.

**A game of matched sets** (`cardgames.backend.shedding`) asks one question of a selection a player made, at a
size the selection decides:

```python
matches(named, SameRank(places=len(named)), evaluation)     # two of a rank, three of one, four of one
```

A pattern built per question is what lets one line stand for a pair, a triplet and four of a rank alike, and
`matches` is the reading that holds the cards to being the whole of it — a selection with a card of another rank
in it answers to no size at all. Its evaluation leaves jokers unwild, since the one standard deck it is played
with holds none.

A game states its own evaluation, its own patterns and its own ranking. What it inherits is the reading:
one tally per question, one instance per shape, and a strength it can compare, order and score.
