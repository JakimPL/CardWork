import { useCallback, useMemo, useState } from "react";

import type { Layout } from "../api/layout";
import { movedOn, reasonOf, Refused } from "../api/refusal";
import type { Seat } from "../api/seat";
import type { PositionView, ZoneId } from "../api/views";
import { guidance } from "./guidance";
import type { Prospect, Selection, Target } from "./selection";
import { offersOf, offerTo, pickedUp, prospect } from "./selection";
import { commandFor, deliver, named } from "./sending";

/** A selection as it is held: the cards, and the position they were picked out of. */
interface Held {
  selection: Selection;
  seq: number;
}

/** Playing a table from one seat: what the cards on screen may do, and the three ways of doing it. */
export interface Playing {
  standing: Prospect;
  hint: string;
  sending: boolean;
  pick: (zone: ZoneId, index: number) => void;
  commit: (target: Target) => void;
  clear: () => void;
}

/**
 * Play one table from one seat: pick cards up, read what they could send, and send it by pointing.
 *
 * The moves the table says are open are the whole of what this rests on, so nothing here knows one game from
 * another: a card reads plainly because some move names it, and a place lights up because the cards in hand
 * make a move that goes there. A move leaves for the table only on a click at such a place, which is what keeps
 * a hand of cards from committing itself.
 *
 * A selection is held against the position it was made in. The table moving on — by this seat's own move
 * landing or another's — leaves it behind rather than carrying it onto cards that have since shifted.
 *
 * @param seat - the table played at and the token the seat is held by.
 * @param layout - how this seat lays the table out, which the moves are read through.
 * @param view - the position as it stands, which a move is weighed and sent against.
 * @param refresh - reading the position afresh, for when the table turns out to have moved on.
 */
export function usePlay(seat: Seat, layout: Layout, view: PositionView, refresh: () => void): Playing {
  const [held, setHeld] = useState<Held | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  const selection = held !== null && held.seq === view.seq ? held.selection : null;
  const offers = useMemo(() => offersOf(layout, view), [layout, view]);
  const standing = useMemo(() => prospect(offers, selection), [offers, selection]);

  const clear = useCallback(() => {
    setHeld(null);
    setNotice(null);
  }, []);

  const pick = useCallback(
    (zone: ZoneId, index: number) => {
      const taken = pickedUp(standing, zone, index);
      setHeld(taken === null ? null : { selection: taken, seq: view.seq });
      setNotice(null);
    },
    [standing, view.seq],
  );

  const commit = useCallback(
    (target: Target) => {
      const offer = offerTo(standing, target);
      if (offer === null || sending) {
        return;
      }

      setSending(true);
      setNotice(null);
      deliver(seat, commandFor(offer.move, view.seq, named()))
        .then(() => {
          setHeld(null);
        })
        .catch((trouble: unknown) => {
          setNotice(reasonOf(trouble));
          if (trouble instanceof Refused && movedOn(trouble)) {
            refresh();
          }
        })
        .finally(() => {
          setSending(false);
        });
    },
    [seat, standing, view.seq, sending, refresh],
  );

  return { standing, hint: guidance(layout, view, standing, notice), sending, pick, commit, clear };
}
