import { describe, expect, it } from "vitest";

import { reasonOf, refusalOf } from "../src/api/refusal";

const REFUSED = 403;
const MISSTATED = 422;
const UNREACHED = 502;

/** What the table states a refusal of its own as, which mirrors `cardserver.schemas.error.ErrorBody`. */
const STATED = { error: "Unadmitted", detail: "The code offered admits nobody here" };

/** What a framework answers a misstated request with, before the table reads it into a sentence of its own. */
const FIELDS = [{ type: "missing", loc: ["body", "name"], msg: "Field required", input: {} }];

/** An answer as it arrives off the wire, whatever the body it carries was written by. */
function answering(status: number, body: unknown, statusText = ""): Response {
  return new Response(JSON.stringify(body), {
    status,
    statusText,
    headers: { "content-type": "application/json" },
  });
}

/** An answer carrying a body no client can read as JSON, which is what a proxy in front of a table sends. */
function unreadable(status: number, statusText: string): Response {
  return new Response("<html><body>Bad Gateway</body></html>", {
    status,
    statusText,
    headers: { "content-type": "text/html" },
  });
}

interface ReadingCase {
  description: string;
  answered: () => Response;
  kind: string;
  reason: string;
}

const READINGS: ReadingCase[] = [
  {
    description: "the shape the table states its own refusals in",
    answered: () => answering(REFUSED, STATED),
    kind: STATED.error,
    reason: STATED.detail,
  },
  {
    description: "a body naming a sentence and no kind, which is what a transport answers for itself",
    answered: () => answering(MISSTATED, { detail: "Not Found" }),
    kind: String(MISSTATED),
    reason: "Not Found",
  },
  {
    description: "a body stating the misstated fields as a list, which reaches a person as the list it is",
    answered: () => answering(MISSTATED, { detail: FIELDS }),
    kind: String(MISSTATED),
    reason: JSON.stringify(FIELDS),
  },
  {
    description: "a body of no shape this client knows",
    answered: () => answering(REFUSED, { trouble: "elsewhere" }),
    kind: String(REFUSED),
    reason: "The server said nothing of what went wrong",
  },
  {
    description: "a body that reads as no JSON at all, answered under a status carrying words",
    answered: () => unreadable(UNREACHED, "Bad Gateway"),
    kind: String(UNREACHED),
    reason: "Bad Gateway",
  },
  {
    description: "a body that reads as no JSON at all, under a status carrying no words either",
    answered: () => unreadable(UNREACHED, ""),
    kind: String(UNREACHED),
    reason: "The server said nothing of what went wrong",
  },
];

describe("a refusal read off an answer", () => {
  it.each(READINGS)("$description", async ({ answered, kind, reason }) => {
    const refusal = await refusalOf(answered());

    expect(refusal.kind).toBe(kind);
    expect(refusal.message).toBe(reason);
  });

  it.each(READINGS)("$description says something in words", async ({ answered }) => {
    const refusal = await refusalOf(answered());

    expect(reasonOf(refusal)).not.toContain("[object Object]");
    expect(reasonOf(refusal).length).toBeGreaterThan(0);
  });
});

interface TroubleCase {
  description: string;
  trouble: unknown;
  reason: string;
}

const TROUBLES: TroubleCase[] = [
  {
    description: "a failure stating itself in a sentence",
    trouble: new TypeError("Failed to fetch"),
    reason: "Failed to fetch",
  },
  { description: "a failure stating a kind and no sentence", trouble: new RangeError(), reason: "RangeError" },
  { description: "a sentence thrown on its own", trouble: "the stream dropped", reason: "the stream dropped" },
  { description: "a shape thrown on its own", trouble: { code: 12 }, reason: '{"code":12}' },
  { description: "nothing thrown at all", trouble: null, reason: "The server said nothing of what went wrong" },
];

describe("the words a failure reaches a person as", () => {
  it.each(TROUBLES)("$description", ({ trouble, reason }) => {
    expect(reasonOf(trouble)).toBe(reason);
  });
});
