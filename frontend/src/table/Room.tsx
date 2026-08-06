import type { ReactElement } from "react";

import type { Seat } from "../api/seat";
import { useGathering } from "../play/useGathering";
import { Gathering } from "./Gathering";
import { Table } from "./Table";
import { Waiting } from "./Waiting";

interface RoomProps {
  seat: Seat;
}

/**
 * The room this tab holds a token at, which is a table gathering until the company deals it.
 *
 * One reading of the gathering carries the page across: `dealt` turns true once and the table stands in service
 * from then on, so the guest who called for the deal and the guests who were watching arrive at it together.
 * The seat a token holds is the seat it goes on to play, so nothing is asked again on the way over.
 */
export function Room({ seat }: RoomProps): ReactElement {
  const { gathering, offerings, connection, trouble, claim, settle, callTheDeal } = useGathering(seat);

  if (gathering === null || offerings === null) {
    return <Waiting table={seat.table} connection={connection} trouble={trouble} />;
  }

  if (gathering.dealt) {
    return <Table seat={seat} />;
  }

  return (
    <Gathering
      gathering={gathering}
      offerings={offerings}
      connection={connection}
      trouble={trouble}
      claim={claim}
      settle={settle}
      callTheDeal={callTheDeal}
    />
  );
}
