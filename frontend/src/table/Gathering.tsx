import type { ReactElement } from "react";

import type { Choice, GatheringView, Offering } from "../api/gathering";
import { readOut } from "../play/codes";
import { dealReading, dealReady } from "../play/company";
import type { Connection } from "../play/connection";
import { CONNECTIONS } from "../play/connection";
import { leave } from "../play/useStanding";
import { classes } from "./classes";
import { Company } from "./Company";
import { Settling } from "./Settling";

interface GatheringProps {
  gathering: GatheringView;
  offerings: Offering[];
  connection: Connection;
  trouble: string | null;
  claim: (seat: number | null) => void;
  settle: (choice: Choice) => void;
  callTheDeal: () => void;
}

/**
 * The table before it is dealt: who is at it, what it plays, and the press that deals it.
 *
 * The code stands here as it is read out, since a guest already at the table is who passes it to the next one.
 * Every guest holding a seat may settle the choice and call the deal, and each of them reads the others doing
 * it as it happens: the stream carries the whole room at every change, so a page follows without being told.
 *
 * The deal is the last thing a gathering has to say, and the frame carrying it takes every page at the room
 * over to the table.
 */
export function Gathering({
  gathering,
  offerings,
  connection,
  trouble,
  claim,
  settle,
  callTheDeal,
}: GatheringProps): ReactElement {
  return (
    <div className="notice gathering">
      <p className="gathered">
        Table <strong>{gathering.table}</strong> is gathering, as <strong>{gathering.mine}</strong>
      </p>
      <p className="code">
        Join code <strong>{readOut(gathering.code)}</strong>
      </p>
      <Company gathering={gathering} claim={claim} />
      <Settling gathering={gathering} offerings={offerings} settle={settle} />
      {trouble !== null && <p className="trouble">{trouble}</p>}
      <div className="choices">
        <button type="button" disabled={!dealReady(gathering)} onClick={callTheDeal}>
          {dealReading(gathering)}
        </button>
        <button type="button" onClick={leave}>
          Leave the table
        </button>
        <span className={classes("connection", connection)} title={trouble ?? undefined}>
          {CONNECTIONS[connection]}
        </span>
      </div>
    </div>
  );
}
