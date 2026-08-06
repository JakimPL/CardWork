import type { Layout } from "./layout";
import type { ArrangementRequest, CommandAccepted, MoveRequest } from "./moves";
import { asking, SENDING, stating } from "./requests";
import { credentials, type Seat } from "./seat";
import { follow, type Streamed } from "./streaming";
import type { EventView, PositionView } from "./views";

const TABLES = "/tables";
const LAYOUT = "layout";
const VIEW = "view";
const EVENTS = "events";
const MOVES = "moves";
const ARRANGEMENTS = "arrangements";
const SINCE = "since";

/** The name a commit arrives under on the stream, which mirrors `cardserver.streams.COMMIT_EVENT`. */
const COMMIT = "commit";

/** How this seat lays the table out, which answers for the match and is read once as a client joins. */
export function readLayout(seat: Seat): Promise<Layout> {
  return asking<Layout>(endpoint(seat, LAYOUT), credentials(seat));
}

/** The table as this seat is entitled to see it, which is the position a client joins on. */
export function readView(seat: Seat): Promise<PositionView> {
  return asking<PositionView>(endpoint(seat, VIEW), credentials(seat));
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
function send(seat: Seat, answer: string, command: MoveRequest | ArrangementRequest): Promise<CommandAccepted> {
  return stating<CommandAccepted, MoveRequest | ArrangementRequest>(
    endpoint(seat, answer),
    SENDING,
    credentials(seat),
    command,
  );
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
 * @param seat - the table followed and the token it is followed as.
 * @param since - the first commit wanted, which is the count of commits the client already holds.
 * @param streamed - what to do as the stream opens, carries a commit, drops, or is refused outright.
 */
export function followCommits(seat: Seat, since: number, streamed: Streamed<EventView>): () => void {
  return follow<EventView>(`${endpoint(seat, EVENTS)}?${SINCE}=${since}`, COMMIT, credentials(seat), streamed);
}

/** The address one answer of a table stands at. */
function endpoint(seat: Seat, answer: string): string {
  return `${TABLES}/${encodeURIComponent(seat.table)}/${answer}`;
}
