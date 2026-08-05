import type { CSSProperties } from "react";

import type { Artwork } from "../api/artwork";
import type { Spread } from "../api/layout";
import type { Ring } from "./placing";

/** The names the sheet reads a fan's overlap and a group's width under, each in cards rather than pixels. */
const OVERLAP = "--overlap";
const WIDTHS = "--widths";

/** The name the sheet reads how many lines a group of zones lies in under. */
const LINES = "--lines";

/** One line, which is the fewest a group of zones ever lies in. */
const ONE_LINE = 1;

/** The names the sheet reads the proportions of a card under, both in the units the artwork was written in. */
const ASPECT_WIDTH = "--card-aspect-width";
const ASPECT_HEIGHT = "--card-aspect-height";

/** The names the sheet reads how the seats stand round the table under: up its sides, and across the near edge. */
const STACKED = "--stacked";
const ABREAST = "--abreast";
const FLANKED = "--flanked";

/** One seat, which is the fewest a side of the table ever stands. */
const ONE_SEAT = 1;

/** Whether seats sit up the sides of the table, which is what the seats facing the near edge share the width with. */
const FLANKING = 1;
const CLEAR = 0;

/** How much of a card the next one in a fan lies over, at its loosest and at its tightest. */
const LOOSE = 0.42;
const CLOSED = 0.72;

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
 * @param lines - the zones of the group, gathered into the lines they lie in.
 */
export function spanning(lines: Run[][]): Measured {
  const widths = lines.map((line) => line.reduce((room, run) => room + running(run), 0));
  return { [WIDTHS]: rounded(Math.max(ONE_CARD, ...widths)), [LINES]: Math.max(ONE_LINE, lines.length) };
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
 *
 * @param ring - the seats round the table, gathered by the side of it they sit at.
 */
export function crowding(ring: Ring): Measured {
  const flanked = ring.left.length > 0 || ring.right.length > 0;
  return {
    [STACKED]: Math.max(ONE_SEAT, ring.left.length, ring.right.length),
    [ABREAST]: Math.max(ONE_SEAT, ring.across.length),
    [FLANKED]: flanked ? FLANKING : CLEAR,
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

/** One figure at the fineness the sheet is handed, which is a hundredth of the area the cards lie in. */
function rounded(part: number): number {
  return Math.round(part * FINENESS) / FINENESS;
}
