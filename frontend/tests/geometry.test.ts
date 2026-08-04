import { describe, expect, it } from "vitest";

import { turnOf } from "../src/play/seats";
import { stationing } from "../src/table/sizing";
import { aLayout } from "./tables";

/** One place round the table, read off the figures the style sheet is handed. */
interface Place {
  across: number;
  up: number;
}

function placed(turn: number, players: number): Place {
  const measured = stationing(turn, players);
  return { across: measured["--across"] ?? 0, up: measured["--up"] ?? 0 };
}

/** The middle of the felt, which every place round the table is read against. */
const MIDDLE = 50;

/** As far round a table as these tests read, which is the six seats of the largest of them. */
const TURNS = [0, 1, 2, 3, 4, 5];

/** Every place round a table of one size, which is one for each seat at it. */
function around(players: number): Place[] {
  return TURNS.slice(0, players).map((turn) => placed(turn, players));
}

interface Case {
  description: string;
  turn: number;
  players: number;
  reads: (place: Place) => boolean;
}

const CASES: Case[] = [
  {
    description: "the near edge, which the seat reading the page holds and no station is drawn at",
    turn: 0,
    players: 4,
    reads: (place) => place.across === MIDDLE && place.up > MIDDLE,
  },
  {
    description: "the left of a table of four, which is the seat played into",
    turn: 1,
    players: 4,
    reads: (place) => place.across < MIDDLE && place.up === MIDDLE,
  },
  {
    description: "across a table of four",
    turn: 2,
    players: 4,
    reads: (place) => place.across === MIDDLE && place.up < MIDDLE,
  },
  {
    description: "the right of a table of four",
    turn: 3,
    players: 4,
    reads: (place) => place.across > MIDDLE && place.up === MIDDLE,
  },
  {
    description: "across a table of two, which is the one other seat at it",
    turn: 1,
    players: 2,
    reads: (place) => place.across === MIDDLE && place.up < MIDDLE,
  },
  {
    description: "the upper left of a table of three",
    turn: 1,
    players: 3,
    reads: (place) => place.across < MIDDLE && place.up < MIDDLE,
  },
  {
    description: "the upper right of a table of three",
    turn: 2,
    players: 3,
    reads: (place) => place.across > MIDDLE && place.up < MIDDLE,
  },
];

describe("where a seat sits round the table", () => {
  it.each(CASES)("reads as $description", ({ turn, players, reads }: Case) => {
    expect(reads(placed(turn, players))).toBe(true);
  });

  it("puts every seat of a table of six in a place of its own", () => {
    const places = around(6).map((place) => JSON.stringify(place));

    expect(new Set(places).size).toBe(6);
  });

  it("keeps every place inside the felt it lies in, at any size of table", () => {
    const places = [2, 3, 4, 6].flatMap(around);

    expect(places.every((place) => place.across > 0 && place.across < 100)).toBe(true);
    expect(places.every((place) => place.up > 0 && place.up < 100)).toBe(true);
  });
});

describe("how far round the table a seat sits", () => {
  it("counts from the seat reading the page, so its own turn is nought", () => {
    const layout = aLayout({ observer: 1, players: 4 });

    expect([0, 1, 2, 3].map((seat) => turnOf(layout, seat))).toEqual([3, 0, 1, 2]);
  });

  it("counts from the first seat for somebody only watching, who holds no seat to count from", () => {
    const layout = aLayout({ observer: null, players: 3 });

    expect([0, 1, 2].map((seat) => turnOf(layout, seat))).toEqual([0, 1, 2]);
  });
});
