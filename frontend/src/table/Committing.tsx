import type { ReactElement } from "react";

import type { GatheringView } from "../api/gathering";
import { commitOf } from "../play/company";
import { classes } from "./classes";

/** What a guest holding no seat is told, since the players of the game are the ones who commit and deal it. */
const STAND = "Take a seat to deal";

/** What the press reads while it takes a commitment, one face for giving it and one for taking it back. */
const READY = "Ready";
const READIED = "Ready ✓";

/** What the press reads once the table may be dealt, and what stands there where the deal is the host's to call. */
const DEAL = "Deal the cards";
const WAIT = "Waiting for the host to deal";

interface CommittingProps {
  gathering: GatheringView;
  ready: (committed: boolean) => void;
  callTheDeal: () => void;
}

/**
 * The one press the room carries a seated guest through, from committing to the settings to calling the deal.
 *
 * It is a seated guest's own commitment first: they press to say the settings may be dealt and press again to
 * take that word back, and the line beside it reads what the table still waits on. Once nothing does, the press
 * becomes the deal itself where the guest may call it, and where a host-governed table keeps the deal to the
 * host it reads as the wait it is. A guest standing by neither commits nor deals, and the press tells them so.
 */
export function Committing({ gathering, ready, callTheDeal }: CommittingProps): ReactElement {
  const commit = commitOf(gathering);
  switch (commit.act) {
    case "stand":
      return (
        <button type="button" className="commit" disabled>
          {STAND}
        </button>
      );
    case "ready":
      return (
        <div className="committing">
          <button
            type="button"
            className={classes("commit", "ready", commit.ready && "committed")}
            aria-pressed={commit.ready}
            onClick={() => ready(!commit.ready)}
          >
            {commit.ready ? READIED : READY}
          </button>
          <span className="pending">{commit.pending}</span>
        </div>
      );
    case "deal":
      return (
        <button type="button" className="commit deal" onClick={callTheDeal}>
          {DEAL}
        </button>
      );
    case "wait":
      return (
        <button type="button" className="commit" disabled>
          {WAIT}
        </button>
      );
  }
}
