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
 * One run as it stands at the moment a card of it is taken hold of: where it draws its places, and whether the
 * order of it is this seat's own to set.
 *
 * A run holds as many places while cards of it are being carried as it held before, and each of them is drawn
 * where it was: what a carry through the run changes is which card lies at which place. So the drawing read once
 * as the cards come up answers the whole gesture, and a pointer standing anywhere is read against it.
 *
 * The reach of a card is the same at every place, since one run draws one size of card, and it is what says which
 * of those places a point stands over and how far off the run a card has been carried.
 *
 * A run the table keeps the order of is carried out of and never through: the cards of it are there to send
 * somewhere, and they lie where the table lays them until they are sent.
 */
export interface Places {
  middles: readonly number[];
  along: number;
  reach: Point;
  orderable: boolean;
}

/**
 * The cards in hand: the places they came out of, which of them the hand pressed, where the block of them has
 * reached, where along the pressed card the hand took hold, how far they stand from the places they are drawn at,
 * and the point the hand set out from.
 *
 * The cards travel together in the order the run reads them, so the place reached is where the first of them has
 * come to lie and the pressed card lies its own rank along from there. The cards have reached nowhere in the run
 * while the hand is carrying them clear of it, which leaves the run standing as the table holds it: the cards are
 * drawn at the places they came out of, and what the hand is over is a place to send them to.
 *
 * The shift is the cards as the player sees them, measured from the place the pressed card is drawn at, so the
 * block travels as the little fan it was picked up as with that card exactly under the hand. Nothing stands off
 * its place while the hand holding it has yet to travel, which is what leaves a click a click: the point the hand
 * set out from is what that is read against.
 */
export interface Carry {
  from: number[];
  rank: number;
  to: number | null;
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
 * nobody plays out of or orders answers none of it, which leaves the card lying where the table holds it.
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

/**
 * The cards one press takes hold of, out of the place pressed and the places already in hand.
 *
 * A press takes hold of the cards in hand where the card pressed is one of them, and of that card alone
 * otherwise: a run gathered into a block travels as a block, and a card picked out of one travels by itself. The
 * cards are held in the order the run reads them, wherever in it the player picked them up.
 *
 * The run stands as the table holds it until the hand carries the cards off, so a press changes nothing.
 *
 * @param place - the place of the run the hand pressed.
 * @param inHand - the places of the run whose cards the player has already picked up.
 * @param places - the run as it stands, read off the page.
 * @param at - the point the hand pressed at.
 */
export function grasped(place: number, inHand: readonly number[], places: Places, at: Point): Carry {
  const taken = inHand.includes(place) ? [...inHand].sort(ascending) : [place];
  return { from: taken, rank: taken.indexOf(place), to: null, held: from(at, places, place), by: null, began: at };
}

/**
 * The cards in hand as the pointer stands now: the place they have reached, and how far they stand from it.
 *
 * The place they have reached is the one the middle of the pressed card lies nearest, counted back by that card's
 * rank among them, which is where the player is holding the block rather than where the pointer within it stands.
 * So the run opens at the place the block has come to cover, cards taken hold of by any part of themselves lie
 * where they lay, and the two readings of one gesture — the cards under the hand, the run about to lie — are read
 * off the one figure. A block carried off either end of the run comes to lie along the end it reached.
 *
 * Cards carried clear of the run reach nowhere in it: the run stands as the table holds it and the cards travel
 * from the places they came out of, which is a hand taking them somewhere else on the table. A run whose order
 * the table keeps is carried out of that way wherever the hand goes.
 *
 * A hand that has yet to travel holds the cards where the run draws them, and a hand that has travelled carries
 * them for the rest of the press, so an unsteady hand leaves a click a click and a carry stays a carry.
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
  const to = reaching(carrying, places, middle);
  return { ...carrying, to, by: from(middle, places, pressedAt(carrying, to)) };
}

/**
 * The places the run draws the cards in hand at, in the order it reads them.
 *
 * The run has opened for them where they have reached a place in it, and draws them where they came out of it
 * where the hand is carrying them somewhere else, so what stands off its place is read the one way either way.
 */
export function heldAt(carrying: Carry): number[] {
  const reached = carrying.to;
  return reached === null ? carrying.from : [...carrying.from.keys()].map((rank) => reached + rank);
}

/**
 * Whether the cards have come to lie elsewhere than where they were taken from, which is what there is to lay
 * down.
 *
 * Cards picked up here and there in a run come together into a block where they are carried, so gathering three
 * of a kind is an order to lay down even where the first of them stays where it lay.
 */
export function moved(carrying: Carry): boolean {
  return heldAt(carrying).some((place, rank) => place !== carrying.from[rank]);
}

/**
 * Whether the cards in hand are out over the table, which is what letting go of them there sends them from.
 *
 * A hand carrying cards clear of the run they came out of is taking them somewhere else, so what a release
 * answers is the place they are over rather than the order of the run behind them.
 */
export function sending(carrying: Carry): boolean {
  return carrying.by !== null && carrying.to === null;
}

/**
 * Whether the hand on a card has carried it, which is what tells a card being carried from a card being pressed.
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
 * Whether a card carried to one point lies over the run it came out of, which is what orders that run.
 *
 * The card is read rather than the pointer holding it: a hand lifts a card clear of the run to take it elsewhere,
 * so what says the run is being ordered is the card still lying along it. Half a card past either end is the room
 * a card is made first or last in, and half a card above or below is the lift that takes it out over the table.
 *
 * @param places - the run as it stands, read off the page.
 * @param middle - where the middle of the card in hand stands.
 */
export function within(places: Places, middle: Point): boolean {
  const first = places.middles.at(0);
  const last = places.middles.at(LAST);
  if (first === undefined || last === undefined) {
    return false;
  }

  return (
    middle.across >= first - places.reach.across / MIDWAY &&
    middle.across <= last + places.reach.across / MIDWAY &&
    Math.abs(middle.down - places.along) <= places.reach.down / MIDWAY
  );
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
 * until the hand comes off it. The card the hand holds is the one it pressed, wherever the rest of the block came
 * to lie. A hand that came off the run, that let go over the card lying beside the one it carried, or that
 * carried the cards out over the table rests on no card it laid; and a press that carried them nowhere laid
 * nothing down.
 */
export function restingOn(carrying: Carry, places: Places, at: Point): number | null {
  const rested = carrying.to === null ? null : pressedAt(carrying, carrying.to);
  if (carrying.by === null || rested === null || over(places, at) !== rested) {
    return null;
  }

  return rested;
}

/**
 * Where a run draws each of its places, read off the page as a card of it is taken hold of.
 *
 * A run keeps the places it was drawn with for the whole of a carry, so reading them once as the cards come up
 * answers every point the pointer goes on to stand at. They are read off the drawing itself, which is what lets a
 * fan of any size, closed up to whatever room its zone has, be carried through by the cards the player can see.
 *
 * @param run - the drawing of the run, as the page holds it.
 * @param orderable - whether the order of that run is this seat's own to set.
 *
 * Returns:
 *     Where the places lie, and nothing for a run drawing none.
 */
export function placesOf(run: Element | null, orderable: boolean): Places | null {
  const drawn = run === null ? [] : [...run.querySelectorAll(DRAWN)].map((place) => place.getBoundingClientRect());
  const first = drawn.at(0);
  if (first === undefined) {
    return null;
  }

  return {
    middles: drawn.map((place) => place.x + place.width / MIDWAY),
    along: first.y + first.height / MIDWAY,
    reach: { across: first.width, down: first.height },
    orderable,
  };
}

/**
 * One run as the cards carried through it lay it out, which is the order that run comes to lie in.
 *
 * The cards are lifted out of the run and put back where they were carried to, so the cards they passed over
 * close up behind them and they come to lie in a block at the place they were let go at. This is the one reading
 * of a carry: a player carrying cards is reading the run this answers with, and letting them go sends the order
 * they were reading.
 *
 * A run lying as it lies is the answer where no card is being carried through it, where the hand is carrying
 * cards out over the table, and where the places taken from are places the run holds no card at.
 */
export function laidOut<T>(run: readonly T[], carrying: Carry | null): T[] {
  const reached = carrying === null ? null : carrying.to;
  if (carrying === null || reached === null) {
    return [...run];
  }

  const held = run.filter((_, place) => carrying.from.includes(place));
  const rest = run.filter((_, place) => !carrying.from.includes(place));
  if (held.length !== carrying.from.length) {
    return [...run];
  }

  return [...rest.slice(0, reached), ...held, ...rest.slice(reached)];
}

/**
 * The order letting the carried cards go sends, and none where the run stands as the table already holds it.
 *
 * A player reads the run as it lies in front of them, so the order they send by letting go is the one they have
 * been reading: it is theirs to send from wherever on the page the cards are let go, since the run they are
 * answering is the run they can see. Cards carried home again lie at the places they were taken from, which
 * leaves the run the table's own and nothing to send.
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

/** The places of a run in the order it reads them, which is the order the cards of a block travel in. */
function ascending(one: number, other: number): number {
  return one - other;
}

/**
 * Where the block of cards in hand has reached, and nowhere at all where the hand is carrying them elsewhere.
 *
 * The place is where the first of the cards comes to lie, so the pressed card lands where the player is holding
 * it and the cards it was picked up with keep their order around it. A block reaching past either end of the run
 * lies along that end, since a run holds as many cards as it held.
 */
function reaching(carrying: Carry, places: Places, middle: Point): number | null {
  if (!places.orderable || !within(places, middle)) {
    return null;
  }

  const reached = nearest(places.middles, middle.across) - carrying.rank;
  return Math.min(Math.max(reached, 0), Math.max(places.middles.length - carrying.from.length, 0));
}

/** The place the run draws the pressed card at, which the cards it was taken with lie in order around. */
function pressedAt(carrying: Carry, to: number | null): number {
  return to === null ? (carrying.from.at(carrying.rank) ?? 0) : to + carrying.rank;
}

/** Where the middle of the pressed card stands, which is the hold it was taken by carried to where the hand is. */
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
