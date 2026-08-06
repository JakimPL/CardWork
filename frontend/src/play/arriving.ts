import { codeIn } from "./codes";

/** What a person states to arrive at a table: the table, the code that admits them, and the name to be read by. */
export interface Arrival {
  table: string;
  code: string;
  name: string;
}

/**
 * The arrival what was stated stands as, and nothing where it stands short of one.
 *
 * The lobby is told the whole of an arrival at once, so the page holds it back until a table, a code and a name
 * stand together. What comes out is the form the table is told: the code written the one way an address carries
 * it, and the table and the name without the spaces a person types around them.
 */
export function arrivalIn(stated: Arrival): Arrival | null {
  const table = stated.table.trim();
  const name = stated.name.trim();
  const code = codeIn(stated.code);
  if (table === "" || name === "" || code === null) {
    return null;
  }

  return { table, code, name };
}
