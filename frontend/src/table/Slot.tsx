import type { ReactElement } from "react";
import { useEffect, useRef, useState } from "react";

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
import type { Carry, Handling, Places, Point } from "./dragging";
import { carriedTo, grasped, laidOut, sent, travelled } from "./dragging";
import { fanning } from "./sizing";

/** How many cards of a heap a card that lands on it comes to rest on, which is the one it covers. */
const RESTING_ON = 1;

/** Which children of a run are the places it draws, which is every card lying in it. */
const DRAWN = ":scope > .card";

/** What a player presses to leave a run as the table holds it, wherever the card in hand has been carried to. */
const ABANDONING = "Escape";

/** What the reach of a card divides by to stand at the middle of it, which lies midway along either side. */
const MIDWAY = 2;

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
 *
 * A zone whose order is this seat's own to set is laid out by hand: a card is taken hold of where it lies and
 * travels with the pointer that took it, the run closes up behind it and opens at the place it stands nearest,
 * and letting go sends the order it has come to lie in. The card under the hand and the run opening ahead of it
 * are one reading of one gesture, so the order a player is choosing is the order in front of them, and letting
 * the card go sends that reading from wherever on the page they let it go. A player leaves the run as it stood by
 * carrying the card home again or by pressing escape, and the table is what settles it either way: the cards lie
 * as the table holds them until the commit carrying the new order arrives, which is how every other command
 * reaches this page too.
 *
 * A press that carries a card no distance at all is a press, so a run a player also plays out of answers both.
 */
export function Slot({ slot, zone, arrivals, playing }: SlotProps): ReactElement {
  const [carrying, setCarrying] = useState<Carry | null>(null);
  const run = useRef<HTMLDivElement | null>(null);
  const places = useRef<Places | null>(null);
  const sorting = useRef(false);
  const cards = zone?.cards ?? [];
  const drawn = shownIn(slot.spread, cards, landedIn(arrivals, slot.zone));
  const sortable = laysOut(zone, drawn, cards);
  const shown = laidOut(drawn, carrying);
  const onto: Target = { commit: "zone", zone: slot.zone };
  const landing = offerTo(playing.standing, onto);
  const picking = picksIn(playing.standing, slot.zone);
  const held = carrying !== null;

  useEffect(() => {
    if (!held) {
      return undefined;
    }

    const abandon = (event: KeyboardEvent): void => {
      if (event.key === ABANDONING) {
        setCarrying(null);
      }
    };

    window.addEventListener("keydown", abandon);
    return () => {
      window.removeEventListener("keydown", abandon);
    };
  }, [held]);

  const release = (): void => {
    setCarrying(null);
  };

  const carry = (at: Point): Carry | null => {
    const where = places.current;
    return where === null ? null : carriedTo(carrying, where, at);
  };

  const lay = (at: Point): void => {
    const order = sent(drawn, carry(at));
    if (order !== null) {
      playing.arrange(
        slot.zone,
        order.map((card) => card.index),
      );
    }

    release();
  };

  const pick = (index: number): void => {
    if (!sorting.current) {
      playing.pick(slot.zone, index);
    }
  };

  const handling = (index: number): Handling | null =>
    sortable
      ? {
          carried: carrying !== null && carrying.from === index,
          travel: carrying !== null && carrying.from === index ? carrying.by : null,
          grasp: (at: Point) => {
            places.current = placesOf(run.current);
            sorting.current = false;
            if (places.current !== null) {
              setCarrying(grasped(index, places.current, at));
            }
          },
          carry: (at: Point) => {
            const carried = carry(at);
            if (carried !== null && travelled(carried, at)) {
              sorting.current = true;
            }

            setCarrying(carried);
          },
          release: lay,
          abandon: release,
        }
      : null;

  return (
    <section className={classes("slot", slot.spread, landing !== null && "live")}>
      <header className="slot-label">
        <span className="label">{slot.label}</span>
        {slot.counted && <span className="count">{cards.length}</span>}
      </header>
      <div ref={run} className={classes("cards", cards.length > shown.length && "deep")} style={fanning(shown.length)}>
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
          shown.map((lying) => (
            <CardFace
              key={lying.index}
              card={lying.card}
              selected={isSelected(playing.standing, slot.zone, lying.index)}
              dimmed={leadsNowhere(playing.standing, slot.zone, lying.index)}
              arriving={lying.arriving}
              onPick={
                picking
                  ? () => {
                      pick(lying.index);
                    }
                  : null
              }
              handling={handling(lying.index)}
            />
          ))
        )}
      </div>
    </section>
  );
}

/**
 * Where a run draws each of its places, read off the page as a card of it is taken hold of.
 *
 * A run keeps the places it was drawn with for the whole of a carry, so reading them once as the card comes up
 * answers every point the pointer goes on to stand at. They are read off the drawing itself, which is what lets a
 * fan of any size, closed up to whatever room its zone has, be carried through by the card the player can see.
 *
 * Returns:
 *     Where the places lie, and nothing for a run drawing none.
 */
function placesOf(run: HTMLDivElement | null): Places | null {
  const drawn = run === null ? [] : [...run.querySelectorAll(DRAWN)].map((place) => place.getBoundingClientRect());
  const first = drawn.at(0);
  if (first === undefined) {
    return null;
  }

  return {
    middles: drawn.map((place) => place.x + place.width / MIDWAY),
    along: first.y + first.height / MIDWAY,
  };
}

/**
 * Whether a player lays this zone out themselves, which the table says and the drawing of it has to allow.
 *
 * The table resolves who may order which zone, and a run drawn whole is what a player orders by hand: every card
 * of it is there to take hold of and to carry to, so the order they lay down names each position the zone holds.
 * A spread reading a zone by the card on top of it says the depth beneath in a figure instead.
 */
function laysOut(zone: ZoneView | undefined, drawn: Held[], cards: ProjectedCard[]): boolean {
  return (zone?.arrangeable ?? false) && drawn.length === cards.length;
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
