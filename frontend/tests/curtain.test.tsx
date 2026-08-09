import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Layout, Readout } from "../src/api/layout";
import type { Report } from "../src/play/interludes";
import { Curtain } from "../src/table/Curtain";
import { aLayout, atRest, BETWEEN_ROUNDS, MATCH_OVER, PLAQUES, TINTED } from "./tables";

const POINTS: Readout = { field: "points", label: "Points", scope: "seat" };
const THIS_ROUND: Readout = { field: "round_points", label: "This round", scope: "seat" };
const ROUND: Readout = { field: "round_number", label: "Round", scope: "table" };

const LAYOUT: Layout = aLayout({ plaques: PLAQUES, readouts: [POINTS, THIS_ROUND, ROUND] });

/** A round closed with the last of it taken by the third seat, and the match the same standing decided. */
const CLOSED: Report = { interlude: "round", state: atRest(BETWEEN_ROUNDS, [3, 5, 8], [0, 0, 1]) };
const DECIDED: Report = { interlude: "match", state: atRest(MATCH_OVER, [3, 5, 8], [0, 0, 1]) };

/** A dismissal that does nothing, since what these tests read is the panel rather than what follows one. */
const IDLE = (): void => undefined;

function drawn(report: Report, layout: Layout = LAYOUT): string {
  return renderToStaticMarkup(<Curtain layout={layout} report={report} dismiss={IDLE} />);
}

describe("a round read out as it closes", () => {
  it("is titled in the interface's own words rather than the game's", () => {
    expect(drawn(CLOSED)).toContain("Round over");
  });

  it("reads every seat of the table under the name its plaque carries", () => {
    const panel = drawn(CLOSED);

    expect(panel).toContain("Seat 0");
    expect(panel).toContain("Seat 1");
    expect(panel).toContain("Seat 2");
  });

  it("reads the standing and the round's own award out of the cursor the closing commit left", () => {
    const panel = drawn(CLOSED);

    expect(panel).toContain("Points");
    expect(panel).toContain("This round");
    expect([...panel.matchAll(/<dd>8<\/dd>/g)]).toHaveLength(1);
    expect([...panel.matchAll(/<dd>1<\/dd>/g)]).toHaveLength(1);
  });

  it("reads each seat under the tint it played in, which is how the standing is read at a glance", () => {
    const colored = aLayout({ plaques: TINTED, readouts: [POINTS] });
    const panel = drawn(CLOSED, colored);

    expect(panel).toContain('class="result" data-tint="rose"');
    expect([...panel.matchAll(/class="result" data-tint/g)]).toHaveLength(TINTED.length);
  });

  it("reads them under none where no host held a color for anybody", () => {
    expect(drawn(CLOSED)).not.toContain("data-tint");
  });

  it("reads the figures the game keeps of the whole table beneath the seats", () => {
    const panel = drawn(CLOSED);

    expect(panel).toContain("Round");
    expect(panel).toContain("figures table");
  });

  it("names no winner, since the match it belongs to is still being played for", () => {
    expect(drawn(CLOSED)).not.toContain("the match");
  });

  it("offers one press onward", () => {
    expect([...drawn(CLOSED).matchAll(/<button/g)]).toHaveLength(1);
  });
});

describe("a match read out as it is decided", () => {
  it("names the seat at the end of the standing the layout is won at", () => {
    expect(drawn(DECIDED)).toContain("Seat 2 takes the match");
  });

  it("names the other end where the game is won there", () => {
    const golf = aLayout({ plaques: PLAQUES, readouts: [POINTS], award: "lowest" });

    expect(drawn(DECIDED, golf)).toContain("Seat 0 takes the match");
  });

  it("names every seat of a standing several of them hold equally", () => {
    const shared: Report = { interlude: "match", state: atRest(MATCH_OVER, [8, 5, 8], [0, 0, 1]) };

    expect(drawn(shared)).toContain("Seat 0 and Seat 2 share the match");
  });
});

describe("the table under a report", () => {
  it("lies behind the whole page, so no card of it is reached while the report stands", () => {
    expect(drawn(CLOSED)).toContain('class="curtain"');
  });
});
