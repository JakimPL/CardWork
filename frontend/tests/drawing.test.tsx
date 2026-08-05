import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Layout, Readout } from "../src/api/layout";
import type { Cursor, PositionView } from "../src/api/views";
import { NOTHING_LANDED } from "../src/play/arrivals";
import type { Selection } from "../src/play/selection";
import { offersOf, prospect } from "../src/play/selection";
import type { Playing } from "../src/play/usePlay";
import { Header } from "../src/table/Header";
import { own, shared } from "../src/table/placing";
import { StatusLine } from "../src/table/StatusLine";
import { Zones } from "../src/table/Zones";
import {
  aLayout,
  aPass,
  aPlaying,
  AROUND,
  aTake,
  aView,
  card,
  DEALT_FROM,
  HAND,
  HELD,
  LAID_ON,
  offering,
  PASSING,
  PILE,
  PLAQUES,
  STACK,
  TAKING,
} from "./tables";

const POINTS: Readout = { field: "points", label: "Points", scope: "seat" };
const ROUND: Readout = { field: "round_number", label: "Round", scope: "table" };

/** The table `passing` lays out for the seat in the middle of three, as the game's own module states it. */
const LAYOUT: Layout = aLayout({
  slots: [HELD, DEALT_FROM, LAID_ON],
  readouts: [POINTS, ROUND],
  phases: { passing: "Passing" },
  plaques: PLAQUES,
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

/** The same table on a turn a word could give up as well as a card play out. */
const SPEAKING: Layout = aLayout({
  slots: [HELD, DEALT_FROM, LAID_ON],
  gestures: [TAKING, PASSING],
  plaques: PLAQUES,
});

/** A table nothing is being played on, since what these tests read is the drawing of it. */
const RESTING = aPlaying(prospect([], null));

const drawn = (element: Parameters<typeof renderToStaticMarkup>[0]): string => renderToStaticMarkup(element);

/** One group of the page's zones, drawn as the layout places them. */
const held = (): string =>
  drawn(<Zones place="own" slots={own(LAYOUT)} view={DEALT} arrivals={NOTHING_LANDED} playing={RESTING} />);

const middle = (): string =>
  drawn(<Zones place="shared" slots={shared(LAYOUT)} view={DEALT} arrivals={NOTHING_LANDED} playing={RESTING} />);

/** That turn as it stands for one selection of the cards in it, which is what the two ways of sending it read off. */
const A_TURN: PositionView = offering(DEALT, [aTake([0]), aPass()]);

const speaking = (selection: Selection | null): Playing => aPlaying(prospect(offersOf(SPEAKING, A_TURN), selection));

const panel = (selection: Selection | null): string =>
  drawn(
    <Zones place="own" slots={own(SPEAKING)} view={A_TURN} arrivals={NOTHING_LANDED} playing={speaking(selection)} />,
  );

describe("the table one seat reads", () => {
  it("draws every card of its own hand, whichever way up the cards lie", () => {
    const page = held();

    expect(page).toContain("Your hand");
    expect([...page.matchAll(/class="card face/g)]).toHaveLength(3);
    expect(page).toContain(">9</span>");
    expect(page).toContain("concealed");
  });

  it("draws a heap it may not read as the back of one card, under the count of them all", () => {
    const page = middle();

    expect([...page.matchAll(/class="card back"/g)]).toHaveLength(1);
    expect(page).toContain(">4</span>");
  });

  it("draws a heap lying face up by the card laid on it", () => {
    const page = middle();

    expect(page).toContain(">2</span>");
    expect(page).toContain(">♣</span>");
  });

  it("says how many cards wide each group of zones lies, which is the room its cards are drawn to", () => {
    expect(held()).toContain("--widths:2.16");
    expect(middle()).toContain("--widths:2");
  });

  it("holds in the panel it plays from the zones of its own seat and no other", () => {
    const table = aLayout({ slots: [HELD, ...AROUND, DEALT_FROM, LAID_ON], plaques: PLAQUES });
    const cards = drawn(
      <Zones place="own" slots={own(table)} view={DEALT} arrivals={NOTHING_LANDED} playing={RESTING} />,
    );

    expect(cards).toContain("Your hand");
    expect([...cards.matchAll(/class="slot [a-z]/g)]).toHaveLength(1);
  });
});

describe("the place a turn is said in", () => {
  it("draws the words of a move landing on no place, at the end of the panel and the size of a card", () => {
    const drawing = panel(null);

    expect(drawing).toContain("Instead of playing");
    expect(drawing).toContain('class="word"');
    expect(drawing).toContain(PASSING.caption);
    expect(drawing).toContain('aria-keyshortcuts="Space"');
    expect(drawing).not.toContain("disabled");
  });

  it("counts it in the width the cards are drawn to, which is the room of one card", () => {
    expect(panel(null)).toContain("--widths:3.16");
    expect(held()).toContain("--widths:2.16");
  });

  it("leaves it quiet where it stands once a card is picked up, which arms it no longer", () => {
    const drawing = panel({ zone: HAND, indices: [0] });

    expect(drawing).toContain('class="word"');
    expect(drawing).toContain("disabled");
    expect(drawing).toContain("--widths:3.16");
    expect(drawing).not.toContain("aria-keyshortcuts");
  });

  it("draws nothing at all where every move the table offers lands on a place", () => {
    expect(held()).not.toContain("Instead of playing");
  });

  it("stands in the panel a player plays from and nowhere else on the table", () => {
    const table = drawn(
      <Zones
        place="shared"
        slots={shared(SPEAKING)}
        view={A_TURN}
        arrivals={NOTHING_LANDED}
        playing={speaking(null)}
      />,
    );

    expect(table).not.toContain("Instead of playing");
    expect(table).toContain("--widths:2");
  });
});

describe("the standing across the top", () => {
  it("names every seat of the table, and which of them is reading the page", () => {
    const standing = drawn(<Header layout={LAYOUT} view={DEALT} playing={RESTING} />);

    expect(standing).toContain("Seat 0");
    expect(standing).toContain("Seat 1 (you)");
    expect(standing).toContain("Seat 2");
  });

  it("marks the seat the turn belongs to", () => {
    const standing = drawn(<Header layout={LAYOUT} view={DEALT} playing={RESTING} />);

    expect([...standing.matchAll(/plaque acting/g)]).toHaveLength(1);
  });

  it("reads a figure the game keeps per seat at the place each seat sits", () => {
    const standing = drawn(
      <Header layout={LAYOUT} view={{ ...DEALT, state: { ...DEALT.state, points: [3, 5, 8] } }} playing={RESTING} />,
    );

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
