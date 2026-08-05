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
import type { Carry, Handling, Places, Point, Shift } from "./dragging";
import { carriedTo, grasped, laidOut, placesOf, restingOn, sent } from "./dragging";
import { fanning } from "./sizing";

/** How many cards of a heap a card that lands on it comes to rest on, which is the one it covers. */
const RESTING_ON = 1;

/** What a player presses to leave a run as the table holds it, wherever the card in hand has been carried to. */
const ABANDONING = "Escape";

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
 * travels with the pointer that took it, the run closes up behind it and opens at the place the card has come to
 * cover, and letting go sends the order it has come to lie in. The card under the hand and the run opening ahead
 * of it are one reading of one gesture, so the order a player is choosing is the order in front of them, and
 * letting the card go sends that reading from wherever on the page they let it go. A player leaves the run as it
 * stood by carrying the card home again or by pressing escape.
 *
 * The run stays laid out as the player laid it until the table hands that order back, so a card let go lies where
 * it was put and the commit carrying the order home changes nothing on screen. A card let go under the hand that
 * laid it stands raised where it came to rest, and eases nowhere, since the hand is still on it.
 *
 * A press that carries a card no distance at all is a press, so a run a player also plays out of answers both.
 */
export function Slot({ slot, zone, arrivals, playing }: SlotProps): ReactElement {
  const [carrying, setCarrying] = useState<Carry | null>(null);
  const [laid, setLaid] = useState<number | null>(null);
  const run = useRef<HTMLDivElement | null>(null);
  const places = useRef<Places | null>(null);
  const pressed = useRef(true);
  const cards = zone?.cards ?? [];
  const drawn = shownIn(slot.spread, cards, landedIn(arrivals, slot.zone));
  const sortable = laysOut(zone, drawn, cards);
  const read = arrangedBy(drawn, playing.laidIn(slot.zone));
  const shown = laidOut(read, carrying);
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
        pressed.current = false;
        setCarrying(null);
      }
    };

    window.addEventListener("keydown", abandon);
    return () => {
      window.removeEventListener("keydown", abandon);
    };
  }, [held]);

  const abandoned = (): void => {
    pressed.current = false;
    setCarrying(null);
  };

  const carry = (at: Point): Carry | null => {
    const where = places.current;
    return where === null ? null : carriedTo(carrying, where, at);
  };

  const rested = (going: Carry | null, at: Point): number | null => {
    const where = places.current;
    return going === null || where === null ? null : restingOn(going, where, at);
  };

  const lay = (at: Point): void => {
    const going = carry(at);
    const order = sent(read, going);
    if (order !== null) {
      playing.arrange(
        slot.zone,
        order.map((card) => card.index),
      );
    }

    if (going !== null) {
      pressed.current = going.by === null;
    }

    setLaid(rested(going, at));
    setCarrying(null);
  };

  const pick = (index: number): void => {
    if (pressed.current) {
      playing.pick(slot.zone, index);
    }
  };

  const handling = (place: number): Handling | null =>
    sortable
      ? {
          carried: travelOf(carrying, place) !== null,
          laid: laid === place,
          travel: travelOf(carrying, place),
          grasp: (at: Point) => {
            if (held) {
              return;
            }

            places.current = placesOf(run.current);
            pressed.current = true;
            setLaid(null);
            if (places.current !== null) {
              setCarrying(grasped(place, places.current, at));
            }
          },
          carry: (at: Point) => {
            if (laid !== null && laid !== place) {
              setLaid(null);
            }

            setCarrying((standing) => {
              const where = places.current;
              return where === null ? null : carriedTo(standing, where, at);
            });
          },
          release: lay,
          abandon: abandoned,
          leave: () => {
            if (laid === place) {
              setLaid(null);
            }
          },
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
          shown.map((lying, place) => (
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
              handling={handling(place)}
            />
          ))
        )}
      </div>
    </section>
  );
}

/**
 * One run in the order the player laid it out, and in the order the table holds it where they have laid none.
 *
 * A carry is read against the run as it is drawn, so an order laid by hand is applied before one is: the places a
 * card is taken from and carried to are places of the run in front of the player, which is what the order they
 * send is read off.
 *
 * A laid order names every card of the run once, and a run it no longer names is one the table has moved on from.
 */
function arrangedBy(drawn: Held[], order: number[] | null): Held[] {
  if (order === null) {
    return drawn;
  }

  const laid = order.flatMap((index) => drawn.filter((lying) => lying.index === index));
  return laid.length === drawn.length ? laid : drawn;
}

/** How far the card drawn at one place of a run stands from it, which is nothing for a card lying where it lies. */
function travelOf(carrying: Carry | null, place: number): Shift | null {
  return carrying !== null && carrying.to === place ? carrying.by : null;
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
