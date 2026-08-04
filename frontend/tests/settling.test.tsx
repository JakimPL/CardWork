import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Layout } from "../src/api/layout";
import type { PositionView } from "../src/api/views";
import type { Arrivals } from "../src/play/arrivals";
import { NOTHING_LANDED } from "../src/play/arrivals";
import { prospect } from "../src/play/selection";
import type { Placement } from "../src/table/placing";
import { own, shared } from "../src/table/placing";
import { Zones } from "../src/table/Zones";
import { aLayout, aPlaying, aView, card, DEALT_FROM, HAND, HELD, LAID_ON, landing, PILE, STACK } from "./tables";

const LAYOUT: Layout = aLayout({ slots: [HELD, DEALT_FROM, LAID_ON] });

/** A table mid-round: three cards in hand, a pile to draw from, and three already laid on the stack. */
const PLAYED: PositionView = aView(
  {
    [HAND]: [card("9", "♦"), card("8", "♠"), card("4", "♦")],
    [PILE]: [null, null, null, null],
    [STACK]: [card("2", "♣"), card("5", "♥"), card("K", "♠")],
  },
  4,
);

/** A table nothing is being played on, since what these tests read is the drawing of it. */
const RESTING = aPlaying(prospect([], null));

function drawn(view: PositionView, arrivals: Arrivals, place: Placement): string {
  const slots = place === "own" ? own(LAYOUT) : shared(LAYOUT);
  return renderToStaticMarkup(<Zones place={place} slots={slots} view={view} arrivals={arrivals} playing={RESTING} />);
}

describe("a heap at rest", () => {
  it("reads by the card lying on top of it, under the count of them all", () => {
    const table = drawn(PLAYED, NOTHING_LANDED, "shared");

    expect([...table.matchAll(/class="card face/g)]).toHaveLength(1);
    expect(table).toContain(">K</span>");
    expect(table).toContain(">3</span>");
  });

  it("marks the depth of the cards lying under that one", () => {
    const table = drawn(PLAYED, NOTHING_LANDED, "shared");

    expect([...table.matchAll(/class="cards deep"/g)]).toHaveLength(2);
  });

  it("marks no depth under a holding that shows every card it has", () => {
    const hand = drawn(PLAYED, NOTHING_LANDED, "own");

    expect(hand).not.toContain("deep");
  });
});

describe("a card just laid on a heap", () => {
  it("shows beside the card it came to rest on, and is marked as having arrived", () => {
    const table = drawn(PLAYED, landing(STACK, 1), "shared");

    expect([...table.matchAll(/class="card face [a-z]+ arriving"/g)]).toHaveLength(1);
    expect(table).toContain(">5</span>");
    expect(table).toContain(">K</span>");
  });

  it("leaves the heaps it was not laid on reading by their own top card", () => {
    const table = drawn(PLAYED, landing(STACK, 1), "shared");

    expect([...table.matchAll(/class="card back"/g)]).toHaveLength(1);
  });

  it("closes back to the one card once the arrival has been read", () => {
    const table = drawn(PLAYED, NOTHING_LANDED, "shared");

    expect(table).not.toContain("arriving");
    expect([...table.matchAll(/class="card face/g)]).toHaveLength(1);
  });

  it("shows a settlement of several cards whole, on the card they landed on", () => {
    const table = drawn(PLAYED, landing(STACK, 2), "shared");

    expect([...table.matchAll(/class="card face/g)]).toHaveLength(3);
    expect([...table.matchAll(/arriving/g)]).toHaveLength(2);
  });
});

describe("a holding of any size", () => {
  it("tells the style sheet how far it overlaps itself, which follows the cards it fans out", () => {
    const hand = drawn(PLAYED, NOTHING_LANDED, "own");

    expect(hand).toContain("--overlap:0.42");
  });

  it("marks the card just dealt to it as having arrived, beside the cards already held", () => {
    const hand = drawn(PLAYED, landing(HAND, 1), "own");

    expect([...hand.matchAll(/class="card face/g)]).toHaveLength(3);
    expect([...hand.matchAll(/arriving/g)]).toHaveLength(1);
  });
});
