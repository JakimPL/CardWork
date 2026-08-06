import { describe, expect, it } from "vitest";

import { endingRead, offeringOf, runningTo, seatingsOf, settledOn } from "../src/play/choosing";
import { aChoice, CLIMBING, OFFERINGS, PASSING, SHOWDOWN } from "./rooms";

describe("the game one choice names", () => {
  it("is the offering the host holds the rules of", () => {
    expect(offeringOf(OFFERINGS, "climbing")).toEqual(CLIMBING);
  });

  it("is nothing where the host offers that game nowhere", () => {
    expect(offeringOf(OFFERINGS, "bridge")).toBeNull();
  });
});

describe("the tables a game seats", () => {
  it("run from the fewest seats it needs to the most it holds", () => {
    expect(seatingsOf(CLIMBING)).toEqual([2, 3, 4, 5]);
  });

  it("stand as one size for a game played at one", () => {
    expect(seatingsOf(SHOWDOWN)).toEqual([3]);
  });
});

describe("a choice carried onto another game", () => {
  it("keeps the table and the decks that game admits", () => {
    const settled = settledOn(aChoice({ players: 4, decks: 1 }), CLIMBING);

    expect(settled).toEqual(aChoice({ game: "climbing", players: 4, decks: 1 }));
  });

  it("takes the largest table that game seats where the one settled stands beyond it", () => {
    const settled = settledOn(aChoice({ players: 8 }), CLIMBING);

    expect(settled.players).toBe(5);
  });

  it("takes the smallest table that game seats where the one settled falls short of it", () => {
    const settled = settledOn(aChoice({ players: 2 }), SHOWDOWN);

    expect(settled.players).toBe(3);
  });

  it("takes the first count of decks that game is dealt from where the one settled is refused", () => {
    const settled = settledOn(aChoice({ game: "passing", decks: 2 }), CLIMBING);

    expect(settled.decks).toBe(1);
  });

  it("keeps a count of decks the game admits, which is what a game dealt from two of them offers", () => {
    const settled = settledOn(aChoice({ game: "climbing", decks: 2 }), PASSING);

    expect(settled.decks).toBe(2);
  });

  it("leaves the ending the company settled alone, which no game states for itself", () => {
    const settled = settledOn(aChoice(), CLIMBING);

    expect(settled.conclusion).toEqual(aChoice().conclusion);
  });
});

describe("a match set to run for a count of rounds", () => {
  it("ends on that count and on nothing else", () => {
    const settled = runningTo(aChoice(), 5);

    expect(settled.conclusion).toEqual({ rounds: 5, target: null, lead: null });
  });

  it("leaves the game and the table it was settled at alone", () => {
    const settled = runningTo(aChoice({ players: 4 }), 5);

    expect([settled.game, settled.players, settled.decks]).toEqual(["passing", 4, 1]);
  });
});

describe("how long a match runs, read out", () => {
  it("names the count of rounds a table states", () => {
    expect(endingRead({ rounds: 3, target: null, lead: null })).toBe("3 rounds");
  });

  it("names the score a match climbs to", () => {
    expect(endingRead({ rounds: null, target: 40, lead: null })).toBe("40 points");
  });

  it("names the margin a match is taken by", () => {
    expect(endingRead({ rounds: null, target: null, lead: 2 })).toBe("a lead of 2");
  });

  it("reads every clause out together, since the first of them met is the one it ends on", () => {
    expect(endingRead({ rounds: 6, target: 40, lead: null })).toBe("6 rounds, or 40 points");
  });

  it("says the game states its own ending where a table states no clause at all", () => {
    expect(endingRead({ rounds: null, target: null, lead: null })).toBe("as the game says");
  });

  it("reads a clause a table left out altogether the way it reads one stated as nothing", () => {
    expect(endingRead({ lead: 2 })).toBe("a lead of 2");
  });
});
