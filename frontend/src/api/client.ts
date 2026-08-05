import { fetchEventSource } from "@microsoft/fetch-event-source";

import type { Layout } from "./layout";
import type { ArrangementRequest, CommandAccepted, MoveRequest } from "./moves";
import { bodyOf, parsed } from "./parsing";
import { reasonOf, refusalOf, Refused } from "./refusal";
import { credentials, type Seat } from "./seat";
import type { EventView, PositionView } from "./views";

const TABLES = "/tables";
const LAYOUT = "layout";
const VIEW = "view";
const EVENTS = "events";
const MOVES = "moves";
const ARRANGEMENTS = "arrangements";
const SINCE = "since";

const SENDING = "POST";
const CONTENT_TYPE = "content-type";
const JSON_BODY = "application/json";

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

  return bodyOf<AnswerT>(response);
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
 * Send one command up to a table, answering with the sequence the commit took.
 *
 * The command carries the position it was weighed against and a name for the attempt, so a table that has
 * moved on refuses it and a request sent twice under one name lands once. That much holds of both commands a
 * client sends, which is why they are answered alike.
 *
 * @throws Refused when the table turns the command down, which the status tells the kind of.
 */
async function send(seat: Seat, answer: string, command: MoveRequest | ArrangementRequest): Promise<CommandAccepted> {
  const response = await fetch(endpoint(seat, answer), {
    method: SENDING,
    headers: { ...credentials(seat), [CONTENT_TYPE]: JSON_BODY },
    body: JSON.stringify(command),
  });
  if (!response.ok) {
    throw await refusalOf(response);
  }

  return bodyOf<CommandAccepted>(response);
}

/** Send the move a player armed, which reaches the table as the intent its seat states. */
export function sendMove(seat: Seat, command: MoveRequest): Promise<CommandAccepted> {
  return send(seat, MOVES, command);
}

/**
 * Send the order a player laid one of its own zones out in.
 *
 * The seat is absent from the command: the token the request carries is what says whose zone is being sorted,
 * so a client states the zone and the run it comes to lie in and names no seat at all.
 */
export function sendArrangement(seat: Seat, command: ArrangementRequest): Promise<CommandAccepted> {
  return send(seat, ARRANGEMENTS, command);
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
 * One stream stands for as long as it is held, whichever way the page it was opened in is turned. Whether a
 * table is worth a connection just now is the caller's to weigh, which `play/viewing.ts` weighs by what the
 * player is looking at.
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
        following.onCommit(parsed<EventView>(message.data));
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
