import type { ReactElement } from "react";

import type { Slot as Arrangement, Spread } from "../api/layout";
import type { ProjectedCard, ZoneView } from "../api/views";
import type { Arrivals } from "../play/arrivals";
import { landedIn } from "../play/arrivals";
import type { Target } from "../play/selection";
import { isSelected, leadsNowhere, offerTo, picksIn } from "../play/selection";
import type { Playing } from "../play/usePlay";
import { CardFace } from "./CardFace";
import { classes } from "./classes";
import { clicking } from "./clicks";
import { fanning } from "./sizing";

/** How many cards of a heap a card that lands on it comes to rest on, which is the one it covers. */
const RESTING_ON = 1;

/** One card of a zone at the position it lies at, which is the position a move addressing it names. */
interface Held {
  index: number;
  card: ProjectedCard;
  arriving: boolean;
}

interface SlotProps {
  slot: Arrangement;
  zone: ZoneView | undefined;
  arrivals: Arrivals;
  playing: Playing;
}

/**
 * One zone where the layout puts it: what it is called, how many cards it holds, and the cards themselves.
 *
 * How the cards lie against each other is the spread's to say and the geometry of it is this interface's own,
 * so a slot draws the same way whichever game laid it out. A zone standing empty keeps its place, since a
 * player reads a heap run out and a card yet to be sealed by the outline waiting for one.
 *
 * A heap reads by the card on top and the depth beneath it, and opens for a moment on the cards a commit has
 * just laid there, so a player reads what arrived before the heap closes over it.
 *
 * A zone the cards in hand can be sent onto lies under a place to send them, so a player commits by pointing
 * at where the cards go.
 */
export function Slot({ slot, zone, arrivals, playing }: SlotProps): ReactElement {
  const cards = zone?.cards ?? [];
  const shown = shownIn(slot.spread, cards, landedIn(arrivals, slot.zone));
  const onto: Target = { commit: "zone", zone: slot.zone };
  const landing = offerTo(playing.standing, onto);
  const picking = picksIn(playing.standing, slot.zone);
  return (
    <section className={classes("slot", slot.spread, landing !== null && "live")}>
      <header className="slot-label">
        <span className="label">{slot.label}</span>
        {slot.counted && <span className="count">{cards.length}</span>}
      </header>
      <div className={classes("cards", cards.length > shown.length && "deep")} style={fanning(shown.length)}>
        {landing !== null && (
          <button
            type="button"
            className="landing"
            title={landing.caption}
            aria-label={landing.caption}
            onClick={clicking(() => {
              playing.commit(onto);
            })}
          />
        )}
        {shown.length === 0 ? (
          <div className="card empty" aria-label={`${slot.label}, holding nothing`} />
        ) : (
          shown.map((held) => (
            <CardFace
              key={held.index}
              card={held.card}
              selected={isSelected(playing.standing, slot.zone, held.index)}
              dimmed={leadsNowhere(playing.standing, slot.zone, held.index)}
              arriving={held.arriving}
              onPick={
                picking
                  ? () => {
                      playing.pick(slot.zone, held.index);
                    }
                  : null
              }
            />
          ))
        )}
      </div>
    </section>
  );
}

/**
 * The cards of a zone a spread shows, each at the position it lies at and each saying whether it just landed.
 *
 * A heap and a single place read by the card on top, which is the end a game lays on, and by the cards just
 * laid there while they are still being read. A hand and a row read by every card in them. The index travels
 * with the card, so what is drawn on top of a heap is the card a move naming that position addresses.
 */
function shownIn(spread: Spread, cards: ProjectedCard[], landed: number): Held[] {
  const held = cards.map((card, index) => ({ index, card, arriving: index >= cards.length - landed }));
  switch (spread) {
    case "stack":
    case "slot":
      return held.slice(-(landed + RESTING_ON));
    case "fan":
    case "row":
      return held;
  }
}
