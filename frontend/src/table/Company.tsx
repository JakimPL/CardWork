import type { ReactElement } from "react";

import type { GatheringView, Tint } from "../api/gathering";
import { holderOf, mine, seatsOf, standingBy } from "../play/company";
import { classes } from "./classes";
import { Tints } from "./Tints";

/** What an empty place reads as, which is the one thing a seat says of itself before anybody holds it. */
const EMPTY = "empty";

interface CompanyProps {
  gathering: GatheringView;
  claim: (seat: number | null) => void;
  tint: (chosen: Tint) => void;
}

/**
 * Who is at the table: one place per seat the choice settled, the guests standing by, and the colours they play in.
 *
 * A seat is taken by pressing it and given up the same way, which is the whole of the seating: nobody assigns
 * a place and nobody may take one another guest holds. Presence follows the page each guest has open, so the
 * company reads as the room does.
 *
 * Each place carries the tint of the guest holding it, and the swatches stand under all of them: a colour is
 * held by a guest rather than by a seat, so it is the whole company that is being told apart there.
 */
export function Company({ gathering, claim, tint }: CompanyProps): ReactElement {
  const standing = standingBy(gathering);
  return (
    <div className="company">
      <ul className="places">
        {seatsOf(gathering).map((seat) => (
          <Place key={seat} gathering={gathering} seat={seat} claim={claim} />
        ))}
      </ul>
      {standing.length > 0 && <p className="watching">Standing by: {standing.map((guest) => guest.name).join(", ")}</p>}
      <Tints gathering={gathering} tint={tint} />
    </div>
  );
}

interface PlaceProps {
  gathering: GatheringView;
  seat: number;
  claim: (seat: number | null) => void;
}

/** One place at the table: the seat, the guest holding it, and the press that takes or gives it up. */
function Place({ gathering, seat, claim }: PlaceProps): ReactElement {
  const holder = holderOf(gathering, seat);
  const own = mine(gathering, seat);
  return (
    <li className={classes("place", holder === null ? "empty" : "taken", own && "own")} data-tint={holder?.tint}>
      <span className="seat">Seat {seat}</span>
      <span className={classes("guest", holder !== null && (holder.present ? "present" : "away"))}>
        {holder?.name ?? EMPTY}
      </span>
      <button type="button" disabled={holder !== null && !own} onClick={() => claim(own ? null : seat)}>
        {own ? "Stand up" : "Sit here"}
      </button>
    </li>
  );
}
