import { fetchEventSource } from "@microsoft/fetch-event-source";

import { parsed } from "./parsing";
import { reasonOf, refusalOf, Refused } from "./refusal";
import type { Credentials } from "./requests";

/** The name a stream's last frame arrives under, which carries why the table it followed was broken up. */
const CLOSED_EVENT = "closed";

/** How long a client waits before picking a stream up again, which is a moment rather than a pause. */
const AGAIN_AFTER = 100;

/** How long a client waits before reaching for a stream that dropped, which leaves the trouble time to pass. */
const AFTER_A_DROP = 1000;

/** A stream that has carried what it had, which is the word to ask again rather than a fault to report. */
class Ended extends Error {
  constructor() {
    super("the stream carried what it had and ended");
    this.name = "Ended";
  }
}

/** What a closing frame carries: the word left for whoever was following, and nothing where none was left. */
export interface Closed {
  reason: string | null;
}

/** What a client following a stream is told as frames land and as the stream carrying them fares. */
export interface Streamed<FrameT> {
  onOpen: () => void;
  onFrame: (frame: FrameT) => void;
  onClosed: (closed: Closed) => void;
  onDropped: (reason: string) => void;
  onRefused: (reason: string) => void;
}

/**
 * Follow one stream of the server's, and answer with the call that stops following.
 *
 * The stream is read over `fetch` rather than through an `EventSource`, since a client speaks through a header
 * and an `EventSource` sends none: putting the token in the address instead would write it into every log the
 * request passes through. What the browser's own stream gives up in exchange — the retry, and the
 * `Last-Event-ID` a dropped stream resumes from — this carries, so a client that falls off catches up from the
 * frame it acknowledged.
 *
 * A stream carries what the table has to say and ends there, so following one is a run of requests rather than
 * a single answer: each ending has the next asked for, picked up at the frame the last carried. Ending is what
 * puts every answer whole on the wire, so a host that hands an answer on once it is finished carries a table as
 * promptly as one that passes every write straight through.
 *
 * A following stands for as long as it is held, whichever way the page it was opened in is turned. Whether it
 * is worth a connection just now is the caller's to weigh, which `play/viewing.ts` weighs by what the player is
 * looking at.
 *
 * `onOpen` reads the following coming up rather than each request it is made of, so a page is told it is
 * current once and told again where a stream dropped and was reached for afresh.
 *
 * A stream ends of its own accord when the table it follows is broken up: a closing frame carries the word left
 * for the company, `onClosed` reads it, and the following stops there rather than reaching for the frame after.
 *
 * @param address - where the stream is read from, which carries the point it is picked up at.
 * @param event - the name the frames a client reads arrive under, the others being none of its business.
 * @param credentials - the credential the stream is followed as.
 * @param streamed - what to do as the stream opens, carries a frame, closes, drops, or is refused outright.
 */
export function follow<FrameT>(
  address: string,
  event: string,
  credentials: Credentials,
  streamed: Streamed<FrameT>,
): () => void {
  const stopped = new AbortController();
  let current = false;

  void fetchEventSource(address, {
    headers: credentials,
    signal: stopped.signal,
    openWhenHidden: true,
    async onopen(response: Response): Promise<void> {
      if (!response.ok) {
        throw await refusalOf(response);
      }

      if (!current) {
        current = true;
        streamed.onOpen();
      }
    },
    onmessage(message): void {
      if (message.event === event) {
        streamed.onFrame(parsed<FrameT>(message.data));
      } else if (message.event === CLOSED_EVENT) {
        streamed.onClosed(parsed<Closed>(message.data));
        stopped.abort();
      }
    },
    onclose(): void {
      throw new Ended();
    },
    onerror(trouble: unknown): number {
      if (trouble instanceof Refused) {
        throw trouble;
      }

      if (trouble instanceof Ended) {
        return AGAIN_AFTER;
      }

      current = false;
      streamed.onDropped(reasonOf(trouble));
      return AFTER_A_DROP;
    },
  }).catch((trouble: unknown) => {
    if (!stopped.signal.aborted) {
      streamed.onRefused(reasonOf(trouble));
    }
  });

  return () => stopped.abort();
}
