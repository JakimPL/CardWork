import { describe, expect, it } from "vitest";

import type { Seat } from "../src/api/seat";
import { fragmentFor, seatIn } from "../src/play/joining";

interface JoiningCase {
  description: string;
  fragment: string;
  seat: Seat | null;
}

const CASES: JoiningCase[] = [
  {
    description: "a table and the token holding a seat at it",
    fragment: "#table=green-baize&token=abc-123",
    seat: { table: "green-baize", token: "abc-123" },
  },
  {
    description: "a table named without its leading mark",
    fragment: "table=green-baize&token=abc-123",
    seat: { table: "green-baize", token: "abc-123" },
  },
  {
    description: "a table named alone, which is a tab watching it",
    fragment: "#table=green-baize",
    seat: { table: "green-baize", token: null },
  },
  {
    description: "a token stated empty, which holds no seat",
    fragment: "#table=green-baize&token=",
    seat: { table: "green-baize", token: null },
  },
  {
    description: "a table whose name was written out with a space in it",
    fragment: "#table=green%20baize",
    seat: { table: "green baize", token: null },
  },
  {
    description: "nothing at all, which is the address opened bare",
    fragment: "",
    seat: null,
  },
  {
    description: "a token offered for no table, which names no table to offer it at",
    fragment: "#token=abc-123",
    seat: null,
  },
];

describe("the seat a fragment names", () => {
  it.each(CASES)("$description", ({ fragment, seat }) => {
    expect(seatIn(fragment)).toEqual(seat);
  });
});

describe("the fragment a seat is reached through", () => {
  it.each(CASES.filter((one): one is JoiningCase & { seat: Seat } => one.seat !== null))(
    "reads back as the seat it was written for: $description",
    ({ seat }) => {
      expect(seatIn(fragmentFor(seat))).toEqual(seat);
    },
  );
});
