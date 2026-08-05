import type { DragEvent } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { PositionView } from "../src/api/views";
import { NOTHING_LANDED } from "../src/play/arrivals";
import { prospect } from "../src/play/selection";
import type { Handling } from "../src/table/dragging";
import { allowing, carriedTo, grasped, grasping, handled, laidOut, moved, reaching } from "../src/table/dragging";
import type { Placement } from "../src/table/placing";
import { own, shared } from "../src/table/placing";
import { Zones } from "../src/table/Zones";
import { aLayout, aPlaying, aView, card, DEALT_FROM, HAND, HELD, LAID_ON, PILE, sortable, STACK } from "./tables";

/** The run these tests carry a card through, which is a hand of four read by its ranks. */
const RUN = ["9♦", "8♠", "4♦", "K♣"];

/** The name a card travels under, which is one place of one run and nothing another page could want. */
const PLACE = "application/x-cardwork-place";

const LAYOUT = aLayout({ slots: [HELD, DEALT_FROM, LAID_ON] });

const POSITION: PositionView = aView(
  {
    [HAND]: [card("9", "♦"), card("8", "♠"), card("4", "♦")],
    [PILE]: [null, null, null, null],
    [STACK]: [card("2", "♣"), card("5", "♥")],
  },
  4,
);

/** A table at rest, since what these tests read is the drawing of it rather than the moves it offers. */
const RESTING = aPlaying(prospect([], null));

/** A place of a run answering nothing at all, for a test stating the one answer it is reading. */
const IDLE = (): void => undefined;

/** How one place of a run is handled, which a test states the part of it that it means to read. */
function handling(answers: Partial<Handling>): Handling {
  return { place: 0, carried: false, grasp: IDLE, reach: IDLE, release: IDLE, ...answers };
}

/** A drag as one place of a run receives it, which reports what the answer to it did with the event. */
interface Carried {
  prevented: boolean;
  effect: string;
  payload: Record<string, string>;
}

function carried(answer: ((event: DragEvent) => void) | undefined): Carried {
  const drag: Carried = { prevented: false, effect: "", payload: {} };
  answer?.({
    preventDefault: () => {
      drag.prevented = true;
    },
    dataTransfer: {
      set effectAllowed(effect: string) {
        drag.effect = effect;
      },
      setData: (name: string, value: string) => {
        drag.payload[name] = value;
      },
    },
  } as unknown as DragEvent);
  return drag;
}

function drawn(view: PositionView, place: Placement): string {
  const slots = place === "own" ? own(LAYOUT) : shared(LAYOUT);
  return renderToStaticMarkup(
    <Zones place={place} slots={slots} view={view} arrivals={NOTHING_LANDED} playing={RESTING} />,
  );
}

/** How many cards of one drawing a player may take hold of. */
function grippable(drawing: string): number {
  return [...drawing.matchAll(/draggable="true"/g)].length;
}

describe("a card carried to another place of the run it lies in", () => {
  it("comes to lie at the place it was let go over, and the cards it passed over close up behind it", () => {
    expect(laidOut(RUN, { from: 0, to: 2 })).toEqual(["8♠", "4♦", "9♦", "K♣"]);
  });

  it("reads the same way carried back the other way, which is the run read from the far end", () => {
    expect(laidOut(RUN, { from: 3, to: 1 })).toEqual(["9♦", "K♣", "8♠", "4♦"]);
  });

  it("lies first or last where it was carried to either end of the run", () => {
    expect(laidOut(RUN, { from: 2, to: 0 })).toEqual(["4♦", "9♦", "8♠", "K♣"]);
    expect(laidOut(RUN, { from: 1, to: RUN.length - 1 })).toEqual(["9♦", "4♦", "K♣", "8♠"]);
  });

  it("holds every card of the run, whichever card was carried and wherever it came to lie", () => {
    for (const from of RUN.keys()) {
      for (const to of RUN.keys()) {
        expect([...laidOut(RUN, { from, to })].sort()).toEqual([...RUN].sort());
      }
    }
  });

  it("leaves the run as it lies where it was carried to the place it came from", () => {
    expect(laidOut(RUN, { from: 2, to: 2 })).toEqual(RUN);
  });

  it("leaves the run as it lies where the place taken from is one the run holds no card at", () => {
    expect(laidOut(RUN, { from: RUN.length, to: 0 })).toEqual(RUN);
  });

  it("leaves the run as it lies while no card is being carried through it at all", () => {
    expect(laidOut(RUN, null)).toEqual(RUN);
  });
});

describe("a card taken hold of", () => {
  it("lies where it lay until it is carried off, which is a run standing as it stood", () => {
    const taken = grasped(2);

    expect(taken).toEqual({ from: 2, to: 2 });
    expect(moved(taken)).toBe(false);
    expect(laidOut(RUN, taken)).toEqual(RUN);
  });

  it("says there is an order to lay down once it has reached another place", () => {
    expect(carriedTo(grasped(2), 0)).toEqual({ from: 2, to: 0 });
    expect(moved({ from: 2, to: 0 })).toBe(true);
  });

  it("keeps the place it was taken from however far it is carried", () => {
    expect(carriedTo(carriedTo(grasped(1), 3), 0)).toEqual({ from: 1, to: 0 });
  });

  it("carries nothing where nothing was taken hold of", () => {
    expect(carriedTo(null, 2)).toBeNull();
  });
});

describe("the drag a card answers", () => {
  it("tells the browser the card is being moved, and names the place it came from", () => {
    let taken = false;
    const drag = carried(
      grasping(2, () => {
        taken = true;
      }),
    );

    expect(taken).toBe(true);
    expect(drag.effect).toBe("move");
    expect(drag.payload).toEqual({ [PLACE]: "2" });
  });

  it("takes a card reaching a place over from the browser, and carries the answer through", () => {
    let reached = false;
    const drag = carried(
      reaching(() => {
        reached = true;
      }),
    );

    expect(drag.prevented).toBe(true);
    expect(reached).toBe(true);
  });

  it("stands by that as the card is carried across the run, which is what lets it be let go there", () => {
    expect(carried(allowing).prevented).toBe(true);
  });
});

describe("the handling one place of a run states", () => {
  it("gives the browser the whole of the gesture, under the place the card lies at", () => {
    const answers = handled(handling({ place: 3 }));

    expect(answers.draggable).toBe(true);
    expect(carried(answers.onDragStart).payload).toEqual({ [PLACE]: "3" });
    expect(carried(answers.onDragEnter).prevented).toBe(true);
  });

  it("lets a card go wherever it ended up, which is the answer a drag always reaches", () => {
    let released = false;
    const answers = handled(
      handling({
        release: () => {
          released = true;
        },
      }),
    );

    answers.onDragEnd?.();

    expect(released).toBe(true);
  });

  it("gives it nothing where the run is one nobody orders, so the card is carried nowhere", () => {
    expect(handled(null)).toEqual({});
  });
});

describe("a zone the table says this seat lays out", () => {
  it("offers every card of it to be taken hold of, and marks the run as one to grip", () => {
    const hand = drawn(sortable(POSITION, HAND), "own");

    expect(grippable(hand)).toBe(3);
    expect([...hand.matchAll(/sortable/g)]).toHaveLength(3);
  });

  it("draws the cards as it drew them, since ordering a run stands beside playing out of it", () => {
    const held = drawn(POSITION, "own");
    const laid = drawn(sortable(POSITION, HAND), "own");

    expect([...laid.matchAll(/class="card face/g)]).toHaveLength([...held.matchAll(/class="card face/g)].length);
    expect(laid).not.toContain("carried");
  });
});

describe("a zone whose order the table keeps", () => {
  it("offers no card of the shared table to be taken hold of", () => {
    expect(grippable(drawn(POSITION, "shared"))).toBe(0);
  });

  it("offers none of this seat's own where the table has said nothing of the order being its to set", () => {
    expect(grippable(drawn(POSITION, "own"))).toBe(0);
    expect(drawn(POSITION, "own")).not.toContain("sortable");
  });

  it("offers none of a heap read by the card on top of it, whatever the table says of its order", () => {
    expect(grippable(drawn(sortable(POSITION, STACK), "shared"))).toBe(0);
  });

  it("offers the one card of a heap read out to the last of them, which is a run drawn whole", () => {
    const last = aView({ [STACK]: [card("2", "♣")] }, 4);

    expect(grippable(drawn(sortable(last, STACK), "shared"))).toBe(1);
  });
});
