import type { AnyAction, Move } from "./moves";

/**
 * What a client is served of a table, stated by hand because the answers carry the game's own state.
 *
 * `/view` and `/events` are generic in the state a game declares, so they publish no schema and these mirror
 * `cardwork.views` instead. Everything a particular game adds to its cursor arrives inside `state`, which the
 * layout's readouts name the fields of.
 */
export type ZoneId = string;

/** One card of a standard deck, whose suit is the glyph it draws as. */
export interface Card {
  rank: string;
  suit: string;
}

/** The card standing for any other, which a game reads as whatever it needs. */
export interface Joker {
  red: boolean;
}

export type CardOrJoker = Card | Joker;

/** A card as it lies on the table: the card itself, and which way up it is. */
export interface GameCard {
  card: CardOrJoker;
  face_down: boolean;
}

/**
 * One place in a zone: the card an observer reads there, or a placeholder standing for one it may not.
 *
 * A placeholder keeps the index of the card it conceals, so the fifth place of a hand names the same card to
 * the client and to the server and a move addressing it lands where the player aimed.
 */
export type ProjectedCard = GameCard | null;

/**
 * The rules cursor as an observer reads it: the three fields every game shares, and its own besides.
 *
 * A readout names one of those fields, which is how a figure a particular game keeps reaches the screen
 * without this interface holding the name of it.
 */
export interface Cursor {
  phase: string;
  to_act: number[];
  points: number[] | null;
  [field: string]: unknown;
}

/**
 * One zone as an observer reads it, at the true position of every card in it.
 *
 * `arrangeable` is this observer's own answer to whether it may lay the zone out as it pleases, which the table
 * resolves for the same reason it narrows the cards: what a client may do arrives from the table rather than
 * being worked out from what it was served.
 */
export interface ZoneView {
  id: ZoneId;
  owner: number | null;
  arrangeable: boolean;
  cards: ProjectedCard[];
}

/**
 * Everything one observer is entitled to know about a position, stamped with the sequence it stands at.
 *
 * `seq` counts the commits the table holds, so it is both what the next commit is numbered and what a client
 * quotes as `base_seq` to pin a move to the position it was weighed against.
 */
export interface PositionView {
  observer: number | null;
  seq: number;
  zones: Record<ZoneId, ZoneView>;
  state: Cursor;
  legal: Move[];
}

/** The move behind a commit, narrowed to what one observer may know of it. */
export interface MoveView {
  player: number;
  action: AnyAction | null;
}

/** How one zone read before a commit and how it reads after, both as this observer sees them. */
export interface ZoneChange {
  zone: ZoneId;
  before: ProjectedCard[];
  after: ProjectedCard[];
}

/**
 * One commit as it reaches one observer: who acted, what it changed, and the cursor and options it left.
 *
 * `seq` is the number the commit itself took, which stands one behind the count a view holds: a client that
 * has applied the commit numbered `seq` stands at `seq + 1` commits.
 */
export interface EventView {
  seq: number;
  observer: number | null;
  move: MoveView | null;
  changes: ZoneChange[];
  state: Cursor;
  legal: Move[];
}
