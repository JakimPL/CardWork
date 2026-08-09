import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SEAT_HEADER } from "../src/api/seat";
import type { Closed, Streamed } from "../src/api/streaming";
import { follow } from "../src/api/streaming";

const ADDRESS = "/tables/green-baize/gathering/events?since=1";
const TOKEN = "qWLW5p-0BYc";
const STANDING = "gathering";
const CLOSING = "closed";
const RESUME_HEADER = "last-event-id";
const EVENT_STREAM = "text/event-stream";

const REFUSED = 403;
const SERVED = 200;

/** Long enough for a following that meant to ask again to have asked, which is what says one stopped for good. */
const ENOUGH_TO_ASK_AGAIN = 400;

/** Long enough for a following to have got where a test watches for it, drops and their waiting included. */
const PATIENCE = 5000;

/** As much of a room as these read, which is enough to tell one frame from the next. */
interface Standing {
  revision: number;
}

/** One request a following sent, as a test reads it back off the wire. */
interface Asked {
  address: string;
  token: string | null;
  resumed: string | null;
}

/** An answer the table gives one request: a stream of its own, a refusal, or nothing at all. */
type Answer = () => Promise<Response>;

/** What one following was told, which is the whole of what a page reads a stream by. */
interface Heard {
  openings: number;
  frames: Standing[];
  closings: Closed[];
  drops: string[];
  refusals: string[];
}

const asked: Asked[] = [];

/** One frame as it goes over the wire, keyed by the id a client hands back to pick the stream up at. */
function frame(identifier: number, event: string, body: unknown): string {
  return `id: ${identifier}\nevent: ${event}\ndata: ${JSON.stringify(body)}\n\n`;
}

const carrying =
  (...frames: string[]): Answer =>
  () =>
    Promise.resolve(new Response(frames.join(""), { status: SERVED, headers: { "content-type": EVENT_STREAM } }));

/** A stream that carried nothing before its patience ran out, which is a table with nothing to say just now. */
const quiet: Answer = carrying();

const nothing: Answer = () => Promise.reject(new TypeError("Failed to fetch"));

const refusing =
  (status: number, body: unknown): Answer =>
  () =>
    Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } }));

/** Where a request was sent, however the caller named the place. */
function addressOf(target: RequestInfo | URL): string {
  if (typeof target === "string") {
    return target;
  }

  return target instanceof URL ? target.href : target.url;
}

/** A table answering each request in turn, and standing on its last answer thereafter. */
function serving(answers: Answer[]): void {
  let requests = 0;
  vi.stubGlobal("fetch", (target: RequestInfo | URL, request?: RequestInit) => {
    const options = request ?? {};
    const headers = new Headers(options.headers);
    asked.push({
      address: addressOf(target),
      token: headers.get(SEAT_HEADER),
      resumed: headers.get(RESUME_HEADER),
    });
    const answer = answers[Math.min(requests, answers.length - 1)] ?? nothing;
    requests += 1;
    return answer();
  });
}

/** A page listening to a following, which writes down each thing it is told. */
function listening(): { heard: Heard; streamed: Streamed<Standing> } {
  const heard: Heard = { openings: 0, frames: [], closings: [], drops: [], refusals: [] };
  return {
    heard,
    streamed: {
      onOpen: () => {
        heard.openings += 1;
      },
      onFrame: (view) => heard.frames.push(view),
      onClosed: (closing) => heard.closings.push(closing),
      onDropped: (reason) => heard.drops.push(reason),
      onRefused: (reason) => heard.refusals.push(reason),
    },
  };
}

/** Following the table under test as the seat that holds a token at it. */
function followed(streamed: Streamed<Standing>): () => void {
  return follow<Standing>(ADDRESS, STANDING, { [SEAT_HEADER]: TOKEN }, streamed);
}

function pausing(moment: number): Promise<void> {
  return new Promise((wake) => {
    setTimeout(wake, moment);
  });
}

beforeEach(() => {
  asked.length = 0;
  vi.stubGlobal("window", globalThis);
  vi.stubGlobal("document", {
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("a page following one stream of the table's", () => {
  it("picks the stream up again where it ended, stating the frame it last read", async () => {
    serving([carrying(frame(4, STANDING, { revision: 4 })), quiet]);
    const { heard, streamed } = listening();

    const stop = followed(streamed);
    await vi.waitFor(() => {
      expect(asked).toHaveLength(2);
    }, PATIENCE);
    stop();

    expect(heard.frames).toEqual([{ revision: 4 }]);
    expect(asked[0]?.resumed).toBeNull();
    expect(asked[1]?.resumed).toBe("4");
    expect(asked[1]?.token).toBe(TOKEN);
  });

  it("asks again where a stream carried nothing at all, since a room says nothing while it stands still", async () => {
    serving([quiet]);
    const { heard, streamed } = listening();

    const stop = followed(streamed);
    await vi.waitFor(() => {
      expect(asked.length).toBeGreaterThan(1);
    }, PATIENCE);
    stop();

    expect(heard.drops).toEqual([]);
    expect(asked.every((request) => request.address === ADDRESS)).toBe(true);
  });

  it("says it is following once across the run of requests, which is one following however many it takes", async () => {
    serving([carrying(frame(1, STANDING, { revision: 1 })), carrying(frame(2, STANDING, { revision: 2 })), quiet]);
    const { heard, streamed } = listening();

    const stop = followed(streamed);
    await vi.waitFor(() => {
      expect(asked).toHaveLength(3);
    }, PATIENCE);
    stop();

    expect(heard.openings).toBe(1);
    expect(heard.frames.map((view) => view.revision)).toEqual([1, 2]);
  });

  it("reports a stream that dropped, and says it is following afresh once it is back", async () => {
    serving([carrying(frame(1, STANDING, { revision: 1 })), nothing, carrying(frame(2, STANDING, { revision: 2 }))]);
    const { heard, streamed } = listening();

    const stop = followed(streamed);
    await vi.waitFor(() => {
      expect(heard.frames).toHaveLength(2);
    }, PATIENCE);
    stop();

    expect(heard.drops).toEqual(["Failed to fetch"]);
    expect(heard.openings).toBe(2);
  });

  it("stops for good on the frame saying the table was broken up", async () => {
    serving([
      carrying(frame(3, STANDING, { revision: 3 }), frame(3, CLOSING, { reason: "the host called it a night" })),
    ]);
    const { heard, streamed } = listening();

    const stop = followed(streamed);
    await vi.waitFor(() => {
      expect(heard.closings).toHaveLength(1);
    }, PATIENCE);
    await pausing(ENOUGH_TO_ASK_AGAIN);
    stop();

    expect(heard.closings).toEqual([{ reason: "the host called it a night" }]);
    expect(asked).toHaveLength(1);
    expect(heard.refusals).toEqual([]);
  });

  it("stops for good where the table refuses the stream outright, since asking again would be refused too", async () => {
    serving([refusing(REFUSED, { error: "Unauthorized", detail: "no seat at this table answers to that token" })]);
    const { heard, streamed } = listening();

    const stop = followed(streamed);
    await vi.waitFor(() => {
      expect(heard.refusals).toHaveLength(1);
    }, PATIENCE);
    await pausing(ENOUGH_TO_ASK_AGAIN);
    stop();

    expect(heard.refusals).toEqual(["no seat at this table answers to that token"]);
    expect(asked).toHaveLength(1);
    expect(heard.openings).toBe(0);
  });

  it("asks nothing further once it has been stopped", async () => {
    serving([quiet]);
    const { streamed } = listening();

    const stop = followed(streamed);
    await vi.waitFor(() => {
      expect(asked).toHaveLength(1);
    }, PATIENCE);
    stop();
    await pausing(ENOUGH_TO_ASK_AGAIN);

    expect(asked).toHaveLength(1);
  });
});
