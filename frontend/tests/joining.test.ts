import { describe, expect, it } from "vitest";

import type { Seat } from "../src/api/seat";
import type { Standing } from "../src/play/joining";
import { codeIn, fragmentFor, seatIn, standingIn } from "../src/play/joining";

interface JoiningCase {
  description: string;
  fragment: string;
  seat: Seat | null;
  code: string | null;
}

const CASES: JoiningCase[] = [
  {
    description: "a table and the token holding a seat at it",
    fragment: "#table=green-baize&token=abc-123",
    seat: { table: "green-baize", token: "abc-123" },
    code: null,
  },
  {
    description: "a table named without its leading mark",
    fragment: "table=green-baize&token=abc-123",
    seat: { table: "green-baize", token: "abc-123" },
    code: null,
  },
  {
    description: "a table and the code that admits a guest to it, which is the address a host announces",
    fragment: "#table=green-baize&code=K10AJ2",
    seat: { table: "green-baize", token: null },
    code: "K10AJ2",
  },
  {
    description: "a table named alone, which is a tab that reached it another way",
    fragment: "#table=green-baize",
    seat: { table: "green-baize", token: null },
    code: null,
  },
  {
    description: "a token stated empty, which holds no seat",
    fragment: "#table=green-baize&token=",
    seat: { table: "green-baize", token: null },
    code: null,
  },
  {
    description: "a code stated empty, which admits nobody",
    fragment: "#table=green-baize&code=",
    seat: { table: "green-baize", token: null },
    code: null,
  },
  {
    description: "a table whose name was written out with a space in it",
    fragment: "#table=green%20baize",
    seat: { table: "green baize", token: null },
    code: null,
  },
  {
    description: "nothing at all, which is the address opened bare",
    fragment: "",
    seat: null,
    code: null,
  },
  {
    description: "a token offered for no table, which names no table to offer it at",
    fragment: "#token=abc-123",
    seat: null,
    code: null,
  },
];

const STANDING = CASES.filter((one): one is JoiningCase & { seat: Seat } => one.seat !== null);

describe("the seat a fragment names", () => {
  it.each(CASES)("$description", ({ fragment, seat }) => {
    expect(seatIn(fragment)).toEqual(seat);
  });
});

describe("the code a fragment carries", () => {
  it.each(CASES)("$description", ({ fragment, code }) => {
    expect(codeIn(fragment)).toEqual(code);
  });
});

describe("where a fragment leaves a tab standing", () => {
  it.each(CASES)("$description", ({ fragment, seat, code }) => {
    const standing: Standing = { seat, code };

    expect(standingIn(fragment)).toEqual(standing);
  });
});

describe("the fragment a tab is reached through", () => {
  it.each(STANDING)("reads back as the seat it was written for: $description", ({ seat }) => {
    expect(standingIn(fragmentFor(seat))).toEqual({ seat, code: null });
  });

  it("writes the table and the token alone, which is the whole of what a tab remembers", () => {
    expect(fragmentFor({ table: "green-baize", token: "abc-123" })).toBe("#table=green-baize&token=abc-123");
  });

  it("names the table alone for a tab that has yet to arrive, since a code is the host's to hand out", () => {
    const written = fragmentFor({ table: "green-baize", token: null });

    expect(codeIn(written)).toBeNull();
    expect(seatIn(written)).toEqual({ table: "green-baize", token: null });
  });
});
