/**
 * The one place a served answer becomes a shape the compiler knows.
 *
 * A body arrives as text and the readers the platform supplies state no shape for what they read back, so the
 * shape is named here and nowhere else. Every caller beyond this module holds a typed answer, which is what
 * keeps the generated schema and the hand-written projections worth having.
 */
export async function bodyOf<BodyT>(response: Response): Promise<BodyT> {
  return (await response.json()) as BodyT;
}

/** One frame of a stream as the shape it carries, out of the text it arrived as. */
export function parsed<BodyT>(json: string): BodyT {
  return JSON.parse(json) as BodyT;
}
