import { useCallback, useEffect, useRef, useState } from "react";

import type { EventView, ZoneId } from "../api/views";

/** How long a heap shows the cards a commit laid on it before it closes over them, in milliseconds. */
const SETTLING = 400;

/** How many cards one commit has just laid in each zone it laid any in. */
export type Arrivals = ReadonlyMap<ZoneId, number>;

/** What a table reads as it rests, which is every zone holding what it already held. */
export const NOTHING_LANDED: Arrivals = new Map<ZoneId, number>();

/** Cards seen to land, and the reading time they are held on screen for. */
export interface Settling {
  arrivals: Arrivals;
  landed: (event: EventView) => void;
}

/**
 * The cards one commit laid down, counted per zone.
 *
 * A commit carries how each zone it touched read before and after, so what it laid on one is what lies at the
 * positions that zone grew by. A zone that gave cards up, traded one for another or had them shuffled comes
 * out the size it went in and reads as receiving none, which leaves this counting arrivals alone.
 */
export function arrivalsOf(event: EventView): Arrivals {
  const arrivals = new Map<ZoneId, number>();
  for (const change of event.changes) {
    const grown = change.after.length - change.before.length;
    if (grown > 0) {
      arrivals.set(change.zone, grown);
    }
  }

  return arrivals;
}

/** How many cards have just landed in one zone. */
export function landedIn(arrivals: Arrivals, zone: ZoneId): number {
  return arrivals.get(zone) ?? 0;
}

/**
 * Hold what a commit laid down for as long as it takes to read, then let the heaps close over it.
 *
 * A heap shows the cards a commit put on it beside the card they came to rest on, so a player reads what
 * arrived and where it landed; a moment later the heap stands as a heap again, which is the card on top and the
 * count of those beneath. The newest commit is the one that shows, since that is the arrival a player is
 * watching, and a commit that laid nothing down leaves the table as it reads.
 */
export function useArrivals(): Settling {
  const [arrivals, setArrivals] = useState<Arrivals>(NOTHING_LANDED);
  const reading = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      if (reading.current !== null) {
        clearTimeout(reading.current);
      }
    },
    [],
  );

  const landed = useCallback((event: EventView) => {
    const laid = arrivalsOf(event);
    if (laid.size === 0) {
      return;
    }

    if (reading.current !== null) {
      clearTimeout(reading.current);
    }

    setArrivals(laid);
    reading.current = setTimeout(() => {
      setArrivals(NOTHING_LANDED);
    }, SETTLING);
  }, []);

  return { arrivals, landed };
}
