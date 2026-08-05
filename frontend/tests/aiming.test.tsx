import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Layout } from "../src/api/layout";
import type { PositionView } from "../src/api/views";
import { NOTHING_LANDED } from "../src/play/arrivals";
import type { Selection, Target } from "../src/play/selection";
import { keyOf, offersOf, prospect } from "../src/play/selection";
import type { Playing } from "../src/play/usePlay";
import type { Carry, Places } from "../src/table/dragging";
import { grasped, sending, within } from "../src/table/dragging";
import type { Landed, Landings, Placed, Room } from "../src/table/landings";
import { Reachable, reachedAt, released } from "../src/table/landings";
import { shared, stations } from "../src/table/placing";
import { Station } from "../src/table/Station";
import { Zones } from "../src/table/Zones";
import {
  aGive,
  aLayout,
  aPlaying,
  AROUND,
  aTake,
  aView,
  card,
  DEALT_FROM,
  GIVING,
  HAND,
  handOf,
  HELD,
  LAID_ON,
  offering,
  PILE,
  PLAQUES,
  STACK,
  TAKING,
} from "./tables";

/** Where the run these tests carry cards out of is drawn, which is four places a hundred apart. */
const PLACES: Places = {
  middles: [100, 200, 300, 400],
  along: 500,
  reach: { across: 140, down: 190 },
  orderable: true,
};

/** A run drawing no place at all, which is a zone standing empty. */
const NONE: Places = { ...PLACES, middles: [] };

/** The card at the second place, pressed and carried nowhere at all, which is what a click leaves it. */
const PRESSING: Carry = grasped(1, [], PLACES, { across: 210, down: 505 });

/** The same card carried to another place of the run it came out of, which is a run being ordered. */
const THROUGH: Carry = { ...PRESSING, to: 2, by: { across: 4, down: 0 } };

/** The same card carried clear of that run, which is a card on its way somewhere else on the table. */
const AWAY: Carry = { ...PRESSING, to: null, by: { across: 30, down: -300 } };

/** The two places these tests carry cards onto: a zone of the table, and the seat a card is passed to. */
const ONTO: Target = { commit: "zone", zone: PILE };
const NEXT: Target = { commit: "seat", seat: 2 };

/** The room one place takes on the page, and the room a place drawn inside it takes. */
const AROUND_IT: Room = { at: { across: 100, down: 100 }, reach: { across: 200, down: 120 } };
const INSIDE_IT: Room = { at: { across: 140, down: 130 }, reach: { across: 60, down: 40 } };

const PLACED: Placed[] = [
  { target: ONTO, room: AROUND_IT },
  { target: NEXT, room: INSIDE_IT },
];

/** The whole of a `passing` table: the hand this seat plays out of, the pile it exchanges with, the seats round it. */
const LAYOUT: Layout = aLayout({
  slots: [HELD, ...AROUND, DEALT_FROM, LAID_ON],
  plaques: PLAQUES,
  gestures: [TAKING, GIVING],
});

const POSITION: PositionView = aView(
  {
    [HAND]: [card("9", "♦"), card("8", "♠"), card("4", "♦")],
    [handOf(0)]: [null, null],
    [handOf(2)]: [null, null],
    [PILE]: [null, null, null, null],
    [STACK]: [card("2", "♣")],
  },
  1,
);

/** The turn `passing` gives a seat: either card exchanged with the pile, or passed to the seat it plays into. */
const A_TURN: PositionView = offering(POSITION, [aTake([0]), aGive(2, [0])]);

/** The one card in hand, which arms both of those moves and lights the places they go to. */
const HOLDING: Selection = { zone: HAND, indices: [0] };

/** A page whose hand stands over one place, for a test reading how the places on it are drawn. */
function aiming(target: Target | null): Landings {
  return {
    holds: () => () => undefined,
    at: () => target,
    aim: () => undefined,
    aimed: (place) => target !== null && keyOf(place) === keyOf(target),
  };
}

/** The table as this seat plays it, holding the cards a selection names. */
function playing(view: PositionView, selection: Selection | null): Playing {
  return aPlaying(prospect(offersOf(LAYOUT, view), selection));
}

/** The zones the table shares, as they are drawn under a hand standing over one place of the page. */
function drawnShared(view: PositionView, selection: Selection | null, target: Target | null): string {
  return renderToStaticMarkup(
    <Reachable value={aiming(target)}>
      <Zones
        place="shared"
        slots={shared(LAYOUT)}
        view={view}
        arrivals={NOTHING_LANDED}
        playing={playing(view, selection)}
      />
    </Reachable>,
  );
}

/** The seats round the table, drawn the same way. */
function drawnSeated(view: PositionView, selection: Selection | null, target: Target | null): string {
  return renderToStaticMarkup(
    <Reachable value={aiming(target)}>
      {stations(LAYOUT).map((station) => (
        <Station
          key={station.seat}
          station={station}
          layout={LAYOUT}
          view={view}
          arrivals={NOTHING_LANDED}
          playing={playing(view, selection)}
        />
      ))}
    </Reachable>,
  );
}

/** How many cards of one drawing a player may take hold of. */
function grippable(drawing: string): number {
  return [...drawing.matchAll(/carryable/g)].length;
}

interface Lying {
  description: string;
  middle: { across: number; down: number };
  over: boolean;
}

const LYING: Lying[] = [
  {
    description: "a card lying at the middle of a place of the run",
    middle: { across: 250, down: 500 },
    over: true,
  },
  {
    description: "a card carried half of itself past the first place, which is where it is made the first of them",
    middle: { across: 30, down: 500 },
    over: true,
  },
  {
    description: "a card carried further past that, which is a card on its way off the run",
    middle: { across: 29, down: 500 },
    over: false,
  },
  {
    description: "a card carried half of itself past the last place, which is where it is made the last of them",
    middle: { across: 470, down: 500 },
    over: true,
  },
  {
    description: "a card carried further past that end",
    middle: { across: 471, down: 500 },
    over: false,
  },
  {
    description: "a card lifted half of itself above the run, which still lies along it",
    middle: { across: 250, down: 405 },
    over: true,
  },
  {
    description: "a card lifted clear of the run, which is the hand taking it out over the table",
    middle: { across: 250, down: 404 },
    over: false,
  },
  {
    description: "a card let down clear of the run below it",
    middle: { across: 250, down: 596 },
    over: false,
  },
];

describe("whether a card in hand lies over the run it came out of", () => {
  it.each(LYING)("reads $description", ({ middle, over }: Lying) => {
    expect(within(PLACES, middle)).toBe(over);
  });

  it("reads a run drawing no place at all as one no card lies over", () => {
    expect(within(NONE, { across: 250, down: 500 })).toBe(false);
  });
});

describe("whether the cards in hand are out over the table", () => {
  it("reads a hand carrying them clear of the run they came out of as taking them somewhere", () => {
    expect(sending(AWAY)).toBe(true);
  });

  it("reads a hand carrying them through that run as ordering it", () => {
    expect(sending(THROUGH)).toBe(false);
  });

  it("reads a press that carried them nowhere as neither", () => {
    expect(sending(PRESSING)).toBe(false);
  });
});

interface Letting {
  description: string;
  carrying: Carry | null;
  target: Target | null;
  lands: Landed["lands"];
}

const LETTING: Letting[] = [
  {
    description: "cards let go on a place are sent to it",
    carrying: AWAY,
    target: ONTO,
    lands: "sends",
  },
  {
    description: "cards let go in the run they came out of lay the order down",
    carrying: THROUGH,
    target: null,
    lands: "orders",
  },
  {
    description: "cards let go in that run lay it down even where a place lies under the hand",
    carrying: THROUGH,
    target: ONTO,
    lands: "orders",
  },
  {
    description: "cards let go over nothing at all go back down, as escape puts them down",
    carrying: AWAY,
    target: null,
    lands: "clears",
  },
  {
    description: "a press that carried them nowhere is the press it is, whatever lies under it",
    carrying: PRESSING,
    target: ONTO,
    lands: "presses",
  },
  {
    description: "a press on a card nothing was taken hold of by is a press",
    carrying: null,
    target: ONTO,
    lands: "presses",
  },
];

describe("what letting the cards go comes to", () => {
  it.each(LETTING)("reads $description", ({ carrying, target, lands }: Letting) => {
    expect(released(carrying, target).lands).toBe(lands);
  });

  it("carries the place the cards are sent to, which is the one the hand was over", () => {
    expect(released(AWAY, NEXT)).toEqual({ lands: "sends", target: NEXT });
  });
});

describe("the place one point stands over", () => {
  it("is the place whose room covers it, which a point at the middle of one stands over", () => {
    expect(reachedAt(PLACED, { across: 120, down: 150 })).toEqual(ONTO);
  });

  it("is the smallest of the places covering it, since the nearest is the one a hand means", () => {
    expect(reachedAt(PLACED, { across: 160, down: 150 })).toEqual(NEXT);
  });

  it("is the place a point standing exactly at the corner of it lies within", () => {
    expect(reachedAt(PLACED, { across: 300, down: 220 })).toEqual(ONTO);
  });

  it("is none for a point standing clear of every place", () => {
    expect(reachedAt(PLACED, { across: 90, down: 150 })).toBeNull();
    expect(reachedAt(PLACED, { across: 120, down: 900 })).toBeNull();
  });

  it("is none where the page draws no place a move is sent by", () => {
    expect(reachedAt([], { across: 120, down: 150 })).toBeNull();
  });
});

describe("a zone a move of this seat picks in", () => {
  it("offers every card of it to be taken hold of, whether or not the order of it is this seat's own", () => {
    const hand = renderToStaticMarkup(
      <Zones place="own" slots={[HELD]} view={A_TURN} arrivals={NOTHING_LANDED} playing={playing(A_TURN, null)} />,
    );

    expect(grippable(hand)).toBe(3);
  });

  it("offers none of a zone every move of this seat leaves alone", () => {
    expect(grippable(drawnShared(A_TURN, null, null))).toBe(0);
  });

  it("offers none of another seat's cards, since a move of this seat picks in none of them", () => {
    expect(grippable(drawnSeated(A_TURN, HOLDING, null))).toBe(0);
  });
});

describe("the place under a hand carrying cards", () => {
  it("is drawn as the one about to take them", () => {
    expect(drawnShared(A_TURN, HOLDING, ONTO)).toContain('class="landing aimed"');
  });

  it("is drawn plainly where the hand stands over some other place of the page", () => {
    const table = drawnShared(A_TURN, HOLDING, NEXT);

    expect(table).toContain('class="landing"');
    expect(table).not.toContain("aimed");
  });

  it("is the seat the cards are passed to where the hand is over that seat", () => {
    const seats = drawnSeated(A_TURN, HOLDING, NEXT);

    expect([...seats.matchAll(/class="landing aimed"/g)]).toHaveLength(1);
    expect(seats).toContain(`aria-label="${GIVING.caption}: Seat 2"`);
  });

  it("is none of them while the cards are still being picked", () => {
    expect(drawnShared(A_TURN, null, ONTO)).not.toContain("landing");
    expect(drawnSeated(A_TURN, null, NEXT)).not.toContain("landing");
  });
});
