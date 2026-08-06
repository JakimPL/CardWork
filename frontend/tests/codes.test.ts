import { describe, expect, it } from "vitest";

import { codeIn, ranksIn, readOut, written } from "../src/play/codes";

/** The hand these cases read, which is the one `tests/server/test_codes.py` reads on the other side. */
const HAND = ["K", "10", "A", "J", "2"];

/** Every rank of the deck, which mirrors `cardwork.cards.orders.RANK_SEQUENCE`. */
const EVERY_RANK = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"];

interface ReadingCase {
  description: string;
  offered: string;
  ranks: string[] | null;
}

const READINGS: ReadingCase[] = [
  { description: "a code written as it is drawn", offered: "K10AJ2", ranks: HAND },
  { description: "a code in lower case, which a person types either way", offered: "k10aj2", ranks: HAND },
  { description: "a code spoken apart, hyphenated and underscored at once", offered: "K 10-A_J 2", ranks: HAND },
  { description: "the ten taken before the one, which names no rank alone", offered: "10", ranks: ["10"] },
  { description: "two tens in a row, each read whole", offered: "1010", ranks: ["10", "10"] },
  { description: "every rank of the deck, the eight among them", offered: EVERY_RANK.join(""), ranks: EVERY_RANK },
  { description: "digits that read as no hand, since a leading zero names nothing", offered: "012345", ranks: null },
  { description: "a one standing alone", offered: "1", ranks: null },
  { description: "a zero standing alone", offered: "0", ranks: null },
  { description: "a ten with a one left over", offered: "101", ranks: null },
  { description: "a letter the deck holds no rank for", offered: "KZA", ranks: null },
  { description: "nothing offered at all", offered: "", ranks: null },
  { description: "nothing but the separators a code is written with", offered: " - ", ranks: null },
];

describe("the hand of ranks a code reads as", () => {
  it.each(READINGS)("$description", ({ offered, ranks }) => {
    expect(ranksIn(offered)).toEqual(ranks);
  });
});

describe("a hand written down", () => {
  it("reads back as the hand it was written for", () => {
    expect(written(HAND)).toBe("K10AJ2");
    expect(ranksIn(written(HAND))).toEqual(HAND);
  });
});

interface CodeCase {
  description: string;
  offered: string;
  code: string | null;
}

/** The cases `tests/server/test_codes.py` holds `code_in` to, read here by the page that offers a code. */
const CODES: CodeCase[] = [
  { description: "six ranks written as a code is drawn", offered: "KQAJ72", code: "KQAJ72" },
  {
    description: "the same six as one person says them and another writes them down",
    offered: "k q-a_j 7 2",
    code: "KQAJ72",
  },
  { description: "six ranks holding the ten, which writes as seven characters", offered: "K10AJ72", code: null },
  { description: "a code one rank short", offered: "KQAJ7", code: null },
  { description: "a code one rank over", offered: "KQAJ722", code: null },
  { description: "six characters that read as no hand of ranks", offered: "012345", code: null },
];

describe("the code an offering stands as", () => {
  it.each(CODES)("$description", ({ offered, code }) => {
    expect(codeIn(offered)).toBe(code);
  });
});

describe("a code read out", () => {
  it("stands one rank apart from the next, which is how one person passes it to another", () => {
    expect(readOut("K10AJ2")).toBe("K 10 A J 2");
  });

  it("reads back as the same hand it was read out of", () => {
    expect(ranksIn(readOut("K10AJ2"))).toEqual(HAND);
  });

  it("reads a code however it was written down", () => {
    expect(readOut("k 10-a_j 2")).toBe("K 10 A J 2");
  });

  it("stands as it was offered where it reads as no hand of ranks at all", () => {
    expect(readOut("hello")).toBe("hello");
    expect(readOut("")).toBe("");
  });
});
