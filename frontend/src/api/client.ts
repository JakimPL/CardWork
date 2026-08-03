import { fetchEventSource } from "@microsoft/fetch-event-source";

import type { Layout } from "./layout";
import { reasonOf, Refused, refusalOf } from "./refusal";
import { credentials, type Seat } from "./seat";
import type { EventView, PositionView } from "./views";

const TABLES = "/tables";
const LAYOUT = "layout";
const VIEW = "view";
const EVENTS = "events";
const SINCE = "since";

/** The name a commit arrives under on the stream, which mirrors `cardserver.streams.COMMIT_EVENT`. */
const COMMIT = "commit";

/** What a client watching a table is told as commits land and as the stream carrying them fares. */
export interface Following {
  onOpen: () => void;
  onCommit: (event: EventView) => void;
  onDropped: (reason: string) => void;
  onRefused: (reason: string) => void;
}

/**
 * One answer of a table, read as the seat asking for it.
 *
 * The page and the endpoints come out of the same application, so an address of the table is a path and
 * nothing about where the page was loaded from reaches this.
 *
 * @throws Refused when the table answers anything other than the projection asked for.
 */
async function read<AnswerT>(seat: Seat, answer: string): Promise<AnswerT> {
  const response = await fetch(endpoint(seat, answer), { headers: credentials(seat) });
  if (!response.ok) {
    throw await refusalOf(response);
  }

  const body: AnswerT = await response.json();
  return body;
}

/** How this seat lays the table out, which answers for the match and is read once as a client joins. */
export function readLayout(seat: Seat): Promise<Layout> {
  return read<Layout>(seat, LAYOUT);
}

/** The table as this seat is entitled to see it, which is the position a client joins on. */
export function readView(seat: Seat): Promise<PositionView> {
  return read<PositionView>(seat, VIEW);
}

/**
 * Follow every commit from one sequence onward, and answer with the call that stops following.
 *
 * The stream is read over `fetch` rather than through an `EventSource`, since a seat is held by a header and
 * an `EventSource` sends none: putting the token in the address instead would write it into every log the
 * request passes through. What the browser's own stream gives up in exchange — the retry, and the
 * `Last-Event-ID` a dropped stream resumes from — this carries, so a client that falls off catches up from
 * the commit it acknowledged.
 *
 * @param seat - the table followed and the token it is followed as.
 * @param since - the first commit wanted, which is the count of commits the client already holds.
 * @param following - what to do as the stream opens, carries a commit, drops, or is refused outright.
 */
export function followCommits(seat: Seat, since: number, following: Following): () => void {
  const stopped = new AbortController();

  void fetchEventSource(`${endpoint(seat, EVENTS)}?${SINCE}=${since}`, {
    headers: credentials(seat),
    signal: stopped.signal,
    openWhenHidden: true,
    async onopen(response: Response): Promise<void> {
      if (!response.ok) {
        throw await refusalOf(response);
      }

      following.onOpen();
    },
    onmessage(message): void {
      if (message.event === COMMIT) {
        const event: EventView = JSON.parse(message.data);
        following.onCommit(event);
      }
    },
    onerror(trouble: unknown): void {
      if (trouble instanceof Refused) {
        throw trouble;
      }

      following.onDropped(reasonOf(trouble));
    },
  }).catch((trouble: unknown) => {
    if (!stopped.signal.aborted) {
      following.onRefused(reasonOf(trouble));
    }
  });

  return () => stopped.abort();
}

/** The address one answer of a table stands at. */
function endpoint(seat: Seat, answer: string): string {
  return `${TABLES}/${encodeURIComponent(seat.table)}/${answer}`;
}
