import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Plaque as Standing, Readout, Slot } from "../src/api/layout";
import type { PositionView } from "../src/api/views";
import type { Selection } from "../src/play/selection";
import { offersOf, prospect } from "../src/play/selection";
import { Header } from "../src/table/Header";
import { Zones } from "../src/table/Zones";
import { aGive, aLayout, aPlaying, aTake, aView, card, GIVING, HAND, offering, PILE, STACK, TAKING } from "./tables";

const HELD: Slot = { zone: HAND, label: "Your hand", region: "seat", spread: "fan", place: 0, counted: false };
const DEALT_FROM: Slot = { zone: PILE, label: "Pile", region: "table", spread: "stack", place: 0, counted: true };
const LAID_ON: Slot = { zone: STACK, label: "Stack", region: "table", spread: "stack", place: 1, counted: true };

const POINTS: Readout = { field: "points", label: "Points", scope: "seat" };

const SEATS: Standing[] = [
  { seat: 0, name: "Seat 0", counts: [{ zone: "hand:0", label: "Cards" }] },
  { seat: 1, name: "Seat 1", counts: [{ zone: HAND, label: "Cards" }] },
  { seat: 2, name: "Seat 2", counts: [{ zone: "hand:2", label: "Cards" }] },
];

const LAYOUT = aLayout({
  slots: [HELD, DEALT_FROM, LAID_ON],
  readouts: [POINTS],
  phases: { passing: "Passing" },
  plaques: SEATS,
  gestures: [TAKING, GIVING],
});

const WATCHING = aLayout({ observer: null, slots: [DEALT_FROM, LAID_ON], plaques: SEATS });

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

function drawn(view: PositionView, selection: Selection | null, region: "seat" | "table"): string {
  const playing = aPlaying(prospect(offersOf(LAYOUT, view), selection));
  return renderToStaticMarkup(<Zones region={region} layout={LAYOUT} view={view} playing={playing} />);
}

function standing(view: PositionView, selection: Selection | null): string {
  const playing = aPlaying(prospect(offersOf(LAYOUT, view), selection));
  return renderToStaticMarkup(<Header layout={LAYOUT} view={view} playing={playing} />);
}

describe("the cards a player may press", () => {
  it("lights every card a move names, and lights the others not at all", () => {
    const hand = drawn(A_TURN, null, "seat");

    expect([...hand.matchAll(/class="card face [a-z]+ open"/g)]).toHaveLength(2);
    expect([...hand.matchAll(/<button/g)]).toHaveLength(3);
  });

  it("draws a card in hand as pressed, and the card beside it as one still to pick", () => {
    const hand = drawn(A_TURN, { zone: HAND, indices: [0] }, "seat");

    expect(hand).toContain('aria-pressed="true"');
    expect([...hand.matchAll(/aria-pressed="false"/g)]).toHaveLength(2);
    expect(hand).toContain("selected");
  });

  it("presses nothing on a table this seat owes no move to", () => {
    const hand = drawn(POSITION, null, "seat");

    expect(hand).not.toContain("<button");
    expect(hand).not.toContain("open");
  });

  it("presses nothing at a table it is only watching", () => {
    const watched = renderToStaticMarkup(
      <Zones
        region="table"
        layout={WATCHING}
        view={A_TURN}
        playing={aPlaying(prospect(offersOf(WATCHING, A_TURN), null))}
      />,
    );

    expect(watched).not.toContain("<button");
  });
});

describe("the places a selection can be sent onto", () => {
  it("lays a place to send onto over the zone a move commits to, under the words the game gives it", () => {
    const table = drawn(A_TURN, { zone: HAND, indices: [0] }, "table");

    expect(table).toContain("slot stack live");
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
    expect(drawn(A_TURN, null, "table")).not.toContain("landing");
    expect(standing(A_TURN, null)).not.toContain("landing");
  });
});
