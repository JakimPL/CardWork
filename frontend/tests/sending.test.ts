import { afterEach, beforeEach, describe, expect, it } from "vitest";

import type { ArrangementRequest, MoveRequest } from "../src/api/moves";
import { movedOn, Refused } from "../src/api/refusal";
import { type Seat, SEAT_HEADER } from "../src/api/seat";
import { commandFor, deliver, lay, named, orderFor } from "../src/play/sending";
import { aTake } from "./tables";

const PLAYING: Seat = { table: "green-baize", token: "qWLW5p-0BYc" };
const MOVES = "/tables/green-baize/moves";
const ARRANGEMENTS = "/tables/green-baize/arrangements";

const ACCEPTED = 200;
const MOVED_ON = 409;
const AGAINST_THE_RULES = 422;

/** One request the page sent, as a test reads it back off the wire. */
interface Sent {
  address: string;
  token: string | null;
  command: MoveRequest | ArrangementRequest;
}

/** An answer a table gives one attempt: a response of its own, or nothing at all. */
type Answer = () => Promise<Response>;

const answering =
  (status: number, body: unknown): Answer =>
  () =>
    Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } }));

const nothing = (): Promise<Response> => Promise.reject(new TypeError("Failed to fetch"));

/** Where a request was sent, however the caller named the place. */
function addressOf(target: RequestInfo | URL): string {
  if (typeof target === "string") {
    return target;
  }

  return target instanceof URL ? target.href : target.url;
}

const sent: Sent[] = [];
const own = globalThis.fetch;

/** A table answering each attempt in turn, and standing on its last answer thereafter. */
function serving(answers: Answer[]): void {
  let attempts = 0;
  globalThis.fetch = (address, request) => {
    const options = request ?? {};
    sent.push({
      address: addressOf(address),
      token: new Headers(options.headers).get(SEAT_HEADER),
      command: JSON.parse(typeof options.body === "string" ? options.body : "") as MoveRequest | ArrangementRequest,
    });
    const answer = answers[Math.min(attempts, answers.length - 1)] ?? nothing;
    attempts += 1;
    return answer();
  };
}

beforeEach(() => {
  sent.length = 0;
});

afterEach(() => {
  globalThis.fetch = own;
});

describe("a move sent up to a table", () => {
  it("carries the position it was armed against, under the seat that armed it", async () => {
    serving([answering(ACCEPTED, { seq: 3 })]);

    const accepted = await deliver(PLAYING, commandFor(aTake([0]), 2, "the-only-try"));

    expect(accepted.seq).toBe(3);
    expect(sent).toHaveLength(1);
    expect(sent[0]?.address).toBe(MOVES);
    expect(sent[0]?.token).toBe(PLAYING.token);
    expect(sent[0]?.command).toEqual({ move: aTake([0]), base_seq: 2, idempotency_key: "the-only-try" });
  });

  it("goes up a second time under the same name where the first attempt reached no answer", async () => {
    serving([nothing, answering(ACCEPTED, { seq: 4 })]);

    const accepted = await deliver(PLAYING, commandFor(aTake([1]), 3, "one-name-throughout"));

    expect(accepted.seq).toBe(4);
    expect(sent).toHaveLength(2);
    expect(sent.map((attempt) => attempt.command.idempotency_key)).toEqual([
      "one-name-throughout",
      "one-name-throughout",
    ]);
  });

  it("stands on a refusal, since a table that refused a command has answered it", async () => {
    serving([answering(AGAINST_THE_RULES, { error: "IllegalMove", detail: "Seat 1 names one card at a time" })]);

    await expect(deliver(PLAYING, commandFor(aTake([0]), 2, "against-the-rules"))).rejects.toThrow(
      "Seat 1 names one card at a time",
    );
    expect(sent).toHaveLength(1);
  });

  it("says of a refused position that the table has moved on, so a client reads it afresh", async () => {
    serving([
      answering(MOVED_ON, { error: "StalePosition", detail: "built on sequence 1 while the table stands at 2" }),
    ]);

    const refusal: unknown = await deliver(PLAYING, commandFor(aTake([0]), 1, "one-too-late")).catch(
      (trouble: unknown) => trouble,
    );

    expect(refusal).toBeInstanceOf(Refused);
    expect(refusal instanceof Refused && movedOn(refusal)).toBe(true);
    expect(refusal instanceof Refused && refusal.kind).toBe("StalePosition");
  });
});

describe("the order a player laid its own cards out in", () => {
  it("carries the zone and the run, and names the seat nowhere at all", async () => {
    serving([answering(ACCEPTED, { seq: 5 })]);

    const accepted = await lay(PLAYING, orderFor("hand:1", [2, 0, 1], 4, "sorted"));

    expect(accepted.seq).toBe(5);
    expect(sent).toHaveLength(1);
    expect(sent[0]?.address).toBe(ARRANGEMENTS);
    expect(sent[0]?.token).toBe(PLAYING.token);
    expect(sent[0]?.command).toEqual({
      zone: "hand:1",
      order: [2, 0, 1],
      base_seq: 4,
      idempotency_key: "sorted",
    });
  });

  it("goes up a second time under the same name where the first attempt reached no answer", async () => {
    serving([nothing, answering(ACCEPTED, { seq: 6 })]);

    const accepted = await lay(PLAYING, orderFor("hand:1", [1, 0], 5, "one-name-throughout"));

    expect(accepted.seq).toBe(6);
    expect(sent.map((attempt) => attempt.command.idempotency_key)).toEqual([
      "one-name-throughout",
      "one-name-throughout",
    ]);
  });

  it("stands on a refusal, since a table that refused an order has answered it", async () => {
    serving([
      answering(AGAINST_THE_RULES, {
        error: "ArrangementRefused",
        detail: "Seat 1 holds no zone 'stock' of this table to arrange",
      }),
    ]);

    await expect(lay(PLAYING, orderFor("stock", [1, 0], 4, "reaching"))).rejects.toThrow(
      "Seat 1 holds no zone 'stock' of this table to arrange",
    );
    expect(sent).toHaveLength(1);
  });

  it("says of a refused position that the table has moved on, so a client reads it afresh", async () => {
    serving([
      answering(MOVED_ON, { error: "StalePosition", detail: "built on sequence 3 while the table stands at 4" }),
    ]);

    const refusal: unknown = await lay(PLAYING, orderFor("hand:1", [1, 0], 3, "one-too-late")).catch(
      (trouble: unknown) => trouble,
    );

    expect(refusal instanceof Refused && movedOn(refusal)).toBe(true);
  });
});

describe("the name one attempt carries", () => {
  it("names two attempts apart, so a table dedupes the one that was sent twice", () => {
    expect(named()).not.toBe(named());
  });
});
