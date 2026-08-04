import { describe, expect, it } from "vitest";

import type { Viewing } from "../src/play/viewing";
import { whileInView } from "../src/play/viewing";

/** One page a test looks at and looks away from, and every change it stands listening for. */
interface Looked {
  page: Viewing;
  look: () => void;
  away: () => void;
  listening: () => string[];
}

/** One thing held: taking it up, and the count of each way that has gone. */
interface Kept {
  hold: () => () => void;
  holds: () => number;
  releases: () => number;
}

function aPage(hidden: boolean): Looked {
  const noticed = new Map<() => void, string>();
  const page: Viewing = {
    hidden,
    addEventListener: (change, told) => {
      noticed.set(told, change);
    },
    removeEventListener: (change, told) => {
      if (noticed.get(told) === change) {
        noticed.delete(told);
      }
    },
  };
  const turned = (away: boolean) => (): void => {
    page.hidden = away;
    [...noticed.keys()].forEach((told) => {
      told();
    });
  };

  return { page, look: turned(false), away: turned(true), listening: () => [...noticed.values()] };
}

function aThing(): Kept {
  let holds = 0;
  let releases = 0;
  return {
    hold: () => {
      holds += 1;
      return () => {
        releases += 1;
      };
    },
    holds: () => holds,
    releases: () => releases,
  };
}

describe("what a page holds while it is in view", () => {
  it("is taken up at once by a page in view, which is the tab the player is reading", () => {
    const looked = aPage(false);
    const kept = aThing();

    whileInView(looked.page, kept.hold);

    expect([kept.holds(), kept.releases()]).toEqual([1, 0]);
    expect(looked.listening()).toEqual(["visibilitychange"]);
  });

  it("is left alone by a page opened out of view, which is every tab but the one in front", () => {
    const looked = aPage(true);
    const kept = aThing();

    whileInView(looked.page, kept.hold);

    expect([kept.holds(), kept.releases()]).toEqual([0, 0]);
  });

  it("goes as the page goes out of view, and is taken up afresh as the page comes back", () => {
    const looked = aPage(false);
    const kept = aThing();
    whileInView(looked.page, kept.hold);

    looked.away();
    expect([kept.holds(), kept.releases()]).toEqual([1, 1]);

    looked.look();
    expect([kept.holds(), kept.releases()]).toEqual([2, 1]);
  });

  it("stands as the one thing it is, however often the page reports the way it is turned", () => {
    const looked = aPage(false);
    const kept = aThing();
    whileInView(looked.page, kept.hold);

    looked.look();
    looked.look();

    expect([kept.holds(), kept.releases()]).toEqual([1, 0]);
  });

  it("goes once for a page turned away twice over", () => {
    const looked = aPage(false);
    const kept = aThing();
    whileInView(looked.page, kept.hold);

    looked.away();
    looked.away();

    expect(kept.releases()).toBe(1);
  });

  it("goes for good when the holding is stopped, and the page reports to nobody thereafter", () => {
    const looked = aPage(false);
    const kept = aThing();
    const stop = whileInView(looked.page, kept.hold);

    stop();

    expect([kept.holds(), kept.releases()]).toEqual([1, 1]);
    expect(looked.listening()).toEqual([]);

    looked.look();
    expect(kept.holds()).toBe(1);
  });

  it("goes once where the holding is stopped while the page stands out of view", () => {
    const looked = aPage(false);
    const kept = aThing();
    const stop = whileInView(looked.page, kept.hold);

    looked.away();
    stop();

    expect([kept.holds(), kept.releases()]).toEqual([1, 1]);
  });
});
