import type { CSSProperties } from "react";

import type { Artwork } from "../api/artwork";
import type { Slot, Spread } from "../api/layout";
import type { PositionView } from "../api/views";
import type { Offered } from "../play/selection";
import type { Placement, Ring } from "./placing";
import { linesOf } from "./placing";

/** The names the sheet reads a fan's overlap and a group's width under, each in cards rather than pixels. */
const OVERLAP = "--overlap";
const WIDTHS = "--widths";

/** The name the sheet reads how many lines a group of zones lies in under. */
const LINES = "--lines";

/** The names the sheet reads a line's partings under: between the zones along it, and between the cards inside them. */
const PARTED = "--parted";
const JOINTED = "--jointed";

/** One line, which is the fewest a group of zones ever lies in. */
const ONE_LINE = 1;

/** One zone, which is the run a line has no parting to either side of. */
const ONE_ZONE = 1;

/** None of a thing, which is the depth of a middle nothing is shared at and the parting a lone zone stands with. */
const NOTHING = 0;

/** The names the sheet reads the proportions of a card under, both in the units the artwork was written in. */
const ASPECT_WIDTH = "--card-aspect-width";
const ASPECT_HEIGHT = "--card-aspect-height";

/** The names the sheet reads how the seats stand round the table under: up its sides, and across the near edge. */
const STACKED = "--stacked";
const ABREAST = "--abreast";
const FLANKED = "--flanked";

/** The names the sheet reads how deep the table lies under: the lines in the middle, and the lines at a seat. */
const LAID = "--laid";
const DEEPEST = "--deepest";

/** The two placements the felt divides its height between, which are the middle of the table and the seats round it. */
const MIDDLE: Placement = "shared";
const SEATED: Placement = "theirs";

/** One seat, which is the fewest a side of the table ever stands. */
const ONE_SEAT = 1;

/** Whether seats sit up the sides of the table, which is what the seats facing the near edge share the width with. */
const FLANKING = 1;
const CLEAR = 0;

/**
 * How much of a card the next one in a fan lies over, at its loosest and at its tightest.
 *
 * The tightest is the closest a run of them lies while the corner of every card still carries its index, which is
 * what a hand of any size is read by. A closed fan leaves just under a third of a card showing, so the whole of a
 * hand of twenty-six reads by running an eye down the left edge of it.
 */
const LOOSE = 0.42;
const CLOSED = 0.68;

/** The holding a fan lies open at, and how far each card past that closes the run of them up. */
const OPEN = 7;
const TIGHTENING = 0.04;

/** One card, which is the room a heap takes and the first card of any run. */
const ONE_CARD = 1;

/** How fine a figure the sheet is handed, which is a hundredth of the area either way. */
const FINENESS = 100;

/** A style carrying a figure the sheet works its geometry out from, beside the properties React names. */
type Measured = CSSProperties & Record<string, number>;

/** One zone as the fitting reads it: how its cards lie against each other, and how many lie there. */
export interface Run {
  spread: Spread;
  held: number;
}

/**
 * How much of a card the one lying over it in a fan covers, as a part of a card's width.
 *
 * A handful lies open enough to read every face, and a holding of a dozen and more closes up to the room it has,
 * so a hand of any size reads by running an eye down the corners of it. The figure is worked out where the cards
 * are counted, since the room a run of them needs is measured from that same overlap.
 *
 * @param held - how many cards lie in the fan.
 */
export function overlapOf(held: number): number {
  return Math.min(CLOSED, Math.max(LOOSE, LOOSE + (held - OPEN) * TIGHTENING));
}

/**
 * How a fan lies against itself, handed to the style sheet so a wide holding tightens rather than running off.
 *
 * @param held - how many cards the fan holds.
 */
export function fanning(held: number): Measured {
  return { [OVERLAP]: overlapOf(held) };
}

/**
 * How wide a group of zones lies and how many lines it lies in, counted in cards and in lines.
 *
 * A card is as tall as the room its group has for it: the panel a player plays from draws a hand of three at the
 * full height the window affords, and a hand of seventeen beside a row of five at the height their width leaves,
 * both read off one figure saying how many cards wide the group lies. A group standing in two lines is as wide as
 * the wider of them and divides the height it has between them, so every card of it is drawn at one size. What
 * either figure comes to in pixels is the sheet's, since the proportions of a card belong to the drawing of one.
 *
 * A line carries its partings as well — the ones between the zones lying along it, and the ones between the cards
 * a zone lays side by side — since a group measured to the width it was handed keeps the room those take out of
 * the width its cards are drawn to, and neither of them is a width the cards themselves can be counted in.
 *
 * @param lines - the zones of the group, gathered into the lines they lie in.
 */
export function spanning(lines: Run[][]): Measured {
  const widths = lines.map((line) => line.reduce((room, run) => room + running(run), 0));
  const partings = lines.map((line) => line.length - ONE_ZONE);
  const joints = lines.map((line) => line.reduce((count, run) => count + jointing(run), NOTHING));
  return {
    [WIDTHS]: rounded(Math.max(ONE_CARD, ...widths)),
    [LINES]: Math.max(ONE_LINE, lines.length),
    [PARTED]: Math.max(NOTHING, ...partings),
    [JOINTED]: Math.max(NOTHING, ...joints),
  };
}

/**
 * How the seats stand round the table, handed to the sheet so every one of them fits inside it.
 *
 * The seats up one side share the height the table has for them and the seats facing the near edge share its
 * width, so a table of seven draws the cards of a seat smaller than a table of four does. What the seats facing
 * the near edge have the width of is the middle of the table, which is the whole of it where the sides stand
 * empty and half of it where they hold seats.
 *
 * Every card on the table is drawn at that one height, the heaps in the middle with them: what a player reads of
 * another seat is a card the size of the card on the pile, since both of them are cards lying on the same table.
 * That height is the height the felt has left over once every name and every count on it is written, divided by
 * the lines of cards standing one above another, so the seats and the middle are handed the figures they need to
 * work it out: how many lines the middle lies in, and how many the deepest seat stands in.
 *
 * @param ring - the seats round the table, gathered by the side of it they sit at.
 * @param middle - the zones every seat shares, which lie between them.
 */
export function crowding(ring: Ring, middle: Slot[]): Measured {
  const flanked = ring.left.length > 0 || ring.right.length > 0;
  const seated = [...ring.left, ...ring.across, ...ring.right];
  const depths = seated.map((station) => linesOf(SEATED, station.slots).length);
  return {
    [STACKED]: Math.max(ONE_SEAT, ring.left.length, ring.right.length),
    [ABREAST]: Math.max(ONE_SEAT, ring.across.length),
    [FLANKED]: flanked ? FLANKING : CLEAR,
    [LAID]: middle.length === 0 ? NOTHING : linesOf(MIDDLE, middle).length,
    [DEEPEST]: Math.max(NOTHING, ...depths),
  };
}

/**
 * How tall a card stands to its width, handed to the sheet so a pack is drawn at the shape it was written in.
 *
 * Every card is measured from one height, and the width follows from these two figures: a table opened with a
 * pack states the size its pictures were written at, and a table drawing the glyphs the page carries keeps the
 * proportions the sheet holds for them.
 *
 * @param artwork - the pack in service, where a table was opened with one.
 */
export function shaping(artwork: Artwork | null): Measured {
  return artwork === null ? {} : { [ASPECT_WIDTH]: artwork.width, [ASPECT_HEIGHT]: artwork.height };
}

/**
 * Each line of a group as the fitting reads it, with the words of a turn taking the room of a card among them.
 *
 * The reading is the group as it stands rather than as it is drawn, so anything measuring a group before the page
 * holds one — a hand weighed against the width the window has for it — asks the same question of the same figures.
 *
 * @param lines - the zones of the group, gathered into the lines they lie in.
 * @param view - the table as this seat is served it, which is where the cards of a zone are counted.
 * @param said - the moves a turn is said in words by, which lie at the end of the last line.
 */
export function measuring(lines: Slot[][], view: PositionView, said: Offered[]): Run[][] {
  return lines.map((line, index) => [
    ...line.map((slot) => reading(slot, view)),
    ...(index === lines.length - 1 ? saying(said) : []),
  ]);
}

/** One zone as the fitting reads it, which is how its cards lie and how many of them the observer is served. */
function reading(slot: Slot, view: PositionView): Run {
  return { spread: slot.spread, held: view.zones[slot.zone]?.cards.length ?? 0 };
}

/** The room the words of a turn take, which is a card apiece and none at all where a turn is said in none. */
function saying(said: Offered[]): Run[] {
  return said.length === 0 ? [] : [{ spread: "row", held: said.length }];
}

/** How many cards wide one zone lies: a heap reads by one card, a row by all of them, a fan by its overlap. */
function running(run: Run): number {
  switch (run.spread) {
    case "stack":
    case "slot":
      return ONE_CARD;
    case "row":
      return Math.max(ONE_CARD, run.held);
    case "fan":
      return run.held <= ONE_CARD ? ONE_CARD : ONE_CARD + (run.held - ONE_CARD) * (1 - overlapOf(run.held));
  }
}

/** How many partings lie inside one zone: a row lays every card of itself apart, and the rest draw a single card. */
function jointing(run: Run): number {
  return run.spread === "row" ? Math.max(NOTHING, run.held - ONE_CARD) : NOTHING;
}

/** One figure at the fineness the sheet is handed, which is a hundredth of the area the cards lie in. */
function rounded(part: number): number {
  return Math.round(part * FINENESS) / FINENESS;
}
