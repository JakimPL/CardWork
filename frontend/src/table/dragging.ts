import type { CSSProperties, PointerEvent } from "react";

/** Which press takes hold of a card, which is the one a pointer makes of itself. */
const PRESSING = 0;

/** How far a hand travels before it reads as carrying the card it pressed, which leaves a click a click. */
const A_PRESS = 6;

/** A card lying where the run draws it, which is what a place the run draws none at reads as. */
const STILL: Shift = { across: 0, down: 0 };

/** Which children of a run are the places it draws, which is every card lying in it. */
const DRAWN = ":scope > .card";

/** What the reach of a card divides by to stand at the middle of it, which lies midway along either side. */
const MIDWAY = 2;

/** Which of the places covering one point the hand on it rests on, which is the one drawn over the others. */
const LAST = -1;

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
 *
 * The reach of a card is the same at every place, since one run draws one size of card, and it is what says
 * which of those places a point stands over.
 */
export interface Places {
  middles: readonly number[];
  along: number;
  reach: Point;
}

/**
 * A card in hand: where it came from, where it has reached, where along it the player took hold, how far it
 * stands from the place it is drawn at, and the point the hand on it set out from.
 *
 * The place reached is the run as it is about to lie, and the shift is the card as the player sees it: the two
 * come off one pointer, so a card under the hand and a run opening ahead of it are one reading of one gesture.
 * A card stands off its place by nothing at all while the hand holding it has yet to travel, which is what
 * leaves a click a click: the point the hand set out from is what that is read against.
 */
export interface Carry {
  from: number;
  to: number;
  held: Shift;
  by: Shift | null;
  began: Point;
}

/**
 * How one place of a run is taken hold of and carried, which the run states for each of its places in turn.
 *
 * A card draws itself and answers what a player does to it, so the answers a carry asks for arrive together with
 * the place the card lies at: taking it up, carrying it to where the pointer stands, letting it go there, and
 * having it taken out of the player's hand by the page it was being carried across.
 *
 * A card let go under the hand that laid it stands raised where it came to rest, and stands so until the hand
 * comes off it, which is the last of the answers a place states.
 */
export interface Handling {
  carried: boolean;
  laid: boolean;
  travel: Shift | null;
  grasp: (at: Point) => void;
  carry: (at: Point) => void;
  release: (at: Point) => void;
  abandon: () => void;
  leave: () => void;
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
  onPointerLeave?: (() => void) | undefined;
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
  return { from: place, to: place, held: from(at, places, place), by: null, began: at };
}

/**
 * The card in hand as the pointer stands now: the place it has reached, and how far it stands from that place.
 *
 * The place it has reached is the one the middle of the card lies nearest, which is where the player is holding
 * that card rather than where the pointer within it stands. So the run opens at the place the card has come to
 * cover, a card taken hold of by any part of itself lies where it lay, and the two readings of one gesture — the
 * card under the hand, the run about to lie — are read off the one figure.
 *
 * A hand that has yet to travel holds the card where the run draws it, and a hand that has travelled carries it
 * for the rest of the press, so an unsteady hand leaves a click a click and a carry stays a carry.
 *
 * Nothing is carried where nothing was taken hold of.
 */
export function carriedTo(carrying: Carry | null, places: Places, at: Point): Carry | null {
  if (carrying === null) {
    return null;
  }

  if (carrying.by === null && !travelled(carrying, at)) {
    return carrying;
  }

  const middle = middleOf(carrying, at);
  const to = nearest(places.middles, middle.across);
  return { from: carrying.from, to, held: carrying.held, by: from(middle, places, to), began: carrying.began };
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
  return Math.hypot(at.across - carrying.began.across, at.down - carrying.began.down) > A_PRESS;
}

/**
 * The place of a run one point stands over, and none where it stands over no card of it.
 *
 * A fan draws each of its cards over the one before, so the card a hand rests on where two of them cover the
 * point is the later of the two. This is what tells a hand still resting on the card it laid down from a hand
 * that has come off the run or onto the card beside it.
 */
export function over(places: Places, at: Point): number | null {
  const covering = places.middles.flatMap((middle, place) => (covers(places, middle, at) ? [place] : []));
  return covering.at(LAST) ?? null;
}

/**
 * The place a hand rests on having just laid a card down at it, and none where it rests on nothing of the sort.
 *
 * A card let go under the hand that carried it is still a card in hand, so it stands where a card in hand stands
 * until the hand comes off it. A hand that came off the run, or let go over the card lying beside the one it
 * carried, rests on no card it laid; and a press that carried the card nowhere laid nothing down.
 */
export function restingOn(carrying: Carry, places: Places, at: Point): number | null {
  if (carrying.by === null || over(places, at) !== carrying.to) {
    return null;
  }

  return carrying.to;
}

/**
 * Where a run draws each of its places, read off the page as a card of it is taken hold of.
 *
 * A run keeps the places it was drawn with for the whole of a carry, so reading them once as the card comes up
 * answers every point the pointer goes on to stand at. They are read off the drawing itself, which is what lets a
 * fan of any size, closed up to whatever room its zone has, be carried through by the card the player can see.
 *
 * Returns:
 *     Where the places lie, and nothing for a run drawing none.
 */
export function placesOf(run: Element | null): Places | null {
  const drawn = run === null ? [] : [...run.querySelectorAll(DRAWN)].map((place) => place.getBoundingClientRect());
  const first = drawn.at(0);
  if (first === undefined) {
    return null;
  }

  return {
    middles: drawn.map((place) => place.x + place.width / MIDWAY),
    along: first.y + first.height / MIDWAY,
    reach: { across: first.width, down: first.height },
  };
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
    onPointerLeave: handling.leave,
  };
}

/** Where the pointer stands, as the page reads a press travelling across it. */
function pointing(event: PointerEvent<HTMLElement>): Point {
  return { across: event.clientX, down: event.clientY };
}

/** Where the middle of the card in hand stands, which is the hold it was taken by carried to where the hand is. */
function middleOf(carrying: Carry, at: Point): Point {
  return { across: at.across - carrying.held.across, down: at.down - carrying.held.down };
}

/** Whether the card drawn at one place of a run covers one point, which is a point lying within its reach. */
function covers(places: Places, middle: number, at: Point): boolean {
  return (
    Math.abs(at.across - middle) <= places.reach.across / MIDWAY &&
    Math.abs(at.down - places.along) <= places.reach.down / MIDWAY
  );
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
