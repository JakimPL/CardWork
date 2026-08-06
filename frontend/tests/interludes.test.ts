import { describe, expect, it } from "vitest";

import type { EventView } from "../src/api/views";
import type { Interluding, Reading } from "../src/play/interludes";
import { arriving, dismissed, interludeIn, leading, PLAYING_ON } from "../src/play/interludes";
import { aCommit, aLayout, atRest, BETWEEN_ROUNDS, INTERLUDES, MATCH_OVER, PLAQUES, SEATED } from "./tables";

/** The three commits a boundary is read through: the round closed, the next dealt, and the match decided. */
const CLOSED = aCommit(7, [], atRest(BETWEEN_ROUNDS, [3, 5, 8], [0, 0, 1]));
const OPENED = aCommit(8, [], SEATED);
const DECIDED = aCommit(9, [], atRest(MATCH_OVER, [3, 5, 8], [0, 0, 1]));

const LAYOUT = aLayout({ plaques: PLAQUES });

/** Every commit one reading applied, in the order it applied them. */
function seqs(read: Reading): number[] {
  return read.applied.map((event) => event.seq);
}

/** A client that has read the stream to the end of it, one commit at a time. */
function following(events: EventView[]): Reading {
  let read: Reading = { interluding: PLAYING_ON, applied: [] };
  for (const event of events) {
    const next = arriving(read.interluding, { event, interlude: interludeIn(INTERLUDES, event.state) });
    read = { interluding: next.interluding, applied: [...read.applied, ...next.applied] };
  }

  return read;
}

describe("the pause a phase stands at", () => {
  it("is the one the layout keyed against that phase", () => {
    expect(interludeIn(INTERLUDES, atRest(BETWEEN_ROUNDS, [], []))).toBe("round");
    expect(interludeIn(INTERLUDES, atRest(MATCH_OVER, [], []))).toBe("match");
  });

  it("is nothing at a phase the layout keys nowhere, since play carries on through it", () => {
    expect(interludeIn(INTERLUDES, SEATED)).toBeNull();
  });
});

describe("a commit off the stream", () => {
  it("lands on the table where play carries on through it", () => {
    const read = arriving(PLAYING_ON, { event: OPENED, interlude: null });

    expect(seqs(read)).toEqual([OPENED.seq]);
    expect(read.interluding).toEqual(PLAYING_ON);
  });

  it("raises a report carrying the cursor it left, where it pauses play", () => {
    const read = arriving(PLAYING_ON, { event: CLOSED, interlude: "round" });

    expect(read.interluding.report).toEqual({ interlude: "round", state: CLOSED.state });
    expect(seqs(read)).toEqual([CLOSED.seq]);
  });
});

describe("the commits behind a report", () => {
  it("wait rather than land, so the round just closed stays on the table", () => {
    const read = following([CLOSED, OPENED]);

    expect(seqs(read)).toEqual([CLOSED.seq]);
    expect(read.interluding.waiting.map((arrival) => arrival.event.seq)).toEqual([OPENED.seq]);
  });

  it("land in the order they arrived once the report is dismissed", () => {
    const held = following([CLOSED, OPENED]);

    const released = dismissed(held.interluding);

    expect(seqs(released)).toEqual([OPENED.seq]);
    expect(released.interluding).toEqual(PLAYING_ON);
  });

  it("stop again at a boundary among them, so a match over is read on its own", () => {
    const held = following([CLOSED, DECIDED, OPENED]);

    const released = dismissed(held.interluding);

    expect(seqs(released)).toEqual([DECIDED.seq]);
    expect(released.interluding.report).toEqual({ interlude: "match", state: DECIDED.state });
    expect(released.interluding.waiting.map((arrival) => arrival.event.seq)).toEqual([OPENED.seq]);
  });

  it("all land where nothing behind the report pauses play", () => {
    const held: Interluding = following([CLOSED, OPENED, OPENED]).interluding;

    expect(seqs(dismissed(held))).toEqual([OPENED.seq, OPENED.seq]);
  });
});

describe("the seats a match belongs to", () => {
  it("are the ones holding the most points where the game is won at that end", () => {
    expect(leading(LAYOUT, atRest(MATCH_OVER, [3, 5, 8], []))).toEqual([2]);
  });

  it("are the ones holding the fewest where the game is won at the other", () => {
    const golf = aLayout({ plaques: PLAQUES, award: "lowest" });

    expect(leading(golf, atRest(MATCH_OVER, [3, 5, 8], []))).toEqual([0]);
  });

  it("are every seat standing equally well, which is what a shared match reads as", () => {
    expect(leading(LAYOUT, atRest(MATCH_OVER, [8, 5, 8], []))).toEqual([0, 2]);
  });

  it("are nobody where the standing holds nothing at all", () => {
    expect(leading(LAYOUT, { phase: MATCH_OVER, to_act: [], points: null })).toEqual([]);
  });
});
