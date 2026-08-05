import type { ReactElement } from "react";

import type { Offered } from "../play/selection";
import { isArmed, saidAlone } from "../play/selection";
import type { Playing } from "../play/usePlay";
import { clicking } from "./clicks";

/** What the panel calls the place a turn is said in, which stands where the label of a zone stands. */
const INSTEAD = "Instead of playing";

/** The keystroke that says a move, named as a keyboard names it and spelled as the tile letters it. */
const SHORTCUT = "Space";
const STROKE = "space";

interface WordsProps {
  offers: Offered[];
  playing: Playing;
}

/**
 * The place beside a hand where a turn is said rather than played, which is one tile for each move a word sends.
 *
 * A move naming no card is made nowhere among the cards, so what a player presses for one is a place of its own
 * at the end of the panel, lettered and drawn at the size of a card. It lies where the cards lie and takes the
 * room of one, which is what leaves it reading as somewhere on the table rather than as a control beside it.
 *
 * A tile keeps its place for as long as the table offers the move and goes quiet where the cards in hand stand
 * against it, so picking a card up leaves the hand lying where it lay. A turn standing ready to say one move and
 * one alone carries the keystroke that says it, since that is where a stroke leaves no question what it meant.
 *
 * @param offers - the moves a word sends, which the panel drawing them reads off the standing.
 * @param playing - the table as it is played, which says which of them are ready and takes the one said.
 */
export function Words({ offers, playing }: WordsProps): ReactElement {
  const alone = saidAlone(playing.standing);
  return (
    <section className="slot">
      <header className="slot-label">
        <span className="label">{INSTEAD}</span>
      </header>
      <div className="words">
        {offers.map((offer) => {
          const struck = offer === alone;
          return (
            <button
              key={offer.caption}
              type="button"
              className="word"
              disabled={!isArmed(playing.standing, offer)}
              title={offer.caption}
              aria-keyshortcuts={struck ? SHORTCUT : undefined}
              onClick={clicking(() => {
                playing.say(offer);
              })}
            >
              <span>{offer.caption}</span>
              {struck && (
                <span className="stroke" aria-hidden="true">
                  {STROKE}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
}
