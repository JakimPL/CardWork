import { describe, expect, it } from "vitest";

import { turnOf } from "../src/play/seats";
import { ringOf, shared } from "../src/table/placing";
import { crowding } from "../src/table/sizing";
import { aHolding, aLayout, aTableOf } from "./tables";

/** The seats at each side of one table, read out in the order play runs round it. */
function seated(players: number, observer: number): Record<string, number[]> {
  const ring = ringOf(aTableOf(players, observer));
  return {
    left: ring.left.map((station) => station.seat),
    across: ring.across.map((station) => station.seat),
    right: ring.right.map((station) => station.seat),
  };
}

/** How many seats one table stands one above another, which is what its cards are drawn to fit. */
function stacked(players: number): number {
  const layout = aTableOf(players, 0);
  return crowding(ringOf(layout), shared(layout))["--stacked"] ?? 0;
}

interface Case {
  description: string;
  players: number;
  left: number[];
  across: number[];
  right: number[];
}

const CASES: Case[] = [
  {
    description: "a table of two, whose one other seat faces the near edge",
    players: 2,
    left: [],
    across: [1],
    right: [],
  },
  {
    description: "a table of three, whose two other seats face it together",
    players: 3,
    left: [],
    across: [1, 2],
    right: [],
  },
  {
    description: "a table of four, which reads left, across and right",
    players: 4,
    left: [1],
    across: [2],
    right: [3],
  },
  {
    description: "a table of five, whose pair across sits between one seat either side",
    players: 5,
    left: [1],
    across: [2, 3],
    right: [4],
  },
  {
    description: "a table of six, two up each side and one across",
    players: 6,
    left: [1, 2],
    across: [3],
    right: [4, 5],
  },
  {
    description: "a table of seven, two up each side and two across",
    players: 7,
    left: [1, 2],
    across: [3, 4],
    right: [5, 6],
  },
  {
    description: "a table of eight, three up each side",
    players: 8,
    left: [1, 2, 3],
    across: [4],
    right: [5, 6, 7],
  },
];

describe("the seats round the table", () => {
  it.each(CASES)("sits $description", ({ players, left, across, right }: Case) => {
    expect(seated(players, 0)).toEqual({ left, across, right });
  });

  it("reads the ring from the seat holding the page, whichever seat that is", () => {
    expect(seated(7, 3)).toEqual({ left: [4, 5], across: [6, 0], right: [1, 2] });
  });

  it("leaves out a seat whose cards the table draws nowhere, so the rest ring it as a smaller table", () => {
    const table = aLayout({
      observer: 0,
      players: 4,
      slots: [aHolding(1), aHolding(3)],
      plaques: [0, 1, 2, 3].map((seat) => ({ seat, name: `Seat ${seat}`, tint: null, counts: [] })),
    });
    const ring = ringOf(table);

    expect(ring.across.map((station) => station.seat)).toEqual([1, 3]);
    expect([ring.left, ring.right]).toEqual([[], []]);
  });
});

describe("how crowded a side of the table is", () => {
  it("counts the seats standing one above another, which the cards of all of them are drawn to fit", () => {
    expect([2, 4, 6, 7, 8].map(stacked)).toEqual([1, 1, 2, 2, 3]);
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
