import { useEffect, useState } from "react";

import type { Seat } from "../api/seat";
import { fragmentFor, seatIn } from "./joining";

/** The seat this tab plays as, which follows the fragment of the address and changes with it. */
export function useSeat(): Seat | null {
  const [fragment, setFragment] = useState(window.location.hash);

  useEffect(() => {
    const follow = () => setFragment(window.location.hash);
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);

  return seatIn(fragment);
}

/** Take a seat, which the tab remembers by holding it in the address it can be reopened at. */
export function takeSeat(seat: Seat): void {
  window.location.hash = fragmentFor(seat);
}
