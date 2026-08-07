import { describe, expect, it } from "vitest";

import { foundingChoiceFor, foundingIn } from "../src/play/founding";
import { CLIMBING, PASSING } from "./rooms";

describe("the choice a founded table opens on", () => {
  it("seats the smallest table the game admits and deals from the first count of decks it names", () => {
    const choice = foundingChoiceFor(PASSING);

    expect(choice.game).toBe(PASSING.game);
    expect(choice.players).toBe(PASSING.seats.least);
    expect(choice.decks).toBe(PASSING.decks[0]);
  });

  it("runs to a plain count of rounds and lights the move hints, both the company settles once it gathers", () => {
    const choice = foundingChoiceFor(CLIMBING);

    expect(choice.conclusion.rounds).toBe(3);
    expect(choice.conclusion.target).toBeNull();
    expect(choice.cues).toBe(true);
  });
});

describe("the founding a stated table stands as", () => {
  it("holds the whole of it back until a table, a name and a game the host offers stand together", () => {
    expect(foundingIn({ table: "", name: "Ada", game: PASSING.game }, PASSING)).toBeNull();
    expect(foundingIn({ table: "green-baize", name: "  ", game: PASSING.game }, PASSING)).toBeNull();
    expect(foundingIn({ table: "green-baize", name: "Ada", game: "unheld" }, null)).toBeNull();
  });

  it("comes out named without the spaces a person types around the table and themselves", () => {
    const founding = foundingIn({ table: "  green-baize ", name: " Ada ", game: PASSING.game }, PASSING);

    expect(founding).not.toBeNull();
    expect(founding?.table).toBe("green-baize");
    expect(founding?.name).toBe("Ada");
    expect(founding?.choice.game).toBe(PASSING.game);
  });
});
