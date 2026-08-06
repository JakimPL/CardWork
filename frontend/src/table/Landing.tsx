import type { ReactElement } from "react";
import { useEffect, useRef } from "react";

import type { Target } from "../play/selection";
import type { Playing } from "../play/usePlay";
import { classes } from "./classes";
import { clicking } from "./clicks";
import { useLandings } from "./landings";

interface LandingProps {
  onto: Target;
  caption: string;
  label: string;
  playing: Playing;
}

/**
 * The place a move is sent by, drawn over whatever the page points at it with.
 *
 * A zone the cards in hand go into and a seat they are passed to are the same thing to a player: somewhere to put
 * the cards. So the place lies over the drawing of it, answers a click by sending the move, and says where it is
 * drawn for as long as it is drawn, which is what lets a hand carrying cards find it.
 *
 * The place under a hand carrying cards is marked as the one about to take them, so a player reads where the cards
 * are going while they are still holding them.
 *
 * @param onto - the place the move lands on, which stands for that place for as long as it is drawn.
 * @param caption - what the move does, as the game phrased it.
 * @param label - what the place is called, for a reader reaching the page by its words.
 */
export function Landing({ onto, caption, label, playing }: LandingProps): ReactElement {
  const { holds, aimed } = useLandings();
  const drawn = useRef<HTMLButtonElement | null>(null);

  useEffect(() => holds(onto, drawn.current), [holds, onto]);

  return (
    <button
      ref={drawn}
      type="button"
      className={classes("landing", aimed(onto) && "aimed")}
      title={caption}
      aria-label={label}
      onClick={clicking(() => {
        playing.commit(onto);
      })}
    />
  );
}
