import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Layout, Slot } from "../src/api/layout";
import type { PositionView } from "../src/api/views";
import { NOTHING_LANDED } from "../src/play/arrivals";
import type { Selection } from "../src/play/selection";
import { offersOf, prospect } from "../src/play/selection";
import { Header } from "../src/table/Header";
import { drawnAt, linesOf, own, ringOf, shared, SIDES, stations } from "../src/table/placing";
import { Sitting } from "../src/table/Sitting";
import { Station } from "../src/table/Station";
import {
  aBlind,
  aGive,
  aHolding,
  aLayout,
  aPlaying,
  AROUND,
  aTableOf,
  aTake,
  aTray,
  aView,
  blindOf,
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
  SEAT,
  SEATS,
  STACK,
  TAKING,
  TINTED,
  trayOf,
} from "./tables";

/** The whole of a `passing` table: every seat's hand laid out, the pile dealt from and the stack laid on. */
const LAYOUT: Layout = aLayout({
  slots: [HELD, ...AROUND, DEALT_FROM, LAID_ON],
  plaques: PLAQUES,
  gestures: [TAKING, GIVING],
});

/** The same table as a gathering dealt it, every seat playing under a tint of its own. */
const COLOURED: Layout = aLayout({ ...LAYOUT, plaques: TINTED });

/** The same table with nobody at it, which every seat is read across from. */
const WATCHING: Layout = aLayout({
  observer: null,
  slots: SEATS.map(aHolding).concat([DEALT_FROM, LAID_ON]),
  plaques: PLAQUES,
});

/** A table that draws no cards for the other seats, whose holdings their plaques carry the size of. */
const CONCEALED: Layout = aLayout({
  slots: [HELD, DEALT_FROM, LAID_ON],
  plaques: PLAQUES,
  gestures: [TAKING, GIVING],
});

/** What a `showdown` seat holds: a hand, the blind beside it, and the place a commitment lies sealed in. */
function sealing(seat: number): Slot[] {
  return [aHolding(seat), aBlind(seat), aTray(seat)];
}

/** A table of that shape as one seat plays it, which is three zones in the panel and three at every other seat. */
const SEALED_AT: Layout = aLayout({
  slots: [HELD, aBlind(SEAT), aTray(SEAT), ...SEATS.filter((seat) => seat !== SEAT).flatMap(sealing)],
  plaques: PLAQUES,
});

const POSITION: PositionView = aView(
  {
    [HAND]: [card("9", "♦"), card("4", "♦")],
    [handOf(0)]: [null, null, null],
    [handOf(2)]: [null, null],
    [PILE]: [null, null, null, null],
    [STACK]: [card("2", "♣")],
  },
  1,
);

/** The turn `passing` gives a seat: either card exchanged with the pile, or passed to the seat it plays into. */
const A_TURN = offering(POSITION, [aTake([0]), aTake([1]), aGive(2, [0]), aGive(2, [1])]);

function drawn(layout: Layout, view: PositionView, selection: Selection | null): string {
  const playing = aPlaying(prospect(offersOf(layout, view), selection));
  return renderToStaticMarkup(
    <>
      {stations(layout).map((station) => (
        <Station
          key={station.seat}
          station={station}
          layout={layout}
          view={view}
          arrivals={NOTHING_LANDED}
          playing={playing}
        />
      ))}
    </>,
  );
}

function standing(layout: Layout, view: PositionView, selection: Selection | null): string {
  const playing = aPlaying(prospect(offersOf(layout, view), selection));
  return renderToStaticMarkup(<Header layout={layout} view={view} playing={playing} />);
}

/** How many stations one drawing holds, which is one for every seat whose cards lie on the table. */
function stationed(drawing: string): number {
  return [...drawing.matchAll(/class="station/g)].length;
}

describe("the seats round the table", () => {
  it("draws one for every seat beside the one reading the page", () => {
    expect(stationed(drawn(LAYOUT, POSITION, null))).toBe(2);
    expect(stations(LAYOUT).map((station) => station.seat)).toEqual([2, 0]);
  });

  it("orders them the way play runs, so the seat played into sits nearest", () => {
    expect(stations(LAYOUT).map((station) => station.turn)).toEqual([1, 2]);
  });

  it("names each of them as their plaque does", () => {
    const table = drawn(LAYOUT, POSITION, null);

    expect(table).toContain("Seat 0");
    expect(table).toContain("Seat 2");
    expect(table).not.toContain("Seat 1");
  });

  it("draws each of them in the tint that seat plays under, as its plaque across the top is drawn", () => {
    const table = drawn(COLOURED, POSITION, null);

    expect(table).toContain('data-tint="rose"');
    expect(table).toContain('data-tint="amber"');
    expect(table).not.toContain('data-tint="coral"');
  });

  it("draws them in none where no host held a colour for anybody", () => {
    expect(drawn(LAYOUT, POSITION, null)).not.toContain("data-tint");
  });

  it("draws every card a seat holds as a back, under the count of them", () => {
    const table = drawn(LAYOUT, POSITION, null);

    expect([...table.matchAll(/class="card back"/g)]).toHaveLength(5);
    expect(table).toContain(">3</span>");
    expect(table).toContain(">2</span>");
  });

  it("presses none of another seat's cards, since no move of this seat picks in them", () => {
    const table = drawn(LAYOUT, A_TURN, null);

    expect(table).not.toContain("<button");
  });

  it("leaves the panel below to the seat reading the page", () => {
    expect(own(LAYOUT).map((slot) => slot.zone)).toEqual([HAND]);
    expect(shared(LAYOUT).map((slot) => slot.zone)).toEqual([PILE, STACK]);
  });

  it("draws every seat of the table for somebody only watching it", () => {
    expect(stationed(drawn(WATCHING, POSITION, null))).toBe(3);
    expect(own(WATCHING)).toEqual([]);
  });

  it("draws no station for a seat whose cards the table keeps off it", () => {
    expect(stationed(drawn(CONCEALED, POSITION, null))).toBe(0);
    expect(drawnAt(CONCEALED, 0)).toBe(false);
  });
});

describe("the lines a group of zones lies in", () => {
  it("stands the holdings of a seat across the table over the place it seals a card in", () => {
    expect(linesOf("theirs", sealing(0)).map((line) => line.map((slot) => slot.zone))).toEqual([
      [handOf(0), blindOf(0)],
      [trayOf(0)],
    ]);
  });

  it("stands a seat with nothing to seal along the one line", () => {
    expect(linesOf("theirs", [aHolding(0)])).toEqual([[aHolding(0)]]);
  });

  it("lays the panel a player plays from along one line, the place they seal a card in among the rest", () => {
    const panel = own(SEALED_AT);

    expect(panel.map((slot) => slot.zone)).toEqual([HAND, blindOf(SEAT), trayOf(SEAT)]);
    expect(linesOf("own", panel)).toEqual([panel]);
  });

  it("lays the zones the table shares along one line", () => {
    expect(linesOf("shared", shared(LAYOUT))).toEqual([shared(LAYOUT)]);
  });

  it("draws a seat across the table in the lines its zones lie in", () => {
    expect([...drawn(SEALED_AT, POSITION, null).matchAll(/class="line"/g)]).toHaveLength(4);
    expect([...drawn(LAYOUT, POSITION, null).matchAll(/class="line"/g)]).toHaveLength(2);
  });

  it("names the group of a seat's zones apart from the box that seat sits in", () => {
    const table = drawn(LAYOUT, POSITION, null);

    expect(table).toContain('class="zones theirs"');
    expect(table).not.toContain('class="zones station"');
  });
});

describe("a card passed to another player", () => {
  it("lands on the cards of the seat it goes to, and on no other seat's", () => {
    const table = drawn(LAYOUT, A_TURN, { zone: HAND, indices: [0] });

    expect([...table.matchAll(/class="station[^"]*live"/g)]).toHaveLength(1);
    expect(table).toContain(`aria-label="${GIVING.caption}: Seat 2"`);
    expect([...table.matchAll(/class="landing"/g)]).toHaveLength(1);
  });

  it("lands nowhere while the cards are still being picked", () => {
    const table = drawn(LAYOUT, A_TURN, null);

    expect(table).not.toContain("landing");
    expect(table).not.toContain("live");
  });

  it("leaves the plaque of a seat drawn on the table out of it, since the cards are what to point at", () => {
    const plaques = standing(LAYOUT, A_TURN, { zone: HAND, indices: [0] });

    expect(plaques).not.toContain("landing");
  });

  it("lands on the plaque of a seat the table draws no cards for, which is the one place left to point", () => {
    const plaques = standing(CONCEALED, A_TURN, { zone: HAND, indices: [0] });

    expect([...plaques.matchAll(/class="landing"/g)]).toHaveLength(1);
    expect(plaques).toContain(`aria-label="${GIVING.caption}: Seat 2"`);
  });
});

/** What one side of the table holds, read out of the page between that side and the next. */
function sideOf(page: string, side: string): string {
  const from = page.indexOf(`class="sitting ${side}"`);
  const rest = page.slice(from + 1);
  const next = rest.indexOf('class="sitting ');
  return next === -1 ? rest : rest.slice(0, next);
}

describe("the sides of a table", () => {
  it("stands each seat in the run of the side it sits at, in the order play runs round them", () => {
    const table = aTableOf(7, 0);
    const ring = ringOf(table);
    const page = renderToStaticMarkup(
      <>
        {SIDES.map((side) => (
          <Sitting
            key={side}
            side={side}
            seats={ring[side]}
            layout={table}
            view={POSITION}
            arrivals={NOTHING_LANDED}
            playing={aPlaying(prospect([], null))}
          />
        ))}
      </>,
    );

    expect(stationed(page)).toBe(6);
    expect(sideOf(page, "left")).toContain("Seat 2");
    expect(sideOf(page, "left")).not.toContain("Seat 3");
    expect(sideOf(page, "across")).toContain("Seat 4");
    expect(sideOf(page, "right")).toContain("Seat 6");
  });
});

describe("a seat whose turn it is", () => {
  it("is marked where it sits, as it is on its plaque", () => {
    const table = drawn(WATCHING, POSITION, null);

    expect([...table.matchAll(/class="station[^"]*acting/g)]).toHaveLength(1);
  });
});
