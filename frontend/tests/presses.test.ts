import type { MouseEvent } from "react";
import { describe, expect, it } from "vitest";

import { answering, clicking } from "../src/table/clicks";
import { clears } from "../src/table/keys";

/** A press as the page receives one, which reports what the answer to it did with the event. */
interface Press {
  answered: boolean;
  stopped: boolean;
  prevented: boolean;
}

function pressed(answer: (event: MouseEvent) => void): Press {
  const press = { answered: false, stopped: false, prevented: false };
  answer({
    stopPropagation: () => {
      press.stopped = true;
    },
    preventDefault: () => {
      press.prevented = true;
    },
  } as unknown as MouseEvent);
  return press;
}

describe("a press the page answers", () => {
  it("stops a click where it was answered, so the page beneath makes nothing of it", () => {
    const press = pressed(clicking(() => undefined));

    expect(press.stopped).toBe(true);
    expect(press.prevented).toBe(false);
  });

  it("takes the other button over from the browser, and lets it travel up to the page", () => {
    const press = pressed(answering(() => undefined));

    expect(press.prevented).toBe(true);
    expect(press.stopped).toBe(false);
  });

  it("carries the answer through in either case", () => {
    for (const wrap of [clicking, answering]) {
      let answered = false;
      pressed(
        wrap(() => {
          answered = true;
        }),
      );

      expect(answered).toBe(true);
    }
  });
});

describe("the key a selection is put down with", () => {
  it("reads the one every page is backed out of", () => {
    expect(clears("Escape")).toBe(true);
  });

  it("leaves every other keystroke to the page", () => {
    for (const key of ["Enter", " ", "Esc", "escape", "a"]) {
      expect(clears(key)).toBe(false);
    }
  });
});
