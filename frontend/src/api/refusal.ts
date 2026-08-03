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
 * The refusal one answer states, read from its body where it holds one.
 *
 * An answer whose body says nothing a client can read still refused the request, so the status it carries
 * stands in for the sentence and the caller has something to show either way.
 */
export async function refusalOf(response: Response): Promise<Refused> {
  const body: ErrorBody | null = await response.json().catch(() => null);
  return new Refused(response.status, body ?? { error: String(response.status), detail: response.statusText });
}

/** What went wrong, in words, out of whatever a failure arrived as. */
export function reasonOf(trouble: unknown): string {
  return trouble instanceof Error ? trouble.message : String(trouble);
}
