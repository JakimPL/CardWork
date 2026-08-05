import type { ReactElement } from "react";

import type { Slot as Arrangement } from "../api/layout";
import type { PositionView } from "../api/views";
import type { Arrivals } from "../play/arrivals";
import type { Offered } from "../play/selection";
import { wordsOf } from "../play/selection";
import type { Playing } from "../play/usePlay";
import { classes } from "./classes";
import type { Placement } from "./placing";
import type { Run } from "./sizing";
import { spanning } from "./sizing";
import { Slot } from "./Slot";
import { Words } from "./Words";

/** The group a player's own moves are drawn in, which is the panel they play from. */
const OWN: Placement = "own";

interface ZonesProps {
  place: Placement;
  slots: Arrangement[];
  view: PositionView;
  arrivals: Arrivals;
  playing: Playing;
}

/**
 * One group of zones where the page puts them, in the order the layout places them.
 *
 * The shared table, the holdings of the seat reading the page and the cards lying at another seat are the same
 * drawing under three geographies, which is the whole of what a placement says: one component serves all of
 * them, and where each sits on the page is the style sheet's affair.
 *
 * A group carries how many cards wide it lies, so the cards of it are drawn as large as the room it has: the
 * panel a player plays from fills the width of the window, and a station the part of the table its seat holds.
 *
 * That panel holds the moves a player says as well as the cards they play: a move landing on no place is drawn
 * at the end of it and counted in the width like a card, so it lies among the cards it is said instead of.
 */
export function Zones({ place, slots, view, arrivals, playing }: ZonesProps): ReactElement {
  const said = place === OWN ? wordsOf(playing.standing) : [];
  const runs = [...slots.map((slot) => reading(slot, view)), ...saying(said)];
  return (
    <div className={classes("zones", place)} style={spanning(runs)}>
      {slots.map((slot) => (
        <Slot key={slot.zone} slot={slot} zone={view.zones[slot.zone]} arrivals={arrivals} playing={playing} />
      ))}
      {said.length > 0 && <Words offers={said} playing={playing} />}
    </div>
  );
}

/** One zone as the fitting reads it, which is how its cards lie and how many of them the observer is served. */
function reading(slot: Arrangement, view: PositionView): Run {
  return { spread: slot.spread, held: view.zones[slot.zone]?.cards.length ?? 0 };
}

/** The room the words of a turn take, which is a card apiece and none at all where a turn is said in none. */
function saying(said: Offered[]): Run[] {
  return said.length === 0 ? [] : [{ spread: "row", held: said.length }];
}
