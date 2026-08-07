import { useCallback, useEffect, useRef, useState } from "react";

import type { Choice, GatheringView, Offering, Tint } from "../api/gathering";
import {
  chooseTint,
  claimSeat,
  commitReady,
  deal,
  followGathering,
  readGathering,
  readOfferings,
  settleChoice,
  settleGovernance,
} from "../api/lobby";
import { reasonOf } from "../api/refusal";
import type { Seat } from "../api/seat";
import type { Connection } from "./connection";
import { whileInView } from "./viewing";

/** How far a client has read before it holds a view, which the one it joins on settles at once. */
const UNREAD = 0;

/** A gathering as one tab holds it: how it stands, what may be played at it, and how it is being kept current. */
export interface Gathered {
  gathering: GatheringView | null;
  offerings: Offering[] | null;
  connection: Connection;
  trouble: string | null;
  claim: (seat: number | null) => void;
  tint: (chosen: Tint) => void;
  settle: (choice: Choice) => void;
  ready: (committed: boolean) => void;
  govern: (democratic: boolean) => void;
  callTheDeal: () => void;
}

/**
 * Join the gathering of one table and stay current with it until the cards are dealt.
 *
 * A client asks for two things as it arrives and one thereafter: what the host offers, how the gathering
 * stands, and then how it stands again at every revision it reaches. A gathering is a room rather than a
 * record, so each frame carries the whole of it and the newest reading is the one that holds.
 *
 * The stream is held while the page is in view, which is also what reads this guest as present, so the company
 * on screen is the company watching the room. A tab that looks away leaves it and rejoins where it left off.
 *
 * Every command quotes the revision it was built on, so two guests settling the choice at once leaves the
 * second told rather than overruled, and the answer to a command is a reading of the room like any other.
 *
 * @param seat - the table gathered and the token it is attended as.
 */
export function useGathering(seat: Seat): Gathered {
  const [gathering, setGathering] = useState<GatheringView | null>(null);
  const [offerings, setOfferings] = useState<Offering[] | null>(null);
  const [connection, setConnection] = useState<Connection>("joining");
  const [trouble, setTrouble] = useState<string | null>(null);
  const reached = useRef(UNREAD);

  const hold = useCallback((view: GatheringView) => {
    reached.current = Math.max(reached.current, view.revision);
    setGathering((held) => (held !== null && held.revision > view.revision ? held : view));
  }, []);

  const stumbled = useCallback((refusal: unknown) => {
    setTrouble(reasonOf(refusal));
  }, []);

  const commanded = useCallback(
    (answering: (revision: number) => Promise<GatheringView>) => {
      setTrouble(null);
      answering(reached.current).then(hold).catch(stumbled);
    },
    [hold, stumbled],
  );

  const claim = useCallback(
    (taken: number | null) => {
      commanded((revision) => claimSeat(seat, { seat: taken, base_revision: revision }));
    },
    [seat, commanded],
  );

  const tint = useCallback(
    (chosen: Tint) => {
      commanded((revision) => chooseTint(seat, { tint: chosen, base_revision: revision }));
    },
    [seat, commanded],
  );

  const settle = useCallback(
    (choice: Choice) => {
      commanded((revision) => settleChoice(seat, { choice, base_revision: revision }));
    },
    [seat, commanded],
  );

  const ready = useCallback(
    (committed: boolean) => {
      commanded((revision) => commitReady(seat, { ready: committed, base_revision: revision }));
    },
    [seat, commanded],
  );

  const govern = useCallback(
    (democratic: boolean) => {
      commanded((revision) => settleGovernance(seat, { democratic, base_revision: revision }));
    },
    [seat, commanded],
  );

  const callTheDeal = useCallback(() => {
    commanded((revision) => deal(seat, { base_revision: revision }));
  }, [seat, commanded]);

  useEffect(() => {
    const attending = { held: true };
    let release: (() => void) | null = null;

    const following = (): (() => void) => {
      const stop = followGathering(seat, reached.current + 1, {
        onOpen: () => {
          setConnection("following");
          setTrouble(null);
        },
        onFrame: hold,
        onDropped: (reason) => {
          setConnection("resuming");
          setTrouble(reason);
        },
        onRefused: (reason) => {
          setConnection("refused");
          setTrouble(reason);
        },
      });

      return () => {
        setConnection("joining");
        stop();
      };
    };

    const join = async (): Promise<void> => {
      const [offered, view] = await Promise.all([readOfferings(), readGathering(seat)]);
      if (!attending.held) {
        return;
      }

      setOfferings(offered);
      hold(view);
      setTrouble(null);
      release = whileInView(document, following);
    };

    join().catch((refusal: unknown) => {
      if (attending.held) {
        setConnection("refused");
        setTrouble(reasonOf(refusal));
      }
    });

    return () => {
      attending.held = false;
      release?.();
    };
  }, [seat, hold]);

  return { gathering, offerings, connection, trouble, claim, tint, settle, ready, govern, callTheDeal };
}
