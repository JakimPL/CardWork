import { describe, expect, it } from "vitest";

import type { Layout, Slot } from "../src/api/layout";
import type { Offered } from "../src/play/selection";
import { ringOf, shared } from "../src/table/placing";
import type { Run } from "../src/table/sizing";
import { crowding, measuring, overlapOf, spanning } from "../src/table/sizing";
import {
  aBlind,
  aHolding,
  aLayout,
  aPass,
  aTableOf,
  aTray,
  aView,
  card,
  DEALT_FROM,
  handOf,
  HELD,
  LAID_ON,
  PILE,
  PLAQUES,
  SEAT,
  SEATS,
} from "./tables";

/** How wide a group lies and how many lines it lies in, read off the figures the style sheet is handed. */
function width(lines: Run[][]): number {
  return spanning(lines)["--widths"] ?? 0;
}

function standing(lines: Run[][]): number {
  return spanning(lines)["--lines"] ?? 0;
}

/** How many partings lie between the zones of the widest-parted line, which the sheet keeps out of its width. */
function parting(lines: Run[][]): number {
  return spanning(lines)["--parted"] ?? 0;
}

/** How many partings lie between the cards those zones lay side by side, which the sheet keeps out too. */
function jointing(lines: Run[][]): number {
  return spanning(lines)["--jointed"] ?? 0;
}

/** How much of a card the next one lies over, at its loosest and at its tightest. */
const LOOSE = 0.42;
const CLOSED = 0.68;

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
  parted: number;
  jointed: number;
}

const SPANS: Span[] = [
  {
    description: "a heap of forty, which is read by the one card on top of it",
    lines: [[HEAP]],
    wide: 1,
    deep: 1,
    parted: 0,
    jointed: 0,
  },
  {
    description: "a place holding the one card sealed in it",
    lines: [[TRAY]],
    wide: 1,
    deep: 1,
    parted: 0,
    jointed: 0,
  },
  {
    description: "a row of five, which lies every card of itself side by side",
    lines: [[BLIND]],
    wide: 5,
    deep: 1,
    parted: 0,
    jointed: 4,
  },
  {
    description: "a fan of five, which lies wider than one card and narrower than five",
    lines: [[HAND]],
    wide: 3.32,
    deep: 1,
    parted: 0,
    jointed: 0,
  },
  {
    description: "a fan of seventeen, closed up as far as a fan closes",
    lines: [[{ spread: "fan", held: 17 }]],
    wide: 6.12,
    deep: 1,
    parted: 0,
    jointed: 0,
  },
  {
    description: "the panel a showdown seat plays from, which is the three of them along one line",
    lines: [[HAND, BLIND, TRAY]],
    wide: 9.32,
    deep: 1,
    parted: 2,
    jointed: 4,
  },
  {
    description: "the same three in two lines, the holdings above and the place a card is sealed in below",
    lines: [[HAND, BLIND], [TRAY]],
    wide: 8.32,
    deep: 2,
    parted: 1,
    jointed: 4,
  },
  {
    description: "a group whose second line is the wider of the two, which is the width its cards are drawn to",
    lines: [[TRAY], [HAND, BLIND]],
    wide: 8.32,
    deep: 2,
    parted: 1,
    jointed: 4,
  },
  {
    description: "a zone standing empty, whose outline keeps the place of a card",
    lines: [[{ spread: "fan", held: 0 }]],
    wide: 1,
    deep: 1,
    parted: 0,
    jointed: 0,
  },
  {
    description: "a line holding no zone at all, which is what a spectator plays from",
    lines: [[]],
    wide: 1,
    deep: 1,
    parted: 0,
    jointed: 0,
  },
  {
    description: "a group standing in no line at all, which lies as one line holding nothing",
    lines: [],
    wide: 1,
    deep: 1,
    parted: 0,
    jointed: 0,
  },
];

describe("how wide a group of zones lies", () => {
  it.each(SPANS)("counts $description", ({ lines, wide, deep, parted, jointed }: Span) => {
    expect(width(lines)).toBeCloseTo(wide);
    expect(standing(lines)).toBe(deep);
    expect(parting(lines)).toBe(parted);
    expect(jointing(lines)).toBe(jointed);
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
    const layout = aTableOf(players, 0);
    const crowd = crowding(ringOf(layout), shared(layout));

    expect(crowd["--stacked"]).toBe(stacked);
    expect(crowd["--abreast"]).toBe(abreast);
    expect(crowd["--flanked"]).toBe(flanked);
  });
});

/** The three shapes of table the felt divides its height for, from the barest to the deepest. */
const SHARES_NOTHING: Layout = aTableOf(3, 0);

const SHARES_TWO_HEAPS: Layout = aLayout({
  slots: [...SEATS.filter((seat) => seat !== SEAT).map(aHolding), HELD, DEALT_FROM, LAID_ON],
  plaques: PLAQUES,
});

const SEALS_A_CARD: Layout = aLayout({
  slots: [...SEATS.flatMap((seat) => [aHolding(seat), aBlind(seat), aTray(seat)]), DEALT_FROM],
  plaques: PLAQUES,
});

interface Depth {
  description: string;
  layout: Layout;
  laid: number;
  deepest: number;
}

const DEPTHS: Depth[] = [
  {
    description: "a table sharing nothing, whose whole felt belongs to the seats round it",
    layout: SHARES_NOTHING,
    laid: 0,
    deepest: 1,
  },
  {
    description: "a table sharing two heaps, which lie along the one line between the seats",
    layout: SHARES_TWO_HEAPS,
    laid: 1,
    deepest: 1,
  },
  {
    description: "a table whose seats seal a card, which stands each of them a line deeper",
    layout: SEALS_A_CARD,
    laid: 1,
    deepest: 2,
  },
];

describe("how deep a table lies", () => {
  it.each(DEPTHS)("reads $description", ({ layout, laid, deepest }: Depth) => {
    const crowd = crowding(ringOf(layout), shared(layout));

    expect(crowd["--laid"]).toBe(laid);
    expect(crowd["--deepest"]).toBe(deepest);
  });
});

/** The table these readings are taken of: a hand of three, a pile of two, and a stack standing empty. */
const DRAWN = aView(
  {
    [handOf(SEAT)]: [card("A", "♠"), card("K", "♥"), card("Q", "♦")],
    [PILE]: [card("2", "♣"), card("3", "♣")],
  },
  1,
);

/** One move a turn is offered in words, which the fitting counts rather than reads. */
function offered(index: number): Offered {
  return { move: aPass(), picked: null, indices: [], target: null, caption: `Say ${index}` };
}

/** The words a turn is said in, which take the room of a card apiece at the end of the last line. */
function words(count: number): Run {
  return { spread: "row", held: count };
}

interface Reading {
  description: string;
  lines: Slot[][];
  said: number;
  reads: Run[][];
}

const READINGS: Reading[] = [
  {
    description: "a hand of three, counted as the cards the observer is served",
    lines: [[HELD]],
    said: 0,
    reads: [[{ spread: "fan", held: 3 }]],
  },
  {
    description: "a zone the observer holds no card of, which reads as the empty place it is",
    lines: [[LAID_ON]],
    said: 0,
    reads: [[{ spread: "stack", held: 0 }]],
  },
  {
    description: "a turn said in two words, which take the room of two cards at the end of the line",
    lines: [[HELD]],
    said: 2,
    reads: [[{ spread: "fan", held: 3 }, words(2)]],
  },
  {
    description: "the words standing at the end of the last line alone, whatever the lines above them hold",
    lines: [[HELD], [DEALT_FROM]],
    said: 1,
    reads: [[{ spread: "fan", held: 3 }], [{ spread: "stack", held: 2 }, words(1)]],
  },
];

describe("how a group of zones reads before it is drawn", () => {
  it.each(READINGS)("reads $description", ({ lines, said, reads }: Reading) => {
    const offers = [...Array(said).keys()].map(offered);

    expect(measuring(lines, DRAWN, offers)).toStrictEqual(reads);
  });
});
