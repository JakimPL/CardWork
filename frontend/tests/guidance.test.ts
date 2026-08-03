import { describe, expect, it } from "vitest";

import { guidance } from "../src/play/guidance";
import type { Selection } from "../src/play/selection";
import { offersOf, prospect } from "../src/play/selection";
import { aDiscard, aGive, aLayout, aTake, aView, card, DISCARDING, GIVING, HAND, offering, TAKING } from "./tables";

const TURN = aLayout({ gestures: [TAKING, GIVING] });
const SETS = aLayout({ gestures: [DISCARDING] });

const DEALT = aView({ [HAND]: [card("9", "♦"), card("9", "♠"), card("4", "♦")] }, 1);
const A_TURN = offering(DEALT, [aTake([0]), aGive(2, [0])]);
const A_SET = offering(DEALT, [aDiscard([0, 1])]);

/** What the line under the cards says about one position and one selection. */
function said(layout: typeof TURN, view: typeof DEALT, selection: Selection | null, notice: string | null): string {
  return guidance(prospect(offersOf(layout, view), selection), notice);
}

interface Case {
  description: string;
  said: string;
  expected: string;
}

const CASES: Case[] = [
  {
    description: "a table this seat owes nothing to",
    said: said(TURN, DEALT, null, null),
    expected: "Nothing to play just now",
  },
  {
    description: "a turn this seat holds, with nothing picked up",
    said: said(TURN, A_TURN, null, null),
    expected: "Pick a card to play",
  },
  {
    description: "one card of a set picked up, with the set still short",
    said: said(SETS, A_SET, { zone: HAND, indices: [0] }, null),
    expected: "Pick another card",
  },
  {
    description: "a card picked up that no move can be built out of",
    said: said(SETS, A_SET, { zone: HAND, indices: [2] }, null),
    expected: "No move sends these cards",
  },
  {
    description: "a set complete, which reads as the words its gesture states",
    said: said(SETS, A_SET, { zone: HAND, indices: [0, 1] }, null),
    expected: DISCARDING.caption,
  },
  {
    description: "one card two moves can send, which reads as both of them",
    said: said(TURN, A_TURN, { zone: HAND, indices: [0] }, null),
    expected: `${TAKING.caption} · ${GIVING.caption}`,
  },
  {
    description: "a refusal the table answered with, which stands over anything else",
    said: said(TURN, A_TURN, { zone: HAND, indices: [0] }, "Seat 1 names one card at a time, and named 3"),
    expected: "Seat 1 names one card at a time, and named 3",
  },
];

describe("the line telling a player where they stand", () => {
  it.each(CASES)("reads $description", ({ said: spoken, expected }: Case) => {
    expect(spoken).toBe(expected);
  });
});
