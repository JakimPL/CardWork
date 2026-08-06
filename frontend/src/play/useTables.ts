import { useEffect, useState } from "react";

import { readTables } from "../api/lobby";

/** What the page holds where nothing gathers here and where the host did not answer, which is a table to name. */
const NONE_GATHERING: string[] = [];

/**
 * The tables gathering at this host, read for a tab that was handed no address.
 *
 * Somebody who reached the server bare is offered what is gathering rather than left to guess at a name, and the
 * usual host holds the one table. A tab whose address already names a table wants none of this, so the read is
 * made where it is asked for, and a host answering nothing leaves the table to be named.
 *
 * @param wanted - whether the tables are asked for at all, which a tab standing at a table answers no.
 * @returns the tables gathering, and nothing until the host has answered.
 */
export function useTables(wanted: boolean): string[] | null {
  const [tables, setTables] = useState<string[] | null>(null);

  useEffect(() => {
    if (!wanted) {
      return;
    }

    const asking = { held: true };
    readTables()
      .then((gathering) => {
        if (asking.held) {
          setTables(gathering);
        }
      })
      .catch(() => {
        if (asking.held) {
          setTables(NONE_GATHERING);
        }
      });

    return () => {
      asking.held = false;
    };
  }, [wanted]);

  return tables;
}
