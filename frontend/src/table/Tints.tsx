import type { ReactElement } from "react";

import type { GatheringView, Guest, Tint } from "../api/gathering";
import { myTint, tintHeldBy } from "../play/company";
import { TINTS } from "../play/tints";
import { classes } from "./classes";

/** What the row of swatches is called, which is the one thing a color says about whose it is. */
const YOURS = "Your color";

interface TintsProps {
  gathering: GatheringView;
  tint: (chosen: Tint) => void;
}

/**
 * The colors the company is told apart by: one swatch a tint, and one press to take a free one.
 *
 * A guest is handed a tint as they arrive and may take any the company has left, seated or standing alike, since
 * a color belongs to the guest rather than to the seat. The one this guest holds stands marked, and the ones
 * another guest holds are left to them, which is the answer the table gives as well.
 */
export function Tints({ gathering, tint }: TintsProps): ReactElement {
  const held = myTint(gathering);
  return (
    <div className="tints">
      <span className="color">{YOURS}</span>
      {TINTS.map((one) => (
        <Swatch key={one} gathering={gathering} one={one} held={held} tint={tint} />
      ))}
    </div>
  );
}

interface SwatchProps {
  gathering: GatheringView;
  one: Tint;
  held: Tint | null;
  tint: (chosen: Tint) => void;
}

/** One color of the eight: who holds it, whether it is this guest's, and the press that takes it. */
function Swatch({ gathering, one, held, tint }: SwatchProps): ReactElement {
  const holder = tintHeldBy(gathering, one);
  const own = one === held;
  const reading = reads(one, holder, own);
  return (
    <button
      type="button"
      className={classes("swatch", own && "own")}
      data-tint={one}
      title={reading}
      aria-label={reading}
      disabled={holder !== null && !own}
      onClick={() => {
        tint(one);
      }}
    />
  );
}

/** What one swatch says of itself: the color, and the guest holding it where somebody does. */
function reads(one: Tint, holder: Guest | null, own: boolean): string {
  if (own) {
    return `${one}, yours`;
  }

  return holder === null ? `${one}, free to take` : `${one}, held by ${holder.name}`;
}
