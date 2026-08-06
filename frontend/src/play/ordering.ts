import type { ProjectedCard } from "../api/views";

/** What a hand is put in order by, which is every card of it read by its rank or by its suit. */
export type Ordering = "rank" | "suit";

/** Which end of an order a run reads from, the lowest card of it first or the highest. */
export type Direction = "up" | "down";

/**
 * One card of a zone at the position it lies at, which is the position an order names it by.
 *
 * A run is read in the order it lies in front of the player and sent as the positions the zone holds its cards at,
 * so an order laid down by hand and an order a press asks for reach the table as the one thing.
 */
export interface Lying {
  index: number;
  card: ProjectedCard;
}

/**
 * The ranks and the suits in the order a hand put in order reads them, which is this interface's own to state.
 *
 * Sorting a hand is a convenience of the page: a player asks for their cards in an order they can read across, and
 * the table is told the order they came to lie in and nothing of why. So a rank reads by the deck as it is spelled,
 * the low card of it first, and a suit by the order the deck declares them in, which stands a red suit either side
 * of a black one. A game that ranks cards by a reckoning of its own ranks them where it weighs its moves.
 */
const RANK_SEQUENCE: readonly string[] = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"];
const SUIT_SEQUENCE: readonly string[] = ["♠", "♥", "♣", "♦"];

/** Where a card these sequences name no place for stands, which is past every card of the deck. */
const BEYOND = RANK_SEQUENCE.length;

/** Where a place this seat reads no card at stands, which is past even those. */
const LAST = BEYOND + 1;

/** The two ends an order is read from, which one press per ordering carries between them. */
const ASCENDING: Direction = "up";
const DESCENDING: Direction = "down";

/** The two figures a card is weighed by, each the place its own glyph stands at in the sequence naming it. */
interface Figures {
  rank: number;
  suit: number;
}

/**
 * The positions of a run in the order sorting it brings them to, which is what a press on it sends.
 *
 * Cards the order tells apart by nothing — two jokers, or one card of a deck dealt twice — keep the order they lay
 * in, whichever end the run is read from, so a press moves what it has something to say about and nothing besides.
 */
export function orderedBy(run: Lying[], by: Ordering, way: Direction): number[] {
  const read = run.map((lying) => ({ index: lying.index, figures: figuresOf(lying.card) }));
  read.sort((one, other) => compared(one.figures, other.figures, by, way));
  return read.map((lying) => lying.index);
}

/**
 * The direction the next press of one ordering applies, which is upwards until the run reads that way.
 *
 * A player asked for a hand in order asks for it twice: the order itself, and the same order from the other end. So
 * the press carries both and the run in front of them says which is next — a run already reading the way a press
 * would put it is one that press turns round instead, which is the whole of what two presses come to.
 */
export function turnedTo(run: Lying[], by: Ordering): Direction {
  return readsBy(run, by, ASCENDING) ? DESCENDING : ASCENDING;
}

/** Whether a run already reads in one order, which sorting it that way leaves every card of it where it lay. */
function readsBy(run: Lying[], by: Ordering, way: Direction): boolean {
  const order = orderedBy(run, by, way);
  return run.every((lying, place) => order[place] === lying.index);
}

/** How two cards stand against each other under one ordering read from one end of it. */
function compared(one: Figures, other: Figures, by: Ordering, way: Direction): number {
  const apart = rising(one, other, by);
  return way === ASCENDING ? apart : -apart;
}

/** The same, read from the lowest card up: the figure the ordering is named for, and the other breaking its ties. */
function rising(one: Figures, other: Figures, by: Ordering): number {
  switch (by) {
    case "rank":
      return breaking(one.rank - other.rank, one.suit - other.suit);
    case "suit":
      return breaking(one.suit - other.suit, one.rank - other.rank);
  }
}

/** Two cards read as the figure they stand apart by, or as the figure breaking that tie where they stand level. */
function breaking(apart: number, tie: number): number {
  return apart === 0 ? tie : apart;
}

/**
 * The figures one card is read as, which is where its rank and its suit stand in the sequences naming them.
 *
 * A joker stands for whatever the game it is in reads it as, so a display order gives it a place of its own past
 * every card of the deck and leaves two of them lying as they lay. A place holding a card this seat is not served
 * stands after even that, and a hand a player sorts holds none, since a seat reads every card of its own.
 */
function figuresOf(card: ProjectedCard): Figures {
  if (card === null) {
    return { rank: LAST, suit: LAST };
  }

  const face = card.card;
  if (!("rank" in face)) {
    return { rank: BEYOND, suit: BEYOND };
  }

  return { rank: placeIn(RANK_SEQUENCE, face.rank), suit: placeIn(SUIT_SEQUENCE, face.suit) };
}

/** Where one glyph stands in the sequence naming it, and past the deck where the sequence names it no place. */
function placeIn(sequence: readonly string[], glyph: string): number {
  const place = sequence.indexOf(glyph);
  return place === -1 ? BEYOND : place;
}
