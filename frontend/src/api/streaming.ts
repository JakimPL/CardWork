import { fetchEventSource } from "@microsoft/fetch-event-source";

import { parsed } from "./parsing";
import { reasonOf, refusalOf, Refused } from "./refusal";
import type { Credentials } from "./requests";

/** What a client following a stream is told as frames land and as the stream carrying them fares. */
export interface Streamed<FrameT> {
  onOpen: () => void;
  onFrame: (frame: FrameT) => void;
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
 * One stream stands for as long as it is held, whichever way the page it was opened in is turned. Whether it is
 * worth a connection just now is the caller's to weigh, which `play/viewing.ts` weighs by what the player is
 * looking at.
 *
 * @param address - where the stream is read from, which carries the point it is picked up at.
 * @param event - the name the frames a client reads arrive under, the others being none of its business.
 * @param credentials - the credential the stream is followed as.
 * @param streamed - what to do as the stream opens, carries a frame, drops, or is refused outright.
 */
export function follow<FrameT>(
  address: string,
  event: string,
  credentials: Credentials,
  streamed: Streamed<FrameT>,
): () => void {
  const stopped = new AbortController();

  void fetchEventSource(address, {
    headers: credentials,
    signal: stopped.signal,
    openWhenHidden: true,
    async onopen(response: Response): Promise<void> {
      if (!response.ok) {
        throw await refusalOf(response);
      }

      streamed.onOpen();
    },
    onmessage(message): void {
      if (message.event === event) {
        streamed.onFrame(parsed<FrameT>(message.data));
      }
    },
    onerror(trouble: unknown): void {
      if (trouble instanceof Refused) {
        throw trouble;
      }

      streamed.onDropped(reasonOf(trouble));
    },
  }).catch((trouble: unknown) => {
    if (!stopped.signal.aborted) {
      streamed.onRefused(reasonOf(trouble));
    }
  });

  return () => stopped.abort();
}
