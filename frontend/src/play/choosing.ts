import type { Choice, Conclusion, Offering } from "../api/gathering";

/** What a match ending on no clause at all reads as, which is a table whose game states its own ending. */
const OPEN_ENDED = "as the game says";

/** One of the clauses a match ends on, which a table states as the `Conclusion` it is opened with. */
type Clause = keyof Conclusion;

/** The clauses a match ends on, each under the words a person reads it by, in the order they are read out. */
const CLAUSES: [Clause, (stated: number) => string][] = [
  ["rounds", (stated) => `${stated} rounds`],
  ["target", (stated) => `${stated} points`],
  ["lead", (stated) => `a lead of ${stated}`],
];

/** The offering one game is played under, and nothing where the host offers it nowhere. */
export function offeringOf(offerings: Offering[], game: string): Offering | null {
  return offerings.find((offering) => offering.game === game) ?? null;
}

/** Every seating one game admits, which is what a control listing the tables it is played at reads. */
export function seatingsOf(offering: Offering): number[] {
  const { least, most } = offering.seats;
  return [...Array(most - least + 1).keys()].map((step) => least + step);
}

/**
 * One choice settled onto another game, at the table and the decks that game admits.
 *
 * A game seats its own tables and is dealt from its own counts of decks, so carrying a choice across keeps
 * whatever the game admits and takes the nearest it does otherwise. That leaves every choice the page can
 * reach one the server admits, and the server confirms it again regardless.
 */
export function settledOn(choice: Choice, offering: Offering): Choice {
  const { least, most } = offering.seats;
  return {
    ...choice,
    game: offering.game,
    players: Math.min(Math.max(choice.players, least), most),
    decks: dealtFrom(choice.decks, offering),
  };
}

/** One choice settled to run to a count of rounds, which is the ending a company states outright. */
export function runningTo(choice: Choice, rounds: number): Choice {
  return { ...choice, conclusion: { rounds, target: null, lead: null } };
}

/**
 * How long a match runs, in the words a person reads.
 *
 * A match stating several clauses ends on the first of them the standing meets, so they are read out together.
 */
export function endingRead(conclusion: Conclusion): string {
  const stated: string[] = [];
  for (const [clause, spoken] of CLAUSES) {
    const held = conclusion[clause];
    if (held !== null && held !== undefined) {
      stated.push(spoken(held));
    }
  }

  return stated.length === 0 ? OPEN_ENDED : stated.join(", or ");
}

/** The count of decks a choice carries onto another game, which is the nearest one that game is dealt from. */
function dealtFrom(decks: number, offering: Offering): number {
  return offering.decks.includes(decks) ? decks : (offering.decks[0] ?? decks);
}
