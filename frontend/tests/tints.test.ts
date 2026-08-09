import { describe, expect, it } from "vitest";

import type { Tint } from "../src/api/gathering";
import { myTint, tintHeldBy } from "../src/play/company";
import { ownTint, tintOf } from "../src/play/seats";
import { TINTS } from "../src/play/tints";
import { aGathering, aGuest, MINE } from "./rooms";
import { aLayout, PLAQUES, TINTED } from "./tables";

/**
 * Every tint the endpoints declare, read as a name apiece.
 *
 * A reading keyed by the generated vocabulary is what holds the row of swatches to it: a tint added to
 * `cardwork.presentation.tint.Tint` leaves this short until it is written here, and the offer short until it is
 * written there.
 */
const EVERY: Record<Tint, true> = {
  rose: true,
  coral: true,
  amber: true,
  lemon: true,
  teal: true,
  azure: true,
  indigo: true,
  violet: true,
};

/** The tints two guests of these tests play under, which are two the company holds apart. */
const HERS: Tint = "teal";
const HIS: Tint = "amber";

describe("the tints a page offers", () => {
  it("offers every tint the room hands out, which is what a company of eight holds between them", () => {
    expect([...TINTS].sort()).toEqual(Object.keys(EVERY).sort());
  });

  it("offers each of them once, so no two guests are told apart by the same color", () => {
    expect(new Set(TINTS).size).toBe(TINTS.length);
  });

  it("stands them in the order a company arriving is handed them", () => {
    expect(TINTS[0]).toBe("rose");
  });
});

describe("the tint one guest of a gathering holds", () => {
  it("reads the tint of the guest whose page it is", () => {
    const room = aGathering([aGuest("Grace", 0, true, HIS), aGuest(MINE, 1, true, HERS)]);

    expect(myTint(room)).toBe(HERS);
  });

  it("reads nothing where the company holds nobody of that name, which is a room read as a stranger", () => {
    expect(myTint(aGathering([aGuest("Grace", 0, true, HIS)]))).toBeNull();
  });

  it("names the guest holding one, so the page leaves the colors another guest plays under to them", () => {
    const room = aGathering([aGuest("Grace", 0, true, HIS)]);

    expect(tintHeldBy(room, HIS)?.name).toBe("Grace");
  });

  it("holds nobody against a tint the company left free", () => {
    expect(tintHeldBy(aGathering([aGuest("Grace", 0, true, HIS)]), HERS)).toBeNull();
  });
});

describe("the tint one seat of a dealt table plays under", () => {
  it("reads it off the plaque that seat carries, which is where the room left it", () => {
    expect(TINTED.map((plaque) => tintOf(aLayout({ plaques: TINTED }), plaque.seat))).toEqual([
      "rose",
      "coral",
      "amber",
    ]);
  });

  it("reads nothing at a table served with no gathering behind it", () => {
    expect(tintOf(aLayout({ plaques: PLAQUES }), 0)).toBeNull();
  });

  it("reads the seat holding the page, which is what the panel it plays from stands in", () => {
    expect(ownTint(aLayout({ observer: 1, plaques: TINTED }))).toBe("coral");
  });

  it("reads nothing for somebody only watching, who plays from no seat", () => {
    expect(ownTint(aLayout({ observer: null, plaques: TINTED }))).toBeNull();
  });
});
