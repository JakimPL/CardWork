import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { copied } from "../src/play/copying";

/** The line under test, which is an invitation as the room hands one out. */
const LINE = "http://127.0.0.1:8421/#table=green-baize&code=KQAJ72";

/** What the clipboard was handed, which is how a test reads that the line reached it. */
const held: string[] = [];

/** A page standing where the clipboard answers the way one of these says it does. */
function standing(writeText: (line: string) => Promise<void>): void {
  vi.stubGlobal("navigator", { clipboard: { writeText } });
}

/** A clipboard that takes what it is handed. */
function taking(line: string): Promise<void> {
  held.push(line);
  return Promise.resolve();
}

/** A clipboard that turns the write down, as a browser does where it holds the page unfit to ask. */
function refusing(): Promise<void> {
  return Promise.reject(new Error("Document is not focused"));
}

/** A clipboard that answers neither way, which is what a page the window is not showing waits on. */
function silent(): Promise<void> {
  return new Promise(() => undefined);
}

beforeEach(() => {
  held.length = 0;
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("handing one line to the clipboard", () => {
  it("says the line was taken, since a press has a word to read once it is", async () => {
    standing(taking);

    await expect(copied(LINE)).resolves.toBe(true);
    expect(held).toEqual([LINE]);
  });

  it("says it was left where the page stands somewhere the clipboard is closed to it, as a table on a home network does", async () => {
    vi.stubGlobal("navigator", {});

    await expect(copied(LINE)).resolves.toBe(false);
  });

  it("says it was left where the browser turns the write down", async () => {
    standing(refusing);

    await expect(copied(LINE)).resolves.toBe(false);
  });

  it("says it was left where the clipboard answers neither way, so a press ends in a word however it goes", async () => {
    standing(silent);

    await expect(copied(LINE)).resolves.toBe(false);
  });
});
