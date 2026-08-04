import { describe, expect, it } from "vitest";

import type { Run } from "../src/table/sizing";
import { overlapOf, spanning } from "../src/table/sizing";

/** How wide a group lies, read off the figure the style sheet is handed. */
function width(runs: Run[]): number {
  return spanning(runs)["--widths"] ?? 0;
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
  runs: Run[];
  reads: number;
}

const SPANS: Span[] = [
  { description: "a heap of forty, which is read by the one card on top of it", runs: [HEAP], reads: 1 },
  { description: "a place holding the one card sealed in it", runs: [TRAY], reads: 1 },
  { description: "a row of five, which lies every card of itself side by side", runs: [BLIND], reads: 5 },
  { description: "a fan of five, which lies wider than one card and narrower than five", runs: [HAND], reads: 3.32 },
  {
    description: "a fan of seventeen, closed up as far as a fan closes",
    runs: [{ spread: "fan", held: 17 }],
    reads: 5.48,
  },
  {
    description: "the panel a showdown seat plays from, which is the three of them together",
    runs: [HAND, BLIND, TRAY],
    reads: 9.32,
  },
  {
    description: "a zone standing empty, whose outline keeps the place of a card",
    runs: [{ spread: "fan", held: 0 }],
    reads: 1,
  },
  { description: "a group holding no zone at all, which is what a spectator plays from", runs: [], reads: 1 },
];

describe("how wide a group of zones lies", () => {
  it.each(SPANS)("counts $description", ({ runs, reads }: Span) => {
    expect(width(runs)).toBeCloseTo(reads);
  });
});
