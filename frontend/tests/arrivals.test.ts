import { describe, expect, it } from "vitest";

import { arrivalsOf, landedIn, NOTHING_LANDED } from "../src/play/arrivals";
import { aCommit, card, HAND, PILE, STACK } from "./tables";

/** The exchange `passing` is played by: a card off the pile, and the card given up laid face up on the stack. */
const EXCHANGE = aCommit(3, [
  { zone: HAND, before: [card("9", "♦"), card("8", "♠")], after: [card("9", "♦"), card("2", "♣")] },
  { zone: PILE, before: [null, null, null], after: [null, null] },
  { zone: STACK, before: [card("5", "♥")], after: [card("5", "♥"), card("8", "♠")] },
]);

/** A settlement of the kind `showdown` closes a turn with, which turns three sealed cards over at once. */
const SETTLEMENT = aCommit(7, [
  {
    zone: STACK,
    before: [card("5", "♥")],
    after: [card("5", "♥"), card("7", "♠"), card("J", "♦"), card("3", "♣")],
  },
]);

describe("the cards a commit laid down", () => {
  it("counts the card laid on a heap, at the heap it was laid on", () => {
    const arrivals = arrivalsOf(EXCHANGE);

    expect(landedIn(arrivals, STACK)).toBe(1);
  });

  it("counts none where a heap was drawn from", () => {
    const arrivals = arrivalsOf(EXCHANGE);

    expect(landedIn(arrivals, PILE)).toBe(0);
  });

  it("counts none where a holding traded one card for another", () => {
    const arrivals = arrivalsOf(EXCHANGE);

    expect(landedIn(arrivals, HAND)).toBe(0);
  });

  it("counts a settlement laying one card per seat as the group it is", () => {
    const arrivals = arrivalsOf(SETTLEMENT);

    expect(landedIn(arrivals, STACK)).toBe(3);
  });

  it("counts none where the cards of a zone were shuffled among themselves", () => {
    const shuffle = aCommit(1, [
      { zone: PILE, before: [card("2", "♣"), card("9", "♦")], after: [card("9", "♦"), card("2", "♣")] },
    ]);

    expect(arrivalsOf(shuffle).size).toBe(0);
  });

  it("counts none at a zone no commit has spoken about", () => {
    expect(landedIn(NOTHING_LANDED, STACK)).toBe(0);
  });
});
