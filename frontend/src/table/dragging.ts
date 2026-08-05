import type { CSSProperties, PointerEvent } from "react";

/** Which press takes hold of a card, which is the one a pointer makes of itself. */
const PRESSING = 0;

/** How far a card travels before the hand on it reads as carrying it, which leaves an unsteady press a press. */
const A_PRESS = 4;

/** A card lying where the run draws it, which is what a card nobody is carrying reads as. */
const STILL: Shift = { across: 0, down: 0 };

/** One point of the page, as far across it and as far down it as that point stands. */
export interface Point {
  across: number;
  down: number;
}

/** How far a card stands from the place the run draws it at, which is what carries it under the pointer. */
export type Shift = Point;

/**
 * Where one run draws its places, read off the page as a card of it is taken hold of.
 *
 * A run holds as many places while a card of it is being carried as it held before, and each of them is drawn
 * where it was: what the carry changes is which card lies at which place. So the drawing read once as the card
 * comes up answers the whole gesture, and a pointer standing anywhere is read against it.
 */
export interface Places {
  middles: readonly number[];
  along: number;
}

/**
 * A card in hand: where it came from, where it has reached, where along it the player took hold, how far it
 * stands from the place it is drawn at, and the point the hand on it set out from.
 *
 * The place reached is the run as it is about to lie, and the shift is the card as the player sees it: the two
 * come off one pointer, so a card under the hand and a run opening ahead of it are one reading of one gesture.
 * The point it set out from is what the hand is read against, since a hand that has gone nowhere has pressed the
 * card rather than carried it.
 */
export interface Carry {
  from: number;
  to: number;
  held: Shift;
  by: Shift;
  began: Point;
}

/**
 * How one place of a run is taken hold of and carried, which the run states for each of its places in turn.
 *
 * A card draws itself and answers what a player does to it, so the answers a carry asks for arrive together with
 * the place the card lies at: taking it up, carrying it to where the pointer stands, letting it go there, and
 * having it taken out of the player's hand by the page it was being carried across.
 */
export interface Handling {
  carried: boolean;
  travel: Shift | null;
  grasp: (at: Point) => void;
  carry: (at: Point) => void;
  release: (at: Point) => void;
  abandon: () => void;
}

/**
 * What one place of a run answers of being taken hold of, which is the whole of what a carry is worked by.
 *
 * A card follows the pointer that took hold of it, so the pointer is held to that card for as long as the press
 * lasts and every point it stands at reaches the card wherever the card has been carried to. A place of a run
 * nobody orders answers none of it, which leaves the card lying where the table holds it.
 */
export interface Grasped {
  style?: CSSProperties | undefined;
  onPointerDown?: ((event: PointerEvent<HTMLElement>) => void) | undefined;
  onPointerMove?: ((event: PointerEvent<HTMLElement>) => void) | undefined;
  onPointerUp?: ((event: PointerEvent<HTMLElement>) => void) | undefined;
  onPointerCancel?: (() => void) | undefined;
}

/** The place of a run one point stands at, which is the place whose middle it lies nearest. */
export function nearest(middles: readonly number[], across: number): number {
  let nearby = 0;
  let closest = Number.POSITIVE_INFINITY;
  middles.forEach((middle, place) => {
    const away = Math.abs(across - middle);
    if (away < closest) {
      closest = away;
      nearby = place;
    }
  });

  return nearby;
}

/** The card at one place taken hold of at one point, which leaves the run lying as the table holds it. */
export function grasped(place: number, places: Places, at: Point): Carry {
  return { from: place, to: place, held: from(at, places, place), by: STILL, began: at };
}

/**
 * The card in hand as the pointer stands now: the place it has reached, and how far it stands from that place.
 *
 * The place it has reached is the one the pointer lies nearest, so a card comes to rest where the player has
 * carried it and the cards it passed over close up behind it. It is drawn from there under the pointer by the
 * same hold it was picked up by, which is what keeps the card under the hand for the whole of the carry.
 *
 * Nothing is carried where nothing was taken hold of.
 */
export function carriedTo(carrying: Carry | null, places: Places, at: Point): Carry | null {
  if (carrying === null) {
    return null;
  }

  const to = nearest(places.middles, at.across);
  const stood = from(at, places, to);
  return {
    from: carrying.from,
    to,
    held: carrying.held,
    by: { across: stood.across - carrying.held.across, down: stood.down - carrying.held.down },
    began: carrying.began,
  };
}

/** Whether the card has come to lie elsewhere than where it was taken from, which is what there is to lay down. */
export function moved(carrying: Carry): boolean {
  return carrying.from !== carrying.to;
}

/**
 * Whether the hand on a card has carried it, which is what tells a card being sorted from a card being pressed.
 *
 * The hand is read against the point it set out from rather than against the place the card is drawn at, since a
 * card carried a whole place along stands under the hand that took it and so lies barely off the place it reached.
 * A hand that has gone as good as nowhere has pressed the card, which leaves a run a player also plays out of
 * answering a press and a carry both.
 */
export function travelled(carrying: Carry, at: Point): boolean {
  return Math.abs(at.across - carrying.began.across) > A_PRESS || Math.abs(at.down - carrying.began.down) > A_PRESS;
}

/**
 * One run as a card carried through it lays it out, which is the order that run comes to lie in.
 *
 * The card is lifted out of the run and put back where it was carried to, so the cards it passed over close up
 * behind it and it comes to lie at the place it was let go at. This is the one reading of a carry: a player
 * carrying a card is reading the run this answers with, and letting it go sends the order they were reading.
 *
 * A run lying as it lies is the answer where no card is being carried, and where the place a card was taken from
 * is one the run holds none at.
 */
export function laidOut<T>(run: readonly T[], carrying: Carry | null): T[] {
  const held = carrying === null ? undefined : run[carrying.from];
  if (carrying === null || held === undefined) {
    return [...run];
  }

  const rest = [...run.slice(0, carrying.from), ...run.slice(carrying.from + 1)];
  return [...rest.slice(0, carrying.to), held, ...rest.slice(carrying.to)];
}

/**
 * The order letting a carried card go sends, and none where the run stands as the table already holds it.
 *
 * A player reads the run as it lies in front of them, so the order they send by letting go is the one they have
 * been reading: it is theirs to send from wherever on the page the card is let go, since the run they are
 * answering is the run they can see. A card carried home again lies at the place it was taken from, which leaves
 * the run the table's own and nothing to send.
 */
export function sent<T>(run: readonly T[], carrying: Carry | null): T[] | null {
  return carrying !== null && moved(carrying) ? laidOut(run, carrying) : null;
}

/** What a card answers of a carry, out of the handling the run it lies in states for its place in that run. */
export function handled(handling: Handling | null): Grasped {
  if (handling === null) {
    return {};
  }

  return {
    style: lifted(handling.travel),
    onPointerDown: (event) => {
      if (event.button !== PRESSING) {
        return;
      }

      event.currentTarget.setPointerCapture(event.pointerId);
      handling.grasp(pointing(event));
    },
    onPointerMove: (event) => {
      handling.carry(pointing(event));
    },
    onPointerUp: (event) => {
      handling.release(pointing(event));
    },
    onPointerCancel: handling.abandon,
  };
}

/** Where the pointer stands, as the page reads a press travelling across it. */
function pointing(event: PointerEvent<HTMLElement>): Point {
  return { across: event.clientX, down: event.clientY };
}

/** A card drawn where it has been carried to, and drawn where the run puts it while nobody carries it. */
function lifted(travel: Shift | null): CSSProperties | undefined {
  return travel === null ? undefined : { transform: `translate(${travel.across}px, ${travel.down}px)` };
}

/** How far one point stands from where the run draws one of its places, and nowhere from a place it draws none at. */
function from(at: Point, places: Places, place: number): Shift {
  const middle = places.middles.at(place);
  return middle === undefined ? STILL : { across: at.across - middle, down: at.down - places.along };
}
