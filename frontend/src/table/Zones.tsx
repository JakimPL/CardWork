import type { ReactElement } from "react";

import type { Slot as Arrangement } from "../api/layout";
import type { PositionView } from "../api/views";
import type { Arrivals } from "../play/arrivals";
import type { Offered } from "../play/selection";
import { onTurn, wordsOf } from "../play/selection";
import type { Playing } from "../play/usePlay";
import { classes } from "./classes";
import type { Placement } from "./placing";
import { linesOf } from "./placing";
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
 * A group carries how many cards wide it lies and how many lines it lies in, so the cards of it are drawn as
 * large as the room it has: the panel a player plays from fills the width of the window, and a seat across the
 * table stands its holdings on one line with the places it seals a card in beneath them, which is the shape of
 * the room round the edge of a table.
 *
 * That panel holds the moves a player says as well as the cards they play: a move landing on no place is drawn
 * at the end of it and counted in the width like a card, so it lies among the cards it is said instead of.
 *
 * It says whose turn it is besides, since a player looking at their own cards is looking at the one place on the
 * page that is theirs: a turn there marks the panel as it marks a plaque and a seat round the table, and a panel
 * the table asks nothing of stands its cards quiet. The moves this seat is served are what both readings rest on,
 * so the panel reads live for exactly as long as there is something in it to do.
 */
export function Zones({ place, slots, view, arrivals, playing }: ZonesProps): ReactElement {
  const mine = place === OWN;
  const said = mine ? wordsOf(playing.standing) : [];
  const turn = mine && onTurn(playing.standing);
  const lines = linesOf(place, slots);
  return (
    <div
      className={classes("zones", place, mine && (turn ? "acting" : "idle"))}
      style={spanning(measuring(lines, view, said))}
    >
      {lines.map((line, index) => (
        <div key={naming(line)} className="line">
          {line.map((slot) => (
            <Slot key={slot.zone} slot={slot} zone={view.zones[slot.zone]} arrivals={arrivals} playing={playing} />
          ))}
          {said.length > 0 && index === lines.length - 1 && <Words offers={said} playing={playing} />}
        </div>
      ))}
    </div>
  );
}

/** Each line of a group as the fitting reads it, with the words of a turn taking the room of a card among them. */
function measuring(lines: Arrangement[][], view: PositionView, said: Offered[]): Run[][] {
  return lines.map((line, index) => [
    ...line.map((slot) => reading(slot, view)),
    ...(index === lines.length - 1 ? saying(said) : []),
  ]);
}

/** What tells one line of a group from the next, which is the zones lying along it. */
function naming(line: Arrangement[]): string {
  return line.map((slot) => slot.zone).join(" ");
}

/** One zone as the fitting reads it, which is how its cards lie and how many of them the observer is served. */
function reading(slot: Arrangement, view: PositionView): Run {
  return { spread: slot.spread, held: view.zones[slot.zone]?.cards.length ?? 0 };
}

/** The room the words of a turn take, which is a card apiece and none at all where a turn is said in none. */
function saying(said: Offered[]): Run[] {
  return said.length === 0 ? [] : [{ spread: "row", held: said.length }];
}
