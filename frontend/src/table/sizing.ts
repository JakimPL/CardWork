import type { CSSProperties } from "react";

/** The name the style sheet reads a holding's size under, which is what it overlaps a fan by. */
const HELD = "--held";

/** The names the sheet reads a station's place under, each a part of the area the cards lie in. */
const ACROSS = "--across";
const UP = "--up";

/** The middle of that area, and how far from it a station sits, all in parts of a hundred. */
const MIDDLE = 50;
const REACH_ACROSS = 33;
const REACH_UP = 36;

/** Half the way round the table, which is what the radians of a ring are measured against. */
const HALF_ROUND = Math.PI;
const HALVES = 2;

/** The near edge of the table, which the seat reading the page holds, and the whole way round it. */
const NEAR_EDGE = HALF_ROUND / HALVES;
const ROUND = HALF_ROUND * HALVES;

/** How fine a figure the sheet is handed, which is a hundredth of the area either way. */
const FINENESS = 100;

/** A style carrying a figure the sheet works its geometry out from, beside the properties React names. */
type Measured = CSSProperties & Record<string, number>;

/**
 * How many cards a fan holds, handed to the style sheet so a wide holding tightens rather than running off.
 *
 * The geometry stays in the sheet and the count is the one thing it takes from the table, which is what keeps
 * a hand of four and a hand of seventeen the same drawing at two overlaps. A custom property is how a figure
 * reaches CSS at all.
 */
export function fanning(held: number): Measured {
  return { [HELD]: held };
}

/**
 * Where one seat sits round the table, handed to the style sheet as a place in the area the cards lie in.
 *
 * The seat reading the page holds the near edge, since its own cards lie in the panel below it, and the seats
 * around it take the rest of the ring in the order play runs: a table of four reads left, across and right,
 * which is how a card table is drawn. The ring lies wider than it is tall, because a window does.
 *
 * @param turn - how far round the table the seat sits from the one reading the page.
 * @param players - how many seats the table holds, which the ring is divided into.
 */
export function stationing(turn: number, players: number): Measured {
  const angle = NEAR_EDGE + (turn * ROUND) / players;
  return {
    [ACROSS]: rounded(MIDDLE + REACH_ACROSS * Math.cos(angle)),
    [UP]: rounded(MIDDLE + REACH_UP * Math.sin(angle)),
  };
}

/** One figure at the fineness the sheet is handed, which is a hundredth of the area the cards lie in. */
function rounded(part: number): number {
  return Math.round(part * FINENESS) / FINENESS;
}
