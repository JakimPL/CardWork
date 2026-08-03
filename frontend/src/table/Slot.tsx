import type { ReactElement } from "react";

import type { Slot as Arrangement, Spread } from "../api/layout";
import type { ProjectedCard, ZoneView } from "../api/views";
import { CardFace } from "./CardFace";
import { classes } from "./classes";

/** One card of a zone at the position it lies at, which is the position a move addressing it names. */
interface Held {
  index: number;
  card: ProjectedCard;
}

interface SlotProps {
  slot: Arrangement;
  zone: ZoneView | undefined;
}

/**
 * One zone where the layout puts it: what it is called, how many cards it holds, and the cards themselves.
 *
 * How the cards lie against each other is the spread's to say and the geometry of it is this interface's own,
 * so a slot draws the same way whichever game laid it out. A zone standing empty keeps its place, since a
 * player reads a heap run out and a card yet to be sealed by the outline waiting for one.
 */
export function Slot({ slot, zone }: SlotProps): ReactElement {
  const cards = zone?.cards ?? [];
  const shown = shownIn(slot.spread, cards);
  return (
    <section className={classes("slot", slot.spread)}>
      <header className="slot-label">
        <span className="label">{slot.label}</span>
        {slot.counted && <span className="count">{cards.length}</span>}
      </header>
      <div className="cards">
        {shown.length === 0 ? (
          <div className="card empty" aria-label={`${slot.label}, holding nothing`} />
        ) : (
          shown.map((held) => <CardFace key={held.index} card={held.card} />)
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
