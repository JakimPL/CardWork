import type { Choice, Founding, Offering } from "../api/gathering";

/** How many rounds a table opens set to run for, which the host settles otherwise once the company gathers. */
const ROUNDS_OPENING = 3;

/** What a founder states to gather a table: the table's name, their own, and the game it opens on. */
export interface Foundation {
  table: string;
  name: string;
  game: string;
}

/**
 * The choice a table opens on, at the smallest table the game seats and the first count of decks it deals from.
 *
 * A founder names the game and the company settles the rest once the table is gathered, so what is drawn here is
 * the plainest choice the game admits, with the move hints lit for everyone until an advanced table turns them
 * off.
 */
export function foundingChoiceFor(offering: Offering): Choice {
  return {
    game: offering.game,
    players: offering.seats.least,
    decks: offering.decks[0] ?? 1,
    conclusion: { rounds: ROUNDS_OPENING, target: null, lead: null },
    cues: true,
  };
}

/**
 * The founding what was stated stands as, and nothing where it stands short of one.
 *
 * The lobby is told the whole of a founding at once, so the page holds it back until a table, a name and a game
 * the host offers stand together. What comes out is the form the lobby is told, the table and the name without
 * the spaces a person types around them.
 */
export function foundingIn(stated: Foundation, offering: Offering | null): Founding | null {
  const table = stated.table.trim();
  const name = stated.name.trim();
  if (table === "" || name === "" || offering === null) {
    return null;
  }

  return { table, name, choice: foundingChoiceFor(offering) };
}
