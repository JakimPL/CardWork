import type { CSSProperties } from "react";

/** The name the style sheet reads a holding's size under, which is what it overlaps a fan by. */
const HELD = "--held";

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
