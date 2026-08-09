import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Layout, Readout } from "../src/api/layout";
import type { PositionView } from "../src/api/views";
import { NOTHING_LANDED } from "../src/play/arrivals";
import type { Selection } from "../src/play/selection";
import { offersOf, prospect } from "../src/play/selection";
import { Header } from "../src/table/Header";
import type { Placement } from "../src/table/placing";
import { own, shared } from "../src/table/placing";
import { Zones } from "../src/table/Zones";
import {
  aDiscard,
  aGive,
  aLayout,
  aPlaying,
  aTake,
  aView,
  card,
  DEALT_FROM,
  DISCARDING,
  DRAWING,
  GIVING,
  HAND,
  HELD,
  LAID_ON,
  offering,
  PILE,
  PLAQUES,
  STACK,
  TAKING,
} from "./tables";

const POINTS: Readout = { field: "points", label: "Points", scope: "seat" };

const LAYOUT = aLayout({
  slots: [HELD, DEALT_FROM, LAID_ON],
  readouts: [POINTS],
  phases: { passing: "Passing" },
  plaques: PLAQUES,
  gestures: [TAKING, GIVING],
});

const WATCHING = aLayout({ observer: null, slots: [DEALT_FROM, LAID_ON], plaques: PLAQUES });

const POSITION: PositionView = aView(
  {
    [HAND]: [card("9", "♦"), card("8", "♠"), card("4", "♦")],
    [PILE]: [null, null, null, null],
    [STACK]: [card("2", "♣")],
  },
  1,
);

/** The turn `passing` gives a seat: either of two cards exchanged with the pile or passed to the next seat. */
const A_TURN = offering(POSITION, [aTake([0]), aTake([2]), aGive(2, [0]), aGive(2, [2])]);

/** The draw `shedding` offers, which names the card at the end of the heap and no other position of it. */
const DRAWS = aLayout({ slots: [HELD, DEALT_FROM, LAID_ON], plaques: PLAQUES, gestures: [DRAWING] });
const A_DRAW = offering(POSITION, [aTake([3])]);

/** A hand three of whose four cards read as one rank, as a game shedding sets of them deals one. */
const SETS = aLayout({ slots: [HELD, DEALT_FROM, LAID_ON], plaques: PLAQUES, gestures: [DISCARDING] });

const A_HAND: PositionView = aView(
  {
    [HAND]: [card("5", "♠"), card("5", "♥"), card("5", "♦"), card("9", "♣")],
    [PILE]: [null, null, null, null],
    [STACK]: [card("2", "♣")],
  },
  1,
);

const SHEDS = [aDiscard([0, 1]), aDiscard([0, 2]), aDiscard([1, 2]), aDiscard([0, 1, 2])];
const A_SET = offering(A_HAND, SHEDS);

/** The whole of a shedding turn: any set of the rank laid down, or the card at the end of the heap taken up. */
const TURNS = aLayout({ slots: [HELD, DEALT_FROM, LAID_ON], plaques: PLAQUES, gestures: [DISCARDING, DRAWING] });
const A_SET_OR_A_DRAW = offering(A_HAND, [...SHEDS, aTake([3])]);

/** How many cards of one drawing have gone quiet, which is what a player reads as out of play. */
function faded(drawing: string): number {
  return [...drawing.matchAll(/class="card [^"]*dimmed/g)].length;
}

/** How many cards of one drawing a player may press at all. */
function pressable(drawing: string): number {
  return [...drawing.matchAll(/<button/g)].length;
}

/** How many cards of one drawing stand raised, which is the whole of what being in hand marks. */
function raised(drawing: string): number {
  return [...drawing.matchAll(/aria-pressed="true"/g)].length;
}

function rendered(layout: Layout, view: PositionView, selection: Selection | null, place: Placement): string {
  const playing = aPlaying(prospect(offersOf(layout, view), selection));
  const slots = place === "own" ? own(layout) : shared(layout);
  return renderToStaticMarkup(
    <Zones place={place} slots={slots} view={view} arrivals={NOTHING_LANDED} playing={playing} />,
  );
}

function drawn(view: PositionView, selection: Selection | null, place: Placement): string {
  return rendered(LAYOUT, view, selection, place);
}

function standing(view: PositionView, selection: Selection | null): string {
  const playing = aPlaying(prospect(offersOf(LAYOUT, view), selection));
  return renderToStaticMarkup(<Header layout={LAYOUT} view={view} playing={playing} />);
}

describe("the cards a player may press", () => {
  it("fades the card no move names, and leaves the cards in play reading as cards", () => {
    const hand = drawn(A_TURN, null, "own");

    expect(faded(hand)).toBe(1);
    expect(pressable(hand)).toBe(3);
    expect(hand).not.toContain("open");
  });

  it("raises the card picked up, and fades the cards a move holding it cannot name beside it", () => {
    const hand = drawn(A_TURN, { zone: HAND, indices: [0] }, "own");

    expect(hand).toContain("selected");
    expect(raised(hand)).toBe(1);
    expect([...hand.matchAll(/aria-pressed="false"/g)]).toHaveLength(2);
    expect(faded(hand)).toBe(2);
  });

  it("presses nothing on a table this seat owes no move to, and fades nothing there either", () => {
    const hand = drawn(POSITION, null, "own");

    expect(pressable(hand)).toBe(0);
    expect(faded(hand)).toBe(0);
  });

  it("presses nothing at a table it is only watching", () => {
    const watched = renderToStaticMarkup(
      <Zones
        place="shared"
        slots={shared(WATCHING)}
        view={A_TURN}
        arrivals={NOTHING_LANDED}
        playing={aPlaying(prospect(offersOf(WATCHING, A_TURN), null))}
      />,
    );

    expect(pressable(watched)).toBe(0);
    expect(faded(watched)).toBe(0);
  });

  it("leaves a zone no move picks in reading as it lies, whatever the hand holds", () => {
    const table = drawn(A_TURN, { zone: HAND, indices: [0] }, "shared");

    expect(faded(table)).toBe(0);
  });

  it("fades no card where the table keeps its move hints out, and leaves every move it would name standing", () => {
    const playing = aPlaying(prospect(offersOf(LAYOUT, A_TURN), null), false);
    const hand = renderToStaticMarkup(
      <Zones place="own" slots={own(LAYOUT)} view={A_TURN} arrivals={NOTHING_LANDED} playing={playing} />,
    );

    expect(faded(hand)).toBe(0);
    expect(pressable(hand)).toBe(3);
  });
});

describe("the panel a player plays from", () => {
  it("marks itself while the table stands on this seat, as a plaque and a seat round the table do", () => {
    expect(drawn(A_TURN, null, "own")).toContain("zones own acting");
  });

  it("keeps that mark through the picking of the cards a move is made of", () => {
    expect(drawn(A_TURN, { zone: HAND, indices: [0] }, "own")).toContain("zones own acting");
  });

  it("stands its cards quiet where the table asks this seat for nothing, and marks none of them out", () => {
    const hand = drawn(POSITION, null, "own");

    expect(hand).toContain("zones own idle");
    expect(faded(hand)).toBe(0);
  });

  it("leaves the zones the table shares reading one way, since the turn belongs to a seat rather than to them", () => {
    expect(drawn(A_TURN, null, "shared")).toContain('class="zones shared"');
    expect(drawn(POSITION, null, "shared")).toContain('class="zones shared"');
  });
});

describe("a hand a set is picked out of", () => {
  it("fades the card of the odd rank from the moment the turn arrives", () => {
    const hand = rendered(SETS, A_SET, null, "own");

    expect(faded(hand)).toBe(1);
    expect(pressable(hand)).toBe(4);
  });

  it("keeps the rest of the rank reading plainly while one of them is in hand", () => {
    const hand = rendered(SETS, A_SET, { zone: HAND, indices: [0] }, "own");

    expect(faded(hand)).toBe(1);
    expect(raised(hand)).toBe(1);
  });

  it("holds the last of the rank open once the set stands complete, and sends it on a place rather than a card", () => {
    const hand = rendered(SETS, A_SET, { zone: HAND, indices: [0, 1] }, "own");
    const table = rendered(SETS, A_SET, { zone: HAND, indices: [0, 1] }, "shared");

    expect(faded(hand)).toBe(1);
    expect(raised(hand)).toBe(2);
    expect(table).toContain(`class="slot live" data-spread="stack"`);
    expect(table).toContain(`aria-label="${DISCARDING.caption}"`);
  });

  it("raises the whole of the rank once every card of it is in hand", () => {
    const hand = rendered(SETS, A_SET, { zone: HAND, indices: [0, 1, 2] }, "own");

    expect(faded(hand)).toBe(1);
    expect(raised(hand)).toBe(3);
  });
});

describe("a heap a player draws off", () => {
  it("leaves the card it shows reading as a card, which is the card a draw off the end of it names", () => {
    const table = rendered(DRAWS, A_DRAW, null, "shared");

    expect(faded(table)).toBe(0);
    expect(pressable(table)).toBe(1);
  });

  it("fades that card once a set is in hand, since a turn lays cards down or takes one up", () => {
    const resting = rendered(TURNS, A_SET_OR_A_DRAW, null, "shared");
    const holding = rendered(TURNS, A_SET_OR_A_DRAW, { zone: HAND, indices: [0] }, "shared");

    expect(faded(resting)).toBe(0);
    expect(faded(holding)).toBe(1);
  });

  it("sends the card onto the holding the game names, which is the seat's own", () => {
    const seat = rendered(DRAWS, A_DRAW, { zone: PILE, indices: [3] }, "own");

    expect(seat).toContain(`class="slot live" data-spread="fan"`);
    expect(seat).toContain(`aria-label="${DRAWING.caption}"`);
    expect([...seat.matchAll(/class="landing"/g)]).toHaveLength(1);
  });
});

describe("the places a selection can be sent onto", () => {
  it("lays a place to send onto over the zone a move commits to, under the words the game gives it", () => {
    const table = drawn(A_TURN, { zone: HAND, indices: [0] }, "shared");

    expect(table).toContain(`class="slot live" data-spread="stack"`);
    expect(table).toContain(`aria-label="${TAKING.caption}"`);
    expect([...table.matchAll(/class="landing"/g)]).toHaveLength(1);
  });

  it("lays one over the seat a move names, and over no other seat of the table", () => {
    const seats = standing(A_TURN, { zone: HAND, indices: [0] });

    expect([...seats.matchAll(/class="landing"/g)]).toHaveLength(1);
    expect(seats).toContain(`aria-label="${GIVING.caption}: Seat 2"`);
    expect([...seats.matchAll(/plaque[^"]*live/g)]).toHaveLength(1);
  });

  it("lays none anywhere while the cards are still being picked", () => {
    expect(drawn(A_TURN, null, "shared")).not.toContain("landing");
    expect(standing(A_TURN, null)).not.toContain("landing");
  });
});
