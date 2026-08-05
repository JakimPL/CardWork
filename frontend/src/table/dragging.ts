import type { DragEvent } from "react";

/** What the browser is told of a card in hand: that it is being moved, and which place of a run it came from. */
const MOVED = "move";
const CARRIED = "application/x-cardwork-place";

/** A card taken hold of and the place it has been carried to, both of them positions of the run it lies in. */
export interface Carry {
  from: number;
  to: number;
}

/**
 * How one place of a run is taken hold of and carried, which the run states for each of its places in turn.
 *
 * A card draws itself and answers what a player does to it, so the answers a drag asks for arrive together with
 * the place the card lies at: taking it up, reaching a place with it, and letting it go wherever it ended up.
 */
export interface Handling {
  place: number;
  carried: boolean;
  grasp: () => void;
  reach: () => void;
  release: () => void;
}

/**
 * What one place of a run answers of being taken hold of, which is the whole of what the browser works a drag by.
 *
 * A place of a run nobody orders answers none of it, and a place answering none of it is one the browser carries
 * nowhere: the gesture is there where the run it would be made in is a run somebody may lay out.
 */
export interface Grasped {
  draggable?: boolean | undefined;
  onDragStart?: ((event: DragEvent) => void) | undefined;
  onDragEnter?: ((event: DragEvent) => void) | undefined;
  onDragEnd?: (() => void) | undefined;
}

/** The card at one position taken hold of, which leaves the run lying as it lay until the card is carried off. */
export function grasped(position: number): Carry {
  return { from: position, to: position };
}

/** The card in hand carried to another place of the run, and none carried where none was taken hold of. */
export function carriedTo(carrying: Carry | null, position: number): Carry | null {
  return carrying === null ? null : { from: carrying.from, to: position };
}

/** Whether the card has come to lie elsewhere than where it was taken from, which is what there is to lay down. */
export function moved(carrying: Carry): boolean {
  return carrying.from !== carrying.to;
}

/**
 * One run as a card carried through it lays it out, which is the order that run comes to lie in.
 *
 * The card is lifted out of the run and put back where it was carried to, so the cards it passed over close up
 * behind it and it comes to lie at the place it was let go over. This is the one reading of a carry: a player
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

/** What a card answers of a drag, out of the handling the run it lies in states for its place in that run. */
export function handled(handling: Handling | null): Grasped {
  if (handling === null) {
    return {};
  }

  return {
    draggable: true,
    onDragStart: grasping(handling.place, handling.grasp),
    onDragEnter: reaching(handling.reach),
    onDragEnd: handling.release,
  };
}

/**
 * Taking hold of one place of a run, which tells the browser what is travelling and the page which card it is.
 *
 * A card travels under a name of this page's own, so what it carries is one place of one run and a page reading
 * any other name is left to make of the drop whatever it was already going to.
 */
export function grasping(position: number, answer: () => void): (event: DragEvent) => void {
  return (event) => {
    event.dataTransfer.effectAllowed = MOVED;
    event.dataTransfer.setData(CARRIED, String(position));
    answer();
  };
}

/**
 * A card carried onto a place of the run, which the page answers in the browser's place.
 *
 * A card is let go only where the page has said it may be, so saying so is what a place does as the card reaches
 * it. Letting go is answered the same way, since what becomes of the card from there is the page's to say.
 */
export function reaching(answer: () => void): (event: DragEvent) => void {
  return (event) => {
    event.preventDefault();
    answer();
  };
}

/** A card carried across a run that will take it, which is the page standing by what it said as the card arrived. */
export function allowing(event: DragEvent): void {
  event.preventDefault();
}
