import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Layout, Readout, Slot } from "../src/api/layout";
import type { Cursor, PositionView } from "../src/api/views";
import { Header } from "../src/table/Header";
import { StatusLine } from "../src/table/StatusLine";
import { Zones } from "../src/table/Zones";
import { aLayout, aView, card, HAND, PILE, STACK } from "./tables";

/** The table `passing` lays out for the seat in the middle of three, as the game's own module states it. */
const HELD: Slot = { zone: HAND, label: "Your hand", region: "seat", spread: "fan", place: 0, counted: false };
const DEALT_FROM: Slot = { zone: PILE, label: "Pile", region: "table", spread: "stack", place: 0, counted: true };
const LAID_ON: Slot = { zone: STACK, label: "Stack", region: "table", spread: "stack", place: 1, counted: true };

const POINTS: Readout = { field: "points", label: "Points", scope: "seat" };
const ROUND: Readout = { field: "round_number", label: "Round", scope: "table" };

const LAYOUT: Layout = aLayout({
  slots: [HELD, DEALT_FROM, LAID_ON],
  readouts: [POINTS, ROUND],
  phases: { passing: "Passing" },
  plaques: [
    { seat: 0, name: "Seat 0", counts: [{ zone: "hand:0", label: "Cards" }] },
    { seat: 1, name: "Seat 1", counts: [{ zone: HAND, label: "Cards" }] },
    { seat: 2, name: "Seat 2", counts: [{ zone: "hand:2", label: "Cards" }] },
  ],
});

const DEALT: PositionView = aView(
  {
    [HAND]: [card("9", "♦", true), card("8", "♠", true), card("4", "♦", true)],
    "hand:0": [null, null, null],
    "hand:2": [null, null, null],
    [PILE]: [null, null, null, null],
    [STACK]: [card("2", "♣")],
  },
  1,
);

const drawn = (element: Parameters<typeof renderToStaticMarkup>[0]): string => renderToStaticMarkup(element);

describe("the table one seat reads", () => {
  it("draws every card of its own hand, whichever way up the cards lie", () => {
    const page = drawn(<Zones region="seat" layout={LAYOUT} view={DEALT} />);

    expect(page).toContain("Your hand");
    expect([...page.matchAll(/class="card face/g)]).toHaveLength(3);
    expect(page).toContain(">9</span>");
    expect(page).toContain("concealed");
  });

  it("draws a heap it may not read as the back of one card, under the count of them all", () => {
    const page = drawn(<Zones region="table" layout={LAYOUT} view={DEALT} />);

    expect([...page.matchAll(/class="card back"/g)]).toHaveLength(1);
    expect(page).toContain(">4</span>");
  });

  it("draws a heap lying face up by the card laid on it", () => {
    const page = drawn(<Zones region="table" layout={LAYOUT} view={DEALT} />);

    expect(page).toContain(">2</span>");
    expect(page).toContain(">♣</span>");
  });

  it("lays out no zone another seat holds, and counts it on that seat's plaque instead", () => {
    const cards = drawn(<Zones region="seat" layout={LAYOUT} view={DEALT} />);
    const standing = drawn(<Header layout={LAYOUT} view={DEALT} />);

    expect(cards).not.toContain("hand:0");
    expect(standing).toContain("Cards");
  });
});

describe("the standing across the top", () => {
  it("names every seat of the table, and which of them is reading the page", () => {
    const standing = drawn(<Header layout={LAYOUT} view={DEALT} />);

    expect(standing).toContain("Seat 0");
    expect(standing).toContain("Seat 1 (you)");
    expect(standing).toContain("Seat 2");
  });

  it("marks the seat the turn belongs to", () => {
    const standing = drawn(<Header layout={LAYOUT} view={DEALT} />);

    expect([...standing.matchAll(/plaque acting/g)]).toHaveLength(1);
  });

  it("reads a figure the game keeps per seat at the place each seat sits", () => {
    const standing = drawn(<Header layout={LAYOUT} view={{ ...DEALT, state: { ...DEALT.state, points: [3, 5, 8] } }} />);

    expect(standing).toContain(">3</dd>");
    expect(standing).toContain(">5</dd>");
    expect(standing).toContain(">8</dd>");
  });
});

describe("the line saying where play stands", () => {
  it("reads the phase in the words the game calls it by, and the figures it scopes to the table", () => {
    const status = drawn(<StatusLine layout={LAYOUT} view={DEALT} connection="following" trouble={null} />);

    expect(status).toContain("Passing");
    expect(status).toContain("Round");
    expect(status).toContain("seat 1");
    expect(status).toContain("Live");
  });

  it("says so while a stream it lost is being taken up again", () => {
    const status = drawn(
      <StatusLine layout={LAYOUT} view={DEALT} connection="resuming" trouble="the stream fell over" />,
    );

    expect(status).toContain("Reconnecting");
    expect(status).toContain("the stream fell over");
  });

  it("names nobody where a phase has come to rest", () => {
    const settled: Cursor = { ...DEALT.state, to_act: [] };
    const status = drawn(
      <StatusLine layout={LAYOUT} view={{ ...DEALT, state: settled }} connection="following" trouble={null} />,
    );

    expect(status).toContain("nobody");
  });
});
