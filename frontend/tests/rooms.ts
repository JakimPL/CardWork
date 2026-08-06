import type { Choice, Conclusion, GatheringView, Guest, Offering } from "../src/api/gathering";

/** The table these tests gather, and the guest whose page they are read as. */
export const TABLE = "green-baize";
export const CODE = "KQAJ72";
export const MINE = "Ada";

/** The games this host offers, one of them dealt from one deck or two and one of them played at one size. */
export const PASSING: Offering = { game: "passing", title: "Passing", seats: { least: 2, most: 8 }, decks: [1, 2] };
export const CLIMBING: Offering = { game: "climbing", title: "Climbing", seats: { least: 2, most: 5 }, decks: [1] };
export const SHOWDOWN: Offering = { game: "showdown", title: "Showdown", seats: { least: 3, most: 3 }, decks: [1] };
export const OFFERINGS: Offering[] = [PASSING, CLIMBING, SHOWDOWN];

/** A match ending on the clause a table states, which is a count of rounds where nothing else is said. */
export const RUNS_TO: Conclusion = { rounds: 3, target: null, lead: null };

export function aChoice(choice: Partial<Choice> = {}): Choice {
  return { game: PASSING.game, players: 3, decks: 1, conclusion: RUNS_TO, ...choice };
}

/** One guest of the company: the name they arrived under, the seat they hold, and whether their page is open. */
export function aGuest(name: string, seat: number | null, present = true): Guest {
  return { name, seat, present };
}

/** A gathering as one of its guests reads it, at whatever company and choice a test states. */
export function aGathering(company: Guest[], gathering: Partial<GatheringView> = {}): GatheringView {
  return {
    table: TABLE,
    code: CODE,
    company,
    choice: aChoice(),
    mine: MINE,
    revision: 4,
    dealt: false,
    ...gathering,
  };
}

/** A gathering whose every seat is taken, which is the one thing the deal waits on. */
export function aSeatedGathering(players: number): GatheringView {
  const company = [...Array(players).keys()].map((seat) => aGuest(seat === 0 ? MINE : `Guest ${seat}`, seat));
  return aGathering(company, { choice: aChoice({ players }) });
}
