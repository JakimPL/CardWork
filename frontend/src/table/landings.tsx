import {
  createContext,
  type ReactElement,
  type ReactNode,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";

import type { Target } from "../play/selection";
import { keyOf } from "../play/selection";
import type { Carry, Point } from "./dragging";
import { sending } from "./dragging";

/** Where the hand stands over no place a move is sent by, which is a carry out over the table itself. */
const NOWHERE = null;

/** The name no place carries, which is what a hand over none of them is read against. */
const UNNAMED = "";

/** The smallest of the places a point stands over, which is the one drawn innermost. */
const NEAREST = 0;

/** The room one place takes on the page: the corner it begins at, and how far it reaches from there. */
export interface Room {
  at: Point;
  reach: Point;
}

/** One place a move is sent by pointing at, as the page draws it. */
export interface Placed {
  target: Target;
  room: Room;
}

/** One place as the page holds it, which is the move's place and the drawing it stated itself into. */
interface Drawn {
  target: Target;
  element: HTMLElement;
}

/**
 * The places a carry may land on, held for the whole page rather than by the zone or the seat drawing one.
 *
 * A hand carrying cards across the page holds the pointer to the card it pressed, so what the hand is over is
 * answered by the room each place takes rather than by what the press arrives at. Each place says where it is
 * drawn as it is drawn, which leaves the reading of a carry the page's own and the drawing of a place its own.
 *
 * The place under the hand is marked while the cards travel, so a player reads where they are about to go before
 * they let them go.
 */
export interface Landings {
  holds: (target: Target, element: HTMLElement | null) => () => void;
  at: (point: Point) => Target | null;
  aim: (target: Target | null) => void;
  aimed: (target: Target) => boolean;
}

/**
 * What letting the cards go comes to: a place they are sent to, the order the run has come to lie in, putting
 * them back down, or a press that carried them nowhere.
 *
 * These four are the whole of what a release answers, so a page reading one of them is a page reading the gesture
 * the player made.
 */
export type Landed =
  { lands: "sends"; target: Target } | { lands: "orders" } | { lands: "clears" } | { lands: "presses" };

/** A page nothing is carried across, which is what a table drawn outside a carry reads. */
const UNREACHED: Landings = {
  holds: () => () => undefined,
  at: () => NOWHERE,
  aim: () => undefined,
  aimed: () => false,
};

/**
 * The places the cards in hand may be carried to, which every place drawn on the page states itself into.
 *
 * A test states the places a carry reaches outright, which is what leaves the reading of a gesture apart from the
 * drawing of a page.
 */
export const Reachable = createContext<Landings>(UNREACHED);

interface ReachingProps {
  children: ReactNode;
}

/**
 * The page as the places on it may be reached, held for the whole of it.
 *
 * The places a move is sent by are drawn where the zones and the seats they belong to are drawn, so where they
 * lie is known only once the page is laid out: each of them says so as it is drawn and takes it back as it goes,
 * and a hand carrying cards asks the page which of them it is over. The room a place takes is read at the moment
 * of the asking, so a table redrawn under the hand is answered as it stands.
 */
export function Reaching({ children }: ReachingProps): ReactElement {
  const held = useRef(new Map<string, Drawn>());
  const [marked, setMarked] = useState<Target | null>(NOWHERE);

  const holds = useCallback((target: Target, element: HTMLElement | null): (() => void) => {
    if (element === null) {
      return () => undefined;
    }

    const name = keyOf(target);
    held.current.set(name, { target, element });
    return () => {
      held.current.delete(name);
    };
  }, []);

  const at = useCallback((point: Point): Target | null => reachedAt(drawn(held.current), point), []);

  const aim = useCallback((target: Target | null) => {
    setMarked((standing) => (naming(standing) === naming(target) ? standing : target));
  }, []);

  const aimed = useCallback((target: Target) => marked !== NOWHERE && keyOf(marked) === keyOf(target), [marked]);

  const landings = useMemo<Landings>(() => ({ holds, at, aim, aimed }), [holds, at, aim, aimed]);

  return <Reachable value={landings}>{children}</Reachable>;
}

/** The places one page draws, which a page holding a carry of its own answers for. */
export function useLandings(): Landings {
  return useContext(Reachable);
}

/**
 * The place one point stands over, and none where it stands over none of them.
 *
 * The places lie one inside another — a seat's whole corner of the table holds the zones drawn at it — so the
 * smallest of the ones covering a point is what a hand standing there means.
 */
export function reachedAt(placed: readonly Placed[], at: Point): Target | null {
  const covering = placed.filter((place) => covers(place.room, at)).sort((one, other) => roomy(one) - roomy(other));
  return covering.at(NEAREST)?.target ?? NOWHERE;
}

/**
 * What letting the cards go comes to, out of the carry that brought them there and the place they are over.
 *
 * A hand over a place sends the cards to it. A hand still over the run they came out of lays down the order it
 * has come to read. A hand over anything else puts the cards back down, which is what a carry landing nowhere
 * comes to. And a hand that carried them nowhere at all pressed the card it was on, which the page answers as the
 * click it is.
 *
 * @param carrying - the cards in hand as the release found them, and none where nothing was taken hold of.
 * @param target - the place the hand stands over, and none where it stands over no place at all.
 */
export function released(carrying: Carry | null, target: Target | null): Landed {
  if (carrying === null) {
    return { lands: "presses" };
  }

  if (carrying.by === null) {
    return { lands: "presses" };
  }

  if (!sending(carrying)) {
    return { lands: "orders" };
  }

  return target === NOWHERE ? { lands: "clears" } : { lands: "sends", target };
}

/** Every place the page draws, each with the room it takes as the page stands now. */
function drawn(held: Map<string, Drawn>): Placed[] {
  return [...held.values()].map((place) => ({ target: place.target, room: roomOf(place.element) }));
}

/** The room one place takes on the page, read off the drawing of it as it stands. */
function roomOf(element: HTMLElement): Room {
  const box = element.getBoundingClientRect();
  return { at: { across: box.x, down: box.y }, reach: { across: box.width, down: box.height } };
}

/** Whether one place covers one point, which is a point standing within the room it takes. */
function covers(room: Room, at: Point): boolean {
  return (
    at.across >= room.at.across &&
    at.across <= room.at.across + room.reach.across &&
    at.down >= room.at.down &&
    at.down <= room.at.down + room.reach.down
  );
}

/** How much of the page one place takes, which is what tells the innermost of two covering a point. */
function roomy(placed: Placed): number {
  return placed.room.reach.across * placed.room.reach.down;
}

/** The name one place carries, and none at all for a hand standing over no place. */
function naming(target: Target | null): string {
  return target === NOWHERE ? UNNAMED : keyOf(target);
}
