import { useEffect, useMemo, useState } from "react";

import type { Seat } from "../api/seat";
import type { Standing } from "./joining";
import { fragmentFor, standingIn } from "./joining";

/** The address a tab standing at no table holds, which is the page a table is named from. */
const UNJOINED = "";

/** The code a tab holding a token has no further use for, since the token is what speaks from then on. */
const ARRIVED = null;

/**
 * Where this tab stands, which follows the fragment of the address and changes with it.
 *
 * One standing holds for as long as the fragment does, so everything hanging off it — the table joined, the
 * gathering followed, the stream held — is disturbed by the address changing and by nothing else.
 */
export function useStanding(): Standing {
  const [fragment, setFragment] = useState(window.location.hash);

  useEffect(() => {
    const follow = (): void => setFragment(window.location.hash);
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);

  return useMemo(() => standingIn(fragment), [fragment]);
}

/** Stand at a table on the code that admits, which is what a tab does before it has a name at one. */
export function standAt(table: string, code: string | null): void {
  window.location.hash = fragmentFor({ table, token: null }, code);
}

/** Speak at a table through the token an arrival minted, which the tab remembers so a reload rejoins on it. */
export function arrivedAt(seat: Seat): void {
  window.location.hash = fragmentFor(seat, ARRIVED);
}

/** Leave the table, which puts the tab back at the page a table is named from. */
export function leave(): void {
  window.location.hash = UNJOINED;
}
