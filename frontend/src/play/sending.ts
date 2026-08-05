import { sendArrangement, sendMove } from "../api/client";
import type { ArrangementRequest, CommandAccepted, Move, MoveRequest } from "../api/moves";
import { Refused } from "../api/refusal";
import type { Seat } from "../api/seat";
import type { ZoneId } from "../api/views";

/**
 * One command out of the move a player armed and the position they armed it against.
 *
 * The name of the attempt is what a table dedupes by, so it is made once here and travels with the command
 * through however many times the command is sent.
 */
export function commandFor(move: Move, seq: number, attempt: string): MoveRequest {
  return { move, base_seq: seq, idempotency_key: attempt };
}

/**
 * One command out of the order a player laid a zone of its own out in.
 *
 * `order` names the positions the zone holds in the run they come to lie in, so the first of them is the card
 * that comes to lie first. The seat is absent by the same rule a move's is not: a move states the seat it is
 * made for and an arrangement is made for whichever seat the token holds.
 */
export function orderFor(zone: ZoneId, order: number[], seq: number, attempt: string): ArrangementRequest {
  return { zone, order, base_seq: seq, idempotency_key: attempt };
}

/** A name for one attempt at a command, which two attempts never share. */
export function named(): string {
  return crypto.randomUUID();
}

/**
 * Send one command, and send it again where the first attempt reached no answer at all.
 *
 * A table that refuses a command has answered it, so a refusal stands as the outcome and is raised for the
 * player to read. A request that fell over on the way was answered by nobody, and the name the command carries
 * is what lets the same command go up again and land a single time whichever attempt arrived.
 *
 * @throws Refused when the table turns the command down.
 */
export function deliver(seat: Seat, command: MoveRequest): Promise<CommandAccepted> {
  return retrying(() => sendMove(seat, command));
}

/**
 * Send one order, and send it again where the first attempt reached no answer at all.
 *
 * @throws Refused when the table turns the order down.
 */
export function lay(seat: Seat, command: ArrangementRequest): Promise<CommandAccepted> {
  return retrying(() => sendArrangement(seat, command));
}

/** One attempt at a command and, where nobody answered the first, a second under the same name. */
async function retrying(attempt: () => Promise<CommandAccepted>): Promise<CommandAccepted> {
  try {
    return await attempt();
  } catch (trouble) {
    if (trouble instanceof Refused) {
      throw trouble;
    }

    return await attempt();
  }
}
