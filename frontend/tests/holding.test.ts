import { describe, expect, it } from "vitest";

import type { PositionView, ProjectedCard, ZoneId } from "../src/api/views";
import { cardsAt, sameRun } from "../src/play/cards";
import type { Selection } from "../src/play/selection";
import { heldFrom, stands } from "../src/play/selection";
import { aView, card, HAND, handOf, PILE } from "./tables";

/** The card standing for any other, which a game reads as whatever it needs. */
const joker = (red: boolean): ProjectedCard => ({ card: { red }, face_down: false });

/** A hand of four, a stock nobody reads, and the hand of the seat across the table. */
const DEALT: PositionView = aView(
  {
    [HAND]: [card("9", "♦"), card("8", "♠"), card("4", "♦"), card("K", "♣")],
    [PILE]: [null, null, null],
    [handOf(2)]: [null, null, null, null],
  },
  4,
);

const PICKED: Selection = { zone: HAND, indices: [1, 3] };

/** The same position with one zone lying in another order, which is what a seat sorting its cards leaves. */
function reordered(view: PositionView, zone: ZoneId, order: number[]): PositionView {
  const cards = view.zones[zone]?.cards ?? [];
  return laid(
    view,
    zone,
    order.map((index) => cards[index] ?? null),
  );
}

/** The same position with one zone holding the cards named. */
function laid(view: PositionView, zone: ZoneId, cards: ProjectedCard[]): PositionView {
  const held = view.zones[zone] ?? { id: zone, owner: null, arrangeable: false, cards: [] };
  return { ...view, zones: { ...view.zones, [zone]: { ...held, cards } } };
}

describe("the cards lying at a run of positions", () => {
  it("reads one card per position, in the order the positions were named", () => {
    expect(cardsAt(DEALT.zones[HAND], [3, 0])).toEqual([card("K", "♣"), card("9", "♦")]);
  });

  it("reads a place nobody at this seat reads as the placeholder standing there", () => {
    expect(cardsAt(DEALT.zones[PILE], [1])).toEqual([null]);
  });

  it("reads no card at a position the zone has given up, so the run comes back shorter", () => {
    expect(cardsAt(DEALT.zones[PILE], [1, 3])).toEqual([null]);
  });

  it("reads no card at all out of a zone this seat has been told nothing of", () => {
    expect(cardsAt(DEALT.zones.nowhere, [0])).toEqual([]);
  });
});

describe("two runs read against each other", () => {
  it("are the one run where the same cards lie in the same order", () => {
    expect(sameRun([card("9", "♦"), null], [card("9", "♦"), null])).toBe(true);
  });

  it("are two runs where a card of one reads as another card", () => {
    expect(sameRun([card("9", "♦")], [card("9", "♠")])).toBe(false);
    expect(sameRun([card("9", "♦")], [card("8", "♦")])).toBe(false);
  });

  it("are two runs where the same cards lie in another order", () => {
    expect(sameRun([card("9", "♦"), card("8", "♠")], [card("8", "♠"), card("9", "♦")])).toBe(false);
  });

  it("are two runs where one holds a card the other holds no card at", () => {
    expect(sameRun([card("9", "♦")], [])).toBe(false);
    expect(sameRun([card("9", "♦")], [null])).toBe(false);
  });

  it("tell a card lying face down from the same card turned over", () => {
    expect(sameRun([card("9", "♦", true)], [card("9", "♦")])).toBe(false);
  });

  it("tell the two jokers apart, and read each of them as itself", () => {
    expect(sameRun([joker(true)], [joker(true)])).toBe(true);
    expect(sameRun([joker(true)], [joker(false)])).toBe(false);
    expect(sameRun([joker(true)], [card("9", "♦")])).toBe(false);
    expect(sameRun([card("9", "♦")], [joker(true)])).toBe(false);
  });
});

describe("a selection made in a zone as it stood", () => {
  it("holds the cards that lay at the positions it names", () => {
    expect(heldFrom(DEALT.zones, PICKED).picked).toEqual([card("8", "♠"), card("K", "♣")]);
  });

  it("stands where the table has moved on and left those cards lying where they lay", () => {
    const sorted = reordered(DEALT, handOf(2), [3, 2, 1, 0]);

    expect(stands(heldFrom(DEALT.zones, PICKED), sorted.zones)).toBe(true);
  });

  it("stands where the position was read afresh and served the same cards over again", () => {
    const read = aView(
      { ...Object.fromEntries(Object.entries(DEALT.zones).map(([zone, held]) => [zone, held.cards])) },
      9,
    );

    expect(stands(heldFrom(DEALT.zones, PICKED), read.zones)).toBe(true);
  });

  it("comes down where the cards it names have been laid out in another order", () => {
    const sorted = reordered(DEALT, HAND, [3, 2, 1, 0]);

    expect(stands(heldFrom(DEALT.zones, PICKED), sorted.zones)).toBe(false);
  });

  it("comes down where a card was dealt in ahead of the ones it names", () => {
    const cards = DEALT.zones[HAND]?.cards ?? [];
    const dealt = laid(DEALT, HAND, [card("2", "♥"), ...cards]);

    expect(stands(heldFrom(DEALT.zones, PICKED), dealt.zones)).toBe(false);
  });

  it("comes down where the cards it names have left the zone altogether", () => {
    const played = laid(DEALT, HAND, [card("9", "♦"), card("4", "♦")]);

    expect(stands(heldFrom(DEALT.zones, PICKED), played.zones)).toBe(false);
  });

  it("stands on a run of cards nobody reads however it is permuted, since a position of a stock names the place", () => {
    const held = heldFrom(DEALT.zones, { zone: PILE, indices: [2] });

    expect(stands(held, reordered(DEALT, PILE, [2, 1, 0]).zones)).toBe(true);
    expect(stands(held, laid(DEALT, PILE, [null, null]).zones)).toBe(false);
  });
});
