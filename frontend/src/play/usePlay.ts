import { useCallback, useMemo, useState } from "react";

import type { Layout } from "../api/layout";
import type { CommandAccepted } from "../api/moves";
import { movedOn, reasonOf, Refused } from "../api/refusal";
import type { Seat } from "../api/seat";
import type { PositionView, ZoneId } from "../api/views";
import type { Laid } from "./arranging";
import { laidFrom, laidIn } from "./arranging";
import { guidance } from "./guidance";
import type { Held, Offered, Prospect, Target } from "./selection";
import { heldFrom, offersOf, offerTo, pickedUp, prospect, stands } from "./selection";
import { commandFor, deliver, lay, named, orderFor } from "./sending";

/**
 * Playing a table from one seat: what the cards on screen may do, and the ways of doing it.
 *
 * A move landing on a place is sent by `commit`, which is given the place pointed at and finds the move that
 * goes there. A move landing on none is sent by `say`, which is given the move itself, since the words drawn for
 * it stand for that move and nothing else. `arrange` sends no move at all: it is the order a player laid a zone
 * of its own out in, which the table records beside the moves and no turn stands in the way of.
 *
 * `laidIn` answers that order back while the table has yet to hand it over, so the cards stay where the player
 * put them from the moment they let go.
 */
export interface Playing {
  standing: Prospect;
  hint: string;
  cues: boolean;
  sending: boolean;
  pick: (zone: ZoneId, index: number) => void;
  commit: (target: Target) => void;
  say: (offer: Offered) => void;
  arrange: (zone: ZoneId, order: number[]) => void;
  laidIn: (zone: ZoneId) => number[] | null;
  clear: () => void;
}

/**
 * Play one table from one seat: pick cards up, read what they could send, and send it by pointing.
 *
 * The moves the table says are open are the whole of what this rests on, so nothing here knows one game from
 * another: a card reads plainly because some move names it, and a place lights up because the cards in hand
 * make a move that goes there. A move leaves for the table only on a click at such a place, which is what keeps
 * a hand of cards from committing itself. A move landing on no place leaves on a click at the words standing for
 * it, which the empty hand it names arms.
 *
 * A selection is held against the cards it was made on. Every commit is read against them, so a table moving on
 * for reasons of its own — another seat's move, another seat sorting its own cards — leaves a selection standing,
 * and the cards it names moving is what puts it down.
 *
 * A command that lands puts the cards in hand back down, since a move played takes them out of the zone they were
 * picked from and an order laid down leaves them lying elsewhere in it: either way the positions the selection
 * named are positions other cards have come to.
 *
 * An order a player lays down stands on screen from the moment they let go until the table hands it back, so the
 * cards lie where they were put while the command travels. A command the table refuses leaves the page reading
 * the table rather than the hand, which is what puts such an order back down.
 *
 * @param seat - the table played at and the token the seat is held by.
 * @param layout - how this seat lays the table out, which the moves are read through.
 * @param view - the position as it stands, which a move is weighed and sent against.
 * @param refresh - reading the position afresh, for when the table turns out to have moved on.
 */
export function usePlay(seat: Seat, layout: Layout, view: PositionView, refresh: () => void): Playing {
  const [held, setHeld] = useState<Held | null>(null);
  const [laid, setLaid] = useState<Laid | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  const selection = held !== null && stands(held, view.zones) ? held.selection : null;
  const offers = useMemo(() => offersOf(layout, view), [layout, view]);
  const standing = useMemo(() => prospect(offers, selection), [offers, selection]);

  const clear = useCallback(() => {
    setHeld(null);
    setNotice(null);
  }, []);

  const pick = useCallback(
    (zone: ZoneId, index: number) => {
      const taken = pickedUp(standing, zone, index);
      setHeld(taken === null ? null : heldFrom(view.zones, taken));
      setNotice(null);
    },
    [standing, view.zones],
  );

  const command = useCallback(
    (attempt: () => Promise<CommandAccepted>): boolean => {
      if (sending) {
        return false;
      }

      setSending(true);
      setNotice(null);
      attempt()
        .then(() => {
          setHeld(null);
        })
        .catch((trouble: unknown) => {
          setNotice(reasonOf(trouble));
          setLaid(null);
          if (trouble instanceof Refused && movedOn(trouble)) {
            refresh();
          }
        })
        .finally(() => {
          setSending(false);
        });

      return true;
    },
    [sending, refresh],
  );

  const send = useCallback(
    (offer: Offered) => {
      command(() => deliver(seat, commandFor(offer.move, view.seq, named())));
    },
    [command, seat, view.seq],
  );

  const arrange = useCallback(
    (zone: ZoneId, order: number[]) => {
      const laying = laidFrom(view.zones, zone, order);
      if (command(() => lay(seat, orderFor(zone, order, view.seq, named())))) {
        setLaid(laying);
      }
    },
    [command, seat, view.seq, view.zones],
  );

  const reading = useCallback((zone: ZoneId): number[] | null => laidIn(laid, zone, view.zones), [laid, view.zones]);

  const commit = useCallback(
    (target: Target) => {
      const offer = offerTo(standing, target);
      if (offer !== null) {
        send(offer);
      }
    },
    [standing, send],
  );

  return {
    standing,
    hint: guidance(layout, view, standing, notice),
    cues: layout.cues,
    sending,
    pick,
    commit,
    say: send,
    arrange,
    laidIn: reading,
    clear,
  };
}
