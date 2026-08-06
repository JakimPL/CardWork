import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { PositionView, ProjectedCard } from "../src/api/views";
import { NOTHING_LANDED } from "../src/play/arrivals";
import type { Direction, Lying, Ordering } from "../src/play/ordering";
import { orderedBy, turnedTo } from "../src/play/ordering";
import { prospect } from "../src/play/selection";
import type { Placement } from "../src/table/placing";
import { own, shared } from "../src/table/placing";
import { Zones } from "../src/table/Zones";
import { aLayout, aPlaying, aView, card, DEALT_FROM, HAND, HELD, LAID_ON, PILE, sortable, STACK } from "./tables";

/** The cards of a run at the positions the zone holds them at, which is a hand as the table hands it over. */
function run(...cards: ProjectedCard[]): Lying[] {
  return cards.map((card, index) => ({ index, card }));
}

/** The card standing for any other, which a display order gives a place of its own. */
function joker(red: boolean): ProjectedCard {
  return { card: { red }, face_down: false };
}

/** The run a press leaves lying, which is what the next press on it reads. */
function sortedBy(hand: Lying[], by: Ordering, way: Direction): Lying[] {
  return orderedBy(hand, by, way).flatMap((index) => hand.filter((lying) => lying.index === index));
}

/** A hand holding one rank twice, so an order by either figure has a tie in it for the other to break. */
const A_HAND: Lying[] = run(card("K", "♦"), card("2", "♠"), card("K", "♠"), card("7", "♥"));

/** The same hand as the player laid it out, whose positions read in an order other than the zone's own. */
const LAID: Lying[] = [
  { index: 2, card: card("K", "♠") },
  { index: 0, card: card("K", "♦") },
  { index: 3, card: card("7", "♥") },
  { index: 1, card: card("2", "♠") },
];

/** A hand holding a card of the deck, a card standing for any of them, and a place this seat reads no card at. */
const A_MIXED: Lying[] = run(joker(false), null, card("A", "♠"), card("2", "♦"));

/** The two orders a hand is put in and the two ends each is read from, for a case reading all four. */
const ORDERINGS: Ordering[] = ["rank", "suit"];
const DIRECTIONS: Direction[] = ["up", "down"];

const LAYOUT = aLayout({ slots: [HELD, DEALT_FROM, LAID_ON] });

/** A hand reading in no order at all, which is what a press on either figure has something to do to. */
const POSITION: PositionView = aView(
  {
    [HAND]: [card("9", "♦"), card("8", "♠"), card("4", "♦")],
    [PILE]: [null, null, null, null],
    [STACK]: [card("2", "♣"), card("5", "♥")],
  },
  4,
);

/** The same hand standing in rank order, which a press by rank turns round and a press by suit still sorts. */
const IN_ORDER: PositionView = aView(
  {
    [HAND]: [card("4", "♦"), card("8", "♠"), card("9", "♦")],
    [PILE]: [null, null, null, null],
    [STACK]: [card("2", "♣"), card("5", "♥")],
  },
  4,
);

/** A hand of one card, which lies in every order at once. */
const A_SINGLE: PositionView = aView({ [HAND]: [card("9", "♦")], [PILE]: [null], [STACK]: [card("2", "♣")] }, 4);

/** A table at rest, since what these cases read is the drawing of it rather than the moves it offers. */
const RESTING = aPlaying(prospect([], null));

function drawn(view: PositionView, place: Placement): string {
  const slots = place === "own" ? own(LAYOUT) : shared(LAYOUT);
  return renderToStaticMarkup(
    <Zones place={place} slots={slots} view={view} arrivals={NOTHING_LANDED} playing={RESTING} />,
  );
}

/** How many presses one drawing offers for putting a run in order. */
function presses(drawing: string): number {
  return [...drawing.matchAll(/class="sort"/g)].length;
}

describe("the order a press puts a hand in", () => {
  it("reads a hand by rank from the low card of it up, and breaks a tie of rank by suit", () => {
    expect(orderedBy(A_HAND, "rank", "up")).toEqual([1, 3, 2, 0]);
  });

  it("reads it from the high card down the other way, which stands the whole order on its head", () => {
    expect(orderedBy(A_HAND, "rank", "down")).toEqual([0, 2, 3, 1]);
  });

  it("reads a hand by suit in the order the deck declares them, and breaks a tie of suit by rank", () => {
    expect(orderedBy(A_HAND, "suit", "up")).toEqual([1, 2, 3, 0]);
  });

  it("reads the suits from the far end the other way, each of them still read by rank", () => {
    expect(orderedBy(A_HAND, "suit", "down")).toEqual([0, 3, 2, 1]);
  });

  it("names the positions the zone holds rather than the places on screen, so a hand laid out sorts as it lies", () => {
    expect(orderedBy(LAID, "rank", "up")).toEqual([1, 3, 2, 0]);
    expect(orderedBy(LAID, "suit", "up")).toEqual([1, 2, 3, 0]);
  });

  it("stands a card standing for any other past every card of the deck, and a place read as none after it", () => {
    expect(orderedBy(A_MIXED, "rank", "up")).toEqual([3, 2, 0, 1]);
    expect(orderedBy(A_MIXED, "suit", "up")).toEqual([2, 3, 0, 1]);
  });

  it("leaves two cards it tells apart by nothing lying as they lay, whichever end it is read from", () => {
    const jokers = run(joker(true), joker(false));

    expect(orderedBy(jokers, "rank", "up")).toEqual([0, 1]);
    expect(orderedBy(jokers, "suit", "down")).toEqual([0, 1]);
  });

  it("names every position of the run once, whichever figure it reads and whichever end it reads from", () => {
    for (const by of ORDERINGS) {
      for (const way of DIRECTIONS) {
        expect([...orderedBy(A_MIXED, by, way)].sort()).toEqual([0, 1, 2, 3]);
      }
    }
  });
});

describe("the end the next press reads an order from", () => {
  it("is the low card up, for a hand reading in no order the press would have put it in", () => {
    expect(turnedTo(A_HAND, "rank")).toBe("up");
    expect(turnedTo(A_HAND, "suit")).toBe("up");
  });

  it("is the far end for a hand already reading the way the press would put it", () => {
    expect(turnedTo(sortedBy(A_HAND, "rank", "up"), "rank")).toBe("down");
    expect(turnedTo(sortedBy(A_HAND, "suit", "up"), "suit")).toBe("down");
  });

  it("comes back round again once the run has been read from the far end, so two presses carry both", () => {
    const risen = sortedBy(A_HAND, "rank", "up");

    expect(turnedTo(sortedBy(risen, "rank", "down"), "rank")).toBe("up");
  });

  it("is read of each figure on its own, since a hand in rank order reads by suit however it pleases", () => {
    expect(turnedTo(sortedBy(A_HAND, "rank", "up"), "suit")).toBe("up");
  });
});

describe("the presses a zone offers for putting it in order", () => {
  it("stands both of them at the name of the zone the table says this seat lays out", () => {
    const hand = drawn(sortable(POSITION, HAND), "own");

    expect(presses(hand)).toBe(2);
    expect(hand).toContain('<span class="label">Your hand</span><span class="sorting">');
    expect(hand).toContain('aria-label="Sort by rank, ascending"');
    expect(hand).toContain('aria-label="Sort by suit, ascending"');
  });

  it("letters each press with the end it reads the order from, so a hand already in one order is turned round", () => {
    const hand = drawn(sortable(IN_ORDER, HAND), "own");

    expect(hand).toContain('aria-label="Sort by rank, descending"');
    expect(hand).toContain('aria-label="Sort by suit, ascending"');
    expect(hand).toContain("↓");
    expect(hand).toContain("↑");
  });

  it("offers none where the table keeps the order of the zone itself", () => {
    expect(presses(drawn(POSITION, "own"))).toBe(0);
  });

  it("offers none of a run of one card, which lies in every order at once", () => {
    expect(presses(drawn(sortable(A_SINGLE, HAND), "own"))).toBe(0);
  });

  it("offers none of a heap read by the card on top of it, since an order it lays would name one card", () => {
    expect(presses(drawn(sortable(POSITION, STACK), "shared"))).toBe(0);
  });
});
