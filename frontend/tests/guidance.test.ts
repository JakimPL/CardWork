import { describe, expect, it } from "vitest";

import type { Layout, Plaque as Standing } from "../src/api/layout";
import type { PositionView } from "../src/api/views";
import { guidance } from "../src/play/guidance";
import type { Selection } from "../src/play/selection";
import { offersOf, prospect } from "../src/play/selection";
import {
  aDiscard,
  aGive,
  aLayout,
  aTake,
  atRest,
  aView,
  card,
  DISCARDING,
  GIVING,
  HAND,
  MATCH_OVER,
  offering,
  SEATED,
  TAKING,
} from "./tables";

const SEATS: Standing[] = [
  { seat: 0, name: "North", counts: [] },
  { seat: 1, name: "East", counts: [] },
  { seat: 2, name: "South", counts: [] },
];

const TURN = aLayout({ gestures: [TAKING, GIVING], plaques: SEATS });
const SETS = aLayout({ gestures: [DISCARDING], plaques: SEATS });

const DEALT = aView({ [HAND]: [card("9", "♦"), card("9", "♠"), card("4", "♦")] }, 1);
const A_TURN = offering(DEALT, [aTake([0]), aGive(2, [0])]);
const A_SET = offering(DEALT, [aDiscard([0, 1])]);

/** The same table with the turn standing elsewhere, and with it standing nowhere at all. */
const ELSEWHERE = aView({ [HAND]: DEALT.zones[HAND]?.cards ?? [] }, 1, { ...SEATED, to_act: [2] });
const SEVERAL = aView({ [HAND]: DEALT.zones[HAND]?.cards ?? [] }, 1, { ...SEATED, to_act: [0, 2] });
const AT_REST = aView({ [HAND]: DEALT.zones[HAND]?.cards ?? [] }, 1, { ...SEATED, to_act: [] });

/** The same table with the match played out, which the standing of the cursor decides. */
const OVER = aView({ [HAND]: [] }, 1, atRest(MATCH_OVER, [3, 5, 8], [0, 0, 1]));
const TIED = aView({ [HAND]: [] }, 1, atRest(MATCH_OVER, [8, 5, 8], [0, 0, 1]));

/** What the line under the cards says about one position and one selection. */
function said(layout: Layout, view: PositionView, selection: Selection | null, notice: string | null): string {
  return guidance(layout, view, prospect(offersOf(layout, view), selection), notice);
}

interface Case {
  description: string;
  said: string;
  expected: string;
}

const CASES: Case[] = [
  {
    description: "a turn standing with another seat, which reads as the name that seat plays under",
    said: said(TURN, ELSEWHERE, null, null),
    expected: "Waiting for South",
  },
  {
    description: "a turn several seats hold at once, which names every one of them",
    said: said(TURN, SEVERAL, null, null),
    expected: "Waiting for North, South",
  },
  {
    description: "a table nobody owes an action to, which stands on the rules rather than on a player",
    said: said(TURN, AT_REST, null, null),
    expected: "Waiting for the table",
  },
  {
    description: "a turn this seat holds with no move in it, which the settlement answers for",
    said: said(TURN, DEALT, null, null),
    expected: "Waiting for the table",
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
  {
    description: "a match played out, which reads as the seat the standing leaves it with",
    said: said(TURN, OVER, null, null),
    expected: "South took the match",
  },
  {
    description: "a match two seats end level on, which names both of them",
    said: said(TURN, TIED, null, null),
    expected: "North, South shared the match",
  },
];

describe("the line telling a player where they stand", () => {
  it.each(CASES)("reads $description", ({ said: spoken, expected }: Case) => {
    expect(spoken).toBe(expected);
  });

  it("names a seat by where it sits where the plaques name none", () => {
    const nameless = aLayout({ gestures: [TAKING] });

    expect(said(nameless, ELSEWHERE, null, null)).toBe("Waiting for Seat 2");
  });
});
