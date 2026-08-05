import { describe, expect, it } from "vitest";

import type { PositionView, ZoneId } from "../src/api/views";
import { laidFrom, laidIn } from "../src/play/arranging";
import { aView, card, HAND, PILE } from "./tables";

/** A hand of three the seat holding it may lay out, and a stock nobody reads. */
const DEALT: PositionView = aView(
  {
    [HAND]: [card("9", "♦"), card("8", "♠"), card("4", "♦")],
    [PILE]: [null, null],
  },
  4,
);

/** The order a player laid that hand out in, which reads it from the far end. */
const BACKWARDS = [2, 1, 0];

/** The same position with one zone lying in another order, which is what the commit carrying one leaves. */
function reordered(view: PositionView, zone: ZoneId, order: number[]): PositionView {
  const cards = view.zones[zone]?.cards ?? [];
  const held = view.zones[zone];
  if (held === undefined) {
    return view;
  }

  return {
    ...view,
    zones: { ...view.zones, [zone]: { ...held, cards: order.map((index) => cards[index] ?? null) } },
  };
}

describe("the order a player has laid one zone out in", () => {
  it("is the order they laid, while the zone still reads as the cards they laid it over", () => {
    const laid = laidFrom(DEALT.zones, HAND, BACKWARDS);

    expect(laidIn(laid, HAND, DEALT.zones)).toEqual(BACKWARDS);
  });

  it("is nothing once the table holds that order itself, which is the commit carrying it arriving", () => {
    const laid = laidFrom(DEALT.zones, HAND, BACKWARDS);
    const after = reordered(DEALT, HAND, BACKWARDS);

    expect(laidIn(laid, HAND, after.zones)).toBeNull();
  });

  it("is nothing once the zone reads as something else again, which is a table that moved on of its own", () => {
    const laid = laidFrom(DEALT.zones, HAND, BACKWARDS);
    const played = reordered(DEALT, HAND, [0, 2]);

    expect(laidIn(laid, HAND, played.zones)).toBeNull();
  });

  it("is nothing for any zone but the one it was laid in", () => {
    const laid = laidFrom(DEALT.zones, HAND, BACKWARDS);

    expect(laidIn(laid, PILE, DEALT.zones)).toBeNull();
  });

  it("is nothing where the player has laid no order down at all", () => {
    expect(laidIn(null, HAND, DEALT.zones)).toBeNull();
  });

  it("is laid over the cards the zone held, and over none where the page has yet to be served that zone", () => {
    expect(laidFrom(DEALT.zones, HAND, BACKWARDS).stood).toEqual(DEALT.zones[HAND]?.cards);
    expect(laidFrom(DEALT.zones, "nowhere", BACKWARDS).stood).toEqual([]);
  });
});
