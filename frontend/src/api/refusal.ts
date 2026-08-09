import { bodyOf } from "./parsing";

/** The status a position moved on is refused under, which mirrors `cardserver.errors.REFUSALS`. */
const CONFLICTED = 409;

/** What a failure is read as where whatever it arrived as says nothing in words. */
const UNSAID = "The server said nothing of what went wrong";

/**
 * A refusal in the shape a client can act on: what kind it was, and what the server made of it.
 *
 * Stated by hand because the adapter answers these from its exception handlers, which leaves them outside
 * the document the endpoints publish. The kind is the name of the rule that refused, so a client branches on
 * it, while the detail stays a sentence the games already phrase for a person to read.
 */
export interface ErrorBody {
  error: string;
  detail: string;
}

/** A refusal as it is raised through the client, carrying the status it arrived under. */
export class Refused extends Error {
  readonly status: number;
  readonly kind: string;

  constructor(status: number, body: ErrorBody) {
    super(body.detail);
    this.name = "Refused";
    this.status = status;
    this.kind = body.error;
  }
}

/**
 * The refusal one answer states, read out of its body whatever shape that arrived in.
 *
 * The server states every refusal of its own as a kind and a sentence, and this reads that straight through.
 * A body of another shape is read for as much as it holds and written out as it arrived for the rest, so a
 * refusal that came from somewhere else — a proxy in front of the table, a framework answering for itself —
 * reaches a person as the words it was made of. An answer whose body says nothing still refused the request,
 * so the status stands in for the sentence and the caller has something to show either way.
 */
export async function refusalOf(response: Response): Promise<Refused> {
  const body = await bodyOf<unknown>(response).catch(() => null);
  return new Refused(response.status, {
    error: sentenceOf(fieldOf(body, "error"), String(response.status)),
    detail: sentenceOf(fieldOf(body, "detail"), sentenceOf(response.statusText, UNSAID)),
  });
}

/**
 * Whether a refusal says the table has moved past the position a command was built on.
 *
 * The status is what says it rather than the name of the rule, since the adapter answers a game's own
 * refusal under the status of the rule it subclasses, and a client acting on this wants the whole family.
 */
export function movedOn(refusal: Refused): boolean {
  return refusal.status === CONFLICTED;
}

/**
 * What went wrong, in words, out of whatever a failure arrived as.
 *
 * A failure states itself in a sentence wherever it can, and one that states none is written out as it
 * stands, so what reaches a person is always something said about the trouble they are looking at.
 */
export function reasonOf(trouble: unknown): string {
  if (trouble instanceof Error) {
    return sentenceOf(trouble.message, trouble.name);
  }

  return sentenceOf(trouble, UNSAID);
}

/**
 * One thing a server said, as a sentence, and the words this client falls back on where it said none.
 *
 * Text arrives as itself. Anything else — the list of misstated fields a framework answers with, a number, a
 * shape stated somewhere upstream — is written out as it came, which keeps whatever was said in front of
 * whoever has to act on it.
 */
function sentenceOf(stated: unknown, otherwise: string): string {
  if (typeof stated === "string") {
    return stated === "" ? otherwise : stated;
  }

  return stated === undefined || stated === null ? otherwise : JSON.stringify(stated);
}

/** One field of whatever a body arrived as, and nothing where the body holds no such field. */
function fieldOf(body: unknown, field: string): unknown {
  if (typeof body !== "object" || body === null) {
    return undefined;
  }

  return (body as Record<string, unknown>)[field];
}
