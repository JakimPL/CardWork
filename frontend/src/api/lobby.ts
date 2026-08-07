import type {
  Admitted,
  Arriving,
  Choosing,
  Claiming,
  Dealing,
  GatheringView,
  Governing,
  Offering,
  Readying,
  Tinting,
} from "./gathering";
import { asking, SENDING, STATING, stating } from "./requests";
import { credentials, type Seat } from "./seat";
import { follow, type Streamed } from "./streaming";

const OFFERINGS = "/offerings";
const TABLES = "/tables";
const GUESTS = "guests";
const GATHERING = "gathering";
const GATHERING_EVENTS = "gathering/events";
const SEAT = "seat";
const TINT = "tint";
const CHOICE = "choice";
const DEAL = "deal";
const READY = "ready";
const GOVERNANCE = "governance";
const SINCE = "since";

/** What no credential at all is offered with, which is how a stranger arrives and how the offerings are read. */
const UNCREDENTIALED = {};

/** The name a gathering arrives under on the stream, which mirrors `cardserver.streams.GATHERING_EVENT`. */
const STANDING = "gathering";

/**
 * Every game this host offers, the tables each of them seats and the deck counts each is dealt from.
 *
 * Read without a credential, as the pack a table draws with is: what may be played here is public, and it is
 * the whole of what a page needs to draw a choice while holding the name of no game.
 */
export function readOfferings(): Promise<Offering[]> {
  return asking<Offering[]>(OFFERINGS, UNCREDENTIALED);
}

/**
 * The tables gathering at this host, which is what a page offers somebody who reached it bare.
 *
 * Read without a credential, as the offerings are: what admits a person is the code, so naming what is
 * gathering costs a table nothing and saves the one who was handed no address from guessing at a name.
 */
export function readTables(): Promise<string[]> {
  return asking<string[]>(TABLES, UNCREDENTIALED);
}

/**
 * Arrive at a table on the code that admits, answering with the token to speak through from then on.
 *
 * This is the one call a stranger makes, and the code is the whole of what it turns on: everything after it
 * reads the guest off the token minted here.
 *
 * @throws Refused when the code admits nobody, when the name is already read at the table, or when the table
 *     has been dealt and its gathering is over.
 */
export function arrive(table: string, arriving: Arriving): Promise<Admitted> {
  return stating<Admitted, Arriving>(gathered(table, GUESTS), SENDING, UNCREDENTIALED, arriving);
}

/** The gathering as this guest reads it: the company, what is settled, and where it stands. */
export function readGathering(seat: Seat): Promise<GatheringView> {
  return asking<GatheringView>(gathered(seat.table, GATHERING), credentials(seat));
}

/** Take a seat at the table, or stand up from the one held by naming none. */
export function claimSeat(seat: Seat, claiming: Claiming): Promise<GatheringView> {
  return stating<GatheringView, Claiming>(gathered(seat.table, SEAT), STATING, credentials(seat), claiming);
}

/** Take one of the company's tints, which is a guest's own to choose whether they hold a seat or stand by. */
export function chooseTint(seat: Seat, tinting: Tinting): Promise<GatheringView> {
  return stating<GatheringView, Tinting>(gathered(seat.table, TINT), STATING, credentials(seat), tinting);
}

/** Settle what the table plays, which every guest holding a seat may do. */
export function settleChoice(seat: Seat, choosing: Choosing): Promise<GatheringView> {
  return stating<GatheringView, Choosing>(gathered(seat.table, CHOICE), STATING, credentials(seat), choosing);
}

/** Call for the deal, which opens the table the company settled on and ends the gathering. */
export function deal(seat: Seat, dealing: Dealing): Promise<GatheringView> {
  return stating<GatheringView, Dealing>(gathered(seat.table, DEAL), SENDING, credentials(seat), dealing);
}

/** Commit to the settings as they stand, or take that commitment back, which every seated guest may do. */
export function commitReady(seat: Seat, readying: Readying): Promise<GatheringView> {
  return stating<GatheringView, Readying>(gathered(seat.table, READY), STATING, credentials(seat), readying);
}

/** Settle how the table is governed, democratically or by the host's own say, which its host alone may do. */
export function settleGovernance(seat: Seat, governing: Governing): Promise<GatheringView> {
  return stating<GatheringView, Governing>(gathered(seat.table, GOVERNANCE), STATING, credentials(seat), governing);
}

/**
 * Follow the gathering from one revision onward, and answer with the call that stops following.
 *
 * A gathering is a room rather than a record, so each frame carries the whole of how it stands. Holding the
 * stream is also what reads this guest as present, so the company a page draws is the company watching it.
 *
 * @param seat - the table followed and the token it is followed as.
 * @param since - the first revision wanted, which is the one past the view the client already holds.
 * @param streamed - what to do as the stream opens, carries a revision, drops, or is refused outright.
 */
export function followGathering(seat: Seat, since: number, streamed: Streamed<GatheringView>): () => void {
  return follow<GatheringView>(
    `${gathered(seat.table, GATHERING_EVENTS)}?${SINCE}=${since}`,
    STANDING,
    credentials(seat),
    streamed,
  );
}

/** The address one answer of a table's gathering stands at. */
function gathered(table: string, answer: string): string {
  return `${TABLES}/${encodeURIComponent(table)}/${answer}`;
}
