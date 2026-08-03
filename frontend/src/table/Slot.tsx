import type { ReactElement } from "react";

import type { Slot as Arrangement, Spread } from "../api/layout";
import type { ProjectedCard, ZoneView } from "../api/views";
import { isOpen, isSelected, offerTo, picksIn } from "../play/selection";
import type { Playing } from "../play/usePlay";
import { CardFace } from "./CardFace";
import { classes } from "./classes";
import { clicking } from "./clicks";

/** One card of a zone at the position it lies at, which is the position a move addressing it names. */
interface Held {
  index: number;
  card: ProjectedCard;
}

interface SlotProps {
  slot: Arrangement;
  zone: ZoneView | undefined;
  playing: Playing;
}

/**
 * One zone where the layout puts it: what it is called, how many cards it holds, and the cards themselves.
 *
 * How the cards lie against each other is the spread's to say and the geometry of it is this interface's own,
 * so a slot draws the same way whichever game laid it out. A zone standing empty keeps its place, since a
 * player reads a heap run out and a card yet to be sealed by the outline waiting for one.
 *
 * A zone the cards in hand can be sent onto lies under a place to send them, so a player commits by pointing
 * at where the cards go.
 */
export function Slot({ slot, zone, playing }: SlotProps): ReactElement {
  const cards = zone?.cards ?? [];
  const shown = shownIn(slot.spread, cards);
  const landing = offerTo(playing.standing, { commit: "zone", zone: slot.zone });
  const picking = picksIn(playing.standing, slot.zone);
  return (
    <section className={classes("slot", slot.spread, landing !== null && "live")}>
      <header className="slot-label">
        <span className="label">{slot.label}</span>
        {slot.counted && <span className="count">{cards.length}</span>}
      </header>
      <div className="cards">
        {landing !== null && (
          <button
            type="button"
            className="landing"
            title={landing.caption}
            aria-label={landing.caption}
            onClick={clicking(() => {
              playing.commit(landing.target);
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
              open={isOpen(playing.standing, slot.zone, held.index)}
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
 * The cards of a zone a spread shows, each at the position it lies at.
 *
 * A heap and a single place read by the card on top, which is the end a game lays on; a hand and a row read
 * by every card in them. The index travels with the card, so what is drawn on top of a heap is the card a
 * move naming that position addresses.
 */
function shownIn(spread: Spread, cards: ProjectedCard[]): Held[] {
  const held = cards.map((card, index) => ({ index, card }));
  switch (spread) {
    case "stack":
    case "slot":
      return held.slice(-1);
    case "fan":
    case "row":
      return held;
  }
}
