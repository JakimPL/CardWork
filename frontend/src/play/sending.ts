import { sendMove } from "../api/client";
import type { Move, MoveAccepted, MoveRequest } from "../api/moves";
import { Refused } from "../api/refusal";
import type { Seat } from "../api/seat";

/**
 * One command out of the move a player armed and the position they armed it against.
 *
 * The name of the attempt is what a table dedupes by, so it is made once here and travels with the command
 * through however many times the command is sent.
 */
export function commandFor(move: Move, seq: number, attempt: string): MoveRequest {
  return { move, base_seq: seq, idempotency_key: attempt };
}

/** A name for one attempt at a move, which two attempts never share. */
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
export async function deliver(seat: Seat, command: MoveRequest): Promise<MoveAccepted> {
  try {
    return await sendMove(seat, command);
  } catch (trouble) {
    if (trouble instanceof Refused) {
      throw trouble;
    }

    return await sendMove(seat, command);
  }
}
