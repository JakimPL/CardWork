import { describe, expect, it } from "vitest";

import type { Readout } from "../src/api/layout";
import { phaseCaption, seatReadouts, seatValue, tableReadouts, tableValue } from "../src/play/readouts";
import { aLayout, SEATED } from "./tables";

const POINTS: Readout = { field: "points", label: "Points", scope: "seat" };
const ROUND: Readout = { field: "round_number", label: "Round", scope: "table" };
const WINNER: Readout = { field: "winner", label: "Won by", scope: "table" };

const LAYOUT = aLayout({ readouts: [POINTS, ROUND, WINNER], phases: { passing: "Passing" } });

describe("the readouts a layout states", () => {
  it("divide by whom the field they name speaks about", () => {
    expect(tableReadouts(LAYOUT)).toEqual([ROUND, WINNER]);
    expect(seatReadouts(LAYOUT)).toEqual([POINTS]);
  });
});

describe("what a readout says", () => {
  it("reads a field of the whole table as the figure it holds", () => {
    expect(tableValue(SEATED, ROUND)).toBe("2");
  });

  it("reads a field the cursor holds nothing for as holding nothing", () => {
    expect(tableValue(SEATED, WINNER)).toBe("—");
  });

  it("reads a seat field at the place the seat sits", () => {
    expect(seatValue(SEATED, POINTS, 2)).toBe("8");
  });

  it("reads a seat field the cursor stands at nothing for as holding nothing", () => {
    expect(seatValue({ ...SEATED, points: null }, POINTS, 2)).toBe("—");
  });
});

describe("the phase in words", () => {
  it("reads as the game words it", () => {
    expect(phaseCaption(LAYOUT, SEATED)).toBe("Passing");
  });

  it("reads under its own name where the layout words it nowhere", () => {
    expect(phaseCaption(LAYOUT, { ...SEATED, phase: "between_rounds" })).toBe("between_rounds");
  });
});
