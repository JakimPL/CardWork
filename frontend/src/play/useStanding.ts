import { useEffect, useMemo, useState } from "react";

import type { Seat } from "../api/seat";
import type { Standing } from "./joining";
import { fragmentFor, standingIn } from "./joining";

/** The address a tab standing at no table holds, which is the arrival a table is named at. */
const UNJOINED = "";

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

/** Speak at a table through the token an arrival minted, which the tab remembers so a reload rejoins on it. */
export function arrivedAt(seat: Seat): void {
  window.location.hash = fragmentFor(seat);
}

/** Leave the table, which puts the tab back at naming a table to arrive at. */
export function leave(): void {
  window.location.hash = UNJOINED;
}
