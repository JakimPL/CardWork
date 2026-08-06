import { describe, expect, it } from "vitest";

import { ringOf } from "../src/table/placing";
import type { Run } from "../src/table/sizing";
import { crowding, overlapOf, spanning } from "../src/table/sizing";
import { aTableOf } from "./tables";

/** How wide a group lies and how many lines it lies in, read off the figures the style sheet is handed. */
function width(lines: Run[][]): number {
  return spanning(lines)["--widths"] ?? 0;
}

function standing(lines: Run[][]): number {
  return spanning(lines)["--lines"] ?? 0;
}

/** How much of a card the next one lies over, at its loosest and at its tightest. */
const LOOSE = 0.42;
const CLOSED = 0.72;

interface Overlap {
  description: string;
  held: number;
  reads: number;
}

const OVERLAPS: Overlap[] = [
  { description: "a hand of three lies as open as a fan opens", held: 3, reads: LOOSE },
  { description: "a hand of seven lies open still, which is where a fan starts closing up", held: 7, reads: LOOSE },
  { description: "a hand of ten lies closer than an open one", held: 10, reads: 0.54 },
  { description: "a hand of seventeen lies as close as a fan closes", held: 17, reads: CLOSED },
];

describe("how far a fan overlaps itself", () => {
  it.each(OVERLAPS)("reads as $description", ({ held, reads }: Overlap) => {
    expect(overlapOf(held)).toBeCloseTo(reads);
  });
});

/** The three arrangements a group is made of, at the sizes the games lay them out at. */
const HAND: Run = { spread: "fan", held: 5 };
const BLIND: Run = { spread: "row", held: 5 };
const TRAY: Run = { spread: "slot", held: 1 };
const HEAP: Run = { spread: "stack", held: 40 };

interface Span {
  description: string;
  lines: Run[][];
  wide: number;
  deep: number;
}

const SPANS: Span[] = [
  { description: "a heap of forty, which is read by the one card on top of it", lines: [[HEAP]], wide: 1, deep: 1 },
  { description: "a place holding the one card sealed in it", lines: [[TRAY]], wide: 1, deep: 1 },
  { description: "a row of five, which lies every card of itself side by side", lines: [[BLIND]], wide: 5, deep: 1 },
  {
    description: "a fan of five, which lies wider than one card and narrower than five",
    lines: [[HAND]],
    wide: 3.32,
    deep: 1,
  },
  {
    description: "a fan of seventeen, closed up as far as a fan closes",
    lines: [[{ spread: "fan", held: 17 }]],
    wide: 5.48,
    deep: 1,
  },
  {
    description: "the panel a showdown seat plays from, which is the three of them along one line",
    lines: [[HAND, BLIND, TRAY]],
    wide: 9.32,
    deep: 1,
  },
  {
    description: "the same three in two lines, the holdings above and the place a card is sealed in below",
    lines: [[HAND, BLIND], [TRAY]],
    wide: 8.32,
    deep: 2,
  },
  {
    description: "a group whose second line is the wider of the two, which is the width its cards are drawn to",
    lines: [[TRAY], [HAND, BLIND]],
    wide: 8.32,
    deep: 2,
  },
  {
    description: "a zone standing empty, whose outline keeps the place of a card",
    lines: [[{ spread: "fan", held: 0 }]],
    wide: 1,
    deep: 1,
  },
  {
    description: "a line holding no zone at all, which is what a spectator plays from",
    lines: [[]],
    wide: 1,
    deep: 1,
  },
  {
    description: "a group standing in no line at all, which lies as one line holding nothing",
    lines: [],
    wide: 1,
    deep: 1,
  },
];

describe("how wide a group of zones lies", () => {
  it.each(SPANS)("counts $description", ({ lines, wide, deep }: Span) => {
    expect(width(lines)).toBeCloseTo(wide);
    expect(standing(lines)).toBe(deep);
  });
});

interface Crowd {
  description: string;
  players: number;
  stacked: number;
  abreast: number;
  flanked: number;
}

const CROWDS: Crowd[] = [
  {
    description: "a table of two, whose one other seat faces the near edge with the sides standing empty",
    players: 2,
    stacked: 1,
    abreast: 1,
    flanked: 0,
  },
  {
    description: "a table of three, whose two other seats face it and share the whole width between them",
    players: 3,
    stacked: 1,
    abreast: 2,
    flanked: 0,
  },
  {
    description: "a table of four, one seat up each side and one facing, which is where the sides fill",
    players: 4,
    stacked: 1,
    abreast: 1,
    flanked: 1,
  },
  {
    description: "a table of five, one seat up each side and two facing",
    players: 5,
    stacked: 1,
    abreast: 2,
    flanked: 1,
  },
  {
    description: "a table of seven, two seats up each side and two facing",
    players: 7,
    stacked: 2,
    abreast: 2,
    flanked: 1,
  },
  {
    description: "a table nobody else sits at, which stands one seat's room at every side of itself",
    players: 1,
    stacked: 1,
    abreast: 1,
    flanked: 0,
  },
];

describe("how the seats crowd a table", () => {
  it.each(CROWDS)("reads $description", ({ players, stacked, abreast, flanked }: Crowd) => {
    const crowd = crowding(ringOf(aTableOf(players, 0)));

    expect(crowd["--stacked"]).toBe(stacked);
    expect(crowd["--abreast"]).toBe(abreast);
    expect(crowd["--flanked"]).toBe(flanked);
  });
});
