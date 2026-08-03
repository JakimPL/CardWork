import { useEffect, useMemo, useState } from "react";

import type { Seat } from "../api/seat";
import { fragmentFor, seatIn } from "./joining";

/** The address a tab holding no seat stands at, which is the page a seat is taken from. */
const UNSEATED = "";

/**
 * The seat this tab plays as, which follows the fragment of the address and changes with it.
 *
 * One seat stands for as long as the fragment does, so everything hanging off it — the table joined, the
 * stream followed — is disturbed by the address changing and by nothing else.
 */
export function useSeat(): Seat | null {
  const [fragment, setFragment] = useState(window.location.hash);

  useEffect(() => {
    const follow = (): void => setFragment(window.location.hash);
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);

  return useMemo(() => seatIn(fragment), [fragment]);
}

/** Take a seat, which the tab remembers by holding it in the address it can be reopened at. */
export function takeSeat(seat: Seat): void {
  window.location.hash = fragmentFor(seat);
}

/** Put a seat down, which leaves the tab at the page a seat is taken from. */
export function leaveSeat(): void {
  window.location.hash = UNSEATED;
}
