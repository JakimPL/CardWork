import type { ReactElement } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { Slot as Arrangement, Spread } from "../api/layout";
import type { ProjectedCard, ZoneView } from "../api/views";
import type { Arrivals } from "../play/arrivals";
import { landedIn } from "../play/arrivals";
import type { Target } from "../play/selection";
import { isSelected, leadsNowhere, offerTo, picksIn } from "../play/selection";
import type { Playing } from "../play/usePlay";
import { CardFace } from "./CardFace";
import { classes } from "./classes";
import type { Carry, Handling, Places, Point, Shift } from "./dragging";
import { carriedTo, grasped, heldAt, laidOut, placesOf, restingOn, sending, sent } from "./dragging";
import { Landing } from "./Landing";
import { released, useLandings } from "./landings";
import { fanning } from "./sizing";
import { Sorting } from "./Sorting";

/** How many cards of a heap a card that lands on it comes to rest on, which is the one it covers. */
const RESTING_ON = 1;

/** The fewest cards a run a player is offered an order for holds, which is a card and another to stand it beside. */
const ORDERABLE_FROM = 2;

/** What a player presses to leave a run as the table holds it, wherever the cards in hand have been carried to. */
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
 * A card of a zone a move picks in is taken hold of where it lies and carried to where it is going, together with
 * the cards already in hand where it is one of them. Carried clear of the run it came out of, it is picked up as a
 * click picks it up, the run stands as the table holds it, and the place the hand is over is marked as the one
 * about to take the cards: letting go there sends the move. Carried within a run whose order this seat sets, it
 * lays that order instead — the run closes up behind the cards and opens at the place they have come to cover, so
 * the order a player is choosing is the order in front of them, and letting go sends that reading from wherever on
 * the page they let it go. Letting go anywhere else puts the cards back down, as pressing escape does.
 *
 * The order of such a run is offered in words as well, at the name of the zone: one press for each way of reading a
 * hand, laying the whole run down in the order it asks for. It reaches the table by the road a carry through the run
 * takes, so a hand sorted stands on screen as a hand a player laid out themselves does.
 *
 * The run stays laid out as the player laid it until the table hands that order back, so cards let go lie where
 * they were put and the commit carrying the order home changes nothing on screen. A card let go under the hand
 * that laid it stands raised where it came to rest, and eases nowhere, since the hand is still on it.
 *
 * A press that carries a card no distance at all is a press, so a run a player plays out of answers both.
 */
export function Slot({ slot, zone, arrivals, playing }: SlotProps): ReactElement {
  const { at: reaching, aim } = useLandings();
  const [carrying, setCarrying] = useState<Carry | null>(null);
  const [laid, setLaid] = useState<number | null>(null);
  const run = useRef<HTMLDivElement | null>(null);
  const places = useRef<Places | null>(null);
  const grip = useRef<Carry | null>(null);
  const pressed = useRef(true);
  const cards = zone?.cards ?? [];
  const drawn = shownIn(slot.spread, cards, landedIn(arrivals, slot.zone));
  const orderable = laysOut(zone, drawn, cards);
  const read = arrangedBy(drawn, playing.laidIn(slot.zone));
  const shown = laidOut(read, carrying);
  const onto = useMemo<Target>(() => ({ commit: "zone", zone: slot.zone }), [slot.zone]);
  const landing = offerTo(playing.standing, onto);
  const picking = picksIn(playing.standing, slot.zone);
  const holding = carrying !== null;
  const inHand = read.flatMap((lying, place) => (isSelected(playing.standing, slot.zone, lying.index) ? [place] : []));

  /** The hand coming off the cards, which leaves nothing marked on the page and the run reading the table. */
  const letGo = useCallback(
    (resting: number | null): void => {
      grip.current = null;
      aim(null);
      setLaid(resting);
      setCarrying(null);
    },
    [aim],
  );

  useEffect(() => {
    if (!holding) {
      return undefined;
    }

    const abandon = (event: KeyboardEvent): void => {
      if (event.key === ABANDONING) {
        pressed.current = false;
        letGo(null);
      }
    };

    window.addEventListener("keydown", abandon);
    return () => {
      window.removeEventListener("keydown", abandon);
    };
  }, [holding, letGo]);

  /** The page taking the carry out of the player's hand, which puts the cards down as letting go of them does. */
  const abandoned = (): void => {
    pressed.current = false;
    if (grip.current !== null && sending(grip.current)) {
      playing.clear();
    }

    letGo(null);
  };

  /** The cards as the hand carrying them stands now, read against the run as it was drawn. */
  const carriedFrom = (at: Point): Carry | null => {
    const where = places.current;
    return where === null ? null : carriedTo(grip.current, where, at);
  };

  const rested = (going: Carry | null, at: Point): number | null => {
    const where = places.current;
    return going === null || where === null ? null : restingOn(going, where, at);
  };

  /** A carry out over the table, which picks the cards up as a click does and marks where they are headed. */
  const reach = (index: number, at: Point): void => {
    if (!isSelected(playing.standing, slot.zone, index)) {
      playing.pick(slot.zone, index);
    }

    aim(reaching(at));
  };

  const carry = (index: number, at: Point): void => {
    const going = carriedFrom(at);
    grip.current = going;
    setCarrying(going);
    if (going === null) {
      return;
    }

    if (sending(going)) {
      reach(index, at);
    } else {
      aim(null);
    }
  };

  /** The order the run has come to lie in, sent as the player let the cards go in it. */
  const order = (going: Carry | null): void => {
    const laying = sent(read, going);
    if (laying !== null) {
      playing.arrange(
        slot.zone,
        laying.map((card) => card.index),
      );
    }
  };

  const lay = (at: Point): void => {
    const going = carriedFrom(at);
    const letting = released(going, going !== null && sending(going) ? reaching(at) : null);
    switch (letting.lands) {
      case "sends":
        playing.commit(letting.target);
        break;
      case "orders":
        order(going);
        break;
      case "clears":
        playing.clear();
        break;
      case "presses":
        break;
    }

    pressed.current = letting.lands === "presses";
    letGo(rested(going, at));
  };

  /**
   * The click a card answers, which a carry that has just ended takes for itself.
   *
   * A carry ends in a press let go, and the page follows that with a click on the card the hand was on: the
   * gesture has been answered already, so the click it arrives with is the carry's own. It is the one click a
   * carry takes, which leaves every click after it — a card pressed, a card reached by the keyboard — picking
   * cards up the way it always has.
   */
  const pick = (index: number): void => {
    if (pressed.current) {
      playing.pick(slot.zone, index);
    }

    pressed.current = true;
  };

  const handling = (place: number, index: number): Handling | null =>
    orderable || picking
      ? {
          carried: travelOf(carrying, place) !== null,
          laid: laid === place,
          travel: travelOf(carrying, place),
          grasp: (at: Point) => {
            if (holding) {
              return;
            }

            places.current = placesOf(run.current, orderable);
            pressed.current = true;
            setLaid(null);
            if (places.current !== null) {
              grip.current = grasped(place, inHand, places.current, at);
              setCarrying(grip.current);
            }
          },
          carry: (at: Point) => {
            if (laid !== null && laid !== place) {
              setLaid(null);
            }

            carry(index, at);
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
    <section className={classes("slot", landing !== null && "live")} data-spread={slot.spread}>
      <header className="slot-label">
        <span className="label">{slot.label}</span>
        {slot.counted && <span className="count">{cards.length}</span>}
        {orderable && read.length >= ORDERABLE_FROM && (
          <Sorting
            run={read}
            onSort={(laying) => {
              playing.arrange(slot.zone, laying);
            }}
          />
        )}
      </header>
      <div ref={run} className={classes("cards", cards.length > shown.length && "deep")} style={fanning(shown.length)}>
        {landing !== null && (
          <Landing onto={onto} caption={landing.caption} label={landing.caption} playing={playing} />
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
              handling={handling(place, lying.index)}
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
 * A carry is read against the run as it is drawn, so an order laid by hand is applied before one is: the places
 * cards are taken from and carried to are places of the run in front of the player, which is what the order they
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
  return carrying !== null && heldAt(carrying).includes(place) ? carrying.by : null;
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
