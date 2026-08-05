import type { PointerEvent } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { PositionView } from "../src/api/views";
import { NOTHING_LANDED } from "../src/play/arrivals";
import { prospect } from "../src/play/selection";
import type { Carry, Handling, Places, Point } from "../src/table/dragging";
import { carriedTo, grasped, handled, laidOut, moved, nearest, sent, travelled } from "../src/table/dragging";
import type { Placement } from "../src/table/placing";
import { own, shared } from "../src/table/placing";
import { Zones } from "../src/table/Zones";
import { aLayout, aPlaying, aView, card, DEALT_FROM, HAND, HELD, LAID_ON, PILE, sortable, STACK } from "./tables";

/** The run these tests carry a card through, which is a hand of four read by its ranks. */
const RUN = ["9♦", "8♠", "4♦", "K♣"];

/** Where that run is drawn: four places a hundred apart, all of them at the one height a run lies at. */
const PLACES: Places = { middles: [100, 200, 300, 400], along: 500 };

/** The press a pointer makes of itself, and one it makes of a button standing beside that. */
const PRESSED = 0;
const BESIDES = 2;

/** The pointer these tests press with, which is the one a card takes hold of. */
const POINTER = 7;

/** How far a hand may wander and still read as a press, which is what a card carried a place along outruns. */
const A_NUDGE = 4;

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

/** The card at the second place taken hold of a little right of the middle of it, as a hand on it would be. */
const TAKEN = grasped(1, PLACES, { across: 210, down: 505 });

/** How one place of a run is handled, which a test states the part of it that it means to read. */
function handling(answers: Partial<Handling>): Handling {
  return { carried: false, travel: null, grasp: IDLE, carry: IDLE, release: IDLE, abandon: IDLE, ...answers };
}

/** What a card was told to do with the pointer pressing it, which is what holds that pointer to that card. */
interface Holding {
  pointer: number | null;
}

/** One press on a card at one point, as the page delivers it and as a card takes hold of the pointer making it. */
function aPress(button: number, at: Point, holding: Holding): PointerEvent<HTMLElement> {
  return {
    button,
    pointerId: POINTER,
    clientX: at.across,
    clientY: at.down,
    currentTarget: {
      setPointerCapture: (pointer: number): void => {
        holding.pointer = pointer;
      },
    },
  } as unknown as PointerEvent<HTMLElement>;
}

/** The carry one point states of the card in hand, which every point states of a card taken hold of. */
function carriedFrom(taken: Carry, at: Point): Carry {
  const carried = carriedTo(taken, PLACES, at);
  if (carried === null) {
    throw new Error("a card taken hold of is carried by every point the pointer stands at");
  }

  return carried;
}

function drawn(view: PositionView, place: Placement): string {
  const slots = place === "own" ? own(LAYOUT) : shared(LAYOUT);
  return renderToStaticMarkup(
    <Zones place={place} slots={slots} view={view} arrivals={NOTHING_LANDED} playing={RESTING} />,
  );
}

/** How many cards of one drawing a player may take hold of. */
function grippable(drawing: string): number {
  return [...drawing.matchAll(/sortable/g)].length;
}

describe("the place of a run one point stands at", () => {
  it("is the place whose middle it lies nearest, so a card passes the halfway mark to reach the next", () => {
    expect(nearest(PLACES.middles, 240)).toBe(1);
    expect(nearest(PLACES.middles, 260)).toBe(2);
  });

  it("is the middle of a place a point stands exactly at", () => {
    expect(nearest(PLACES.middles, 300)).toBe(2);
  });

  it("is the nearer end of the run for a point standing beyond either end of it", () => {
    expect(nearest(PLACES.middles, -400)).toBe(0);
    expect(nearest(PLACES.middles, 4000)).toBe(3);
  });

  it("is the one place of a run drawn at a single place, wherever the point stands", () => {
    expect(nearest([100], 4000)).toBe(0);
  });
});

describe("a card carried to another place of the run it lies in", () => {
  it("comes to lie at the place it was let go at, and the cards it passed over close up behind it", () => {
    expect(laidOut(RUN, { ...TAKEN, from: 0, to: 2 })).toEqual(["8♠", "4♦", "9♦", "K♣"]);
  });

  it("reads the same way carried back the other way, which is the run read from the far end", () => {
    expect(laidOut(RUN, { ...TAKEN, from: 3, to: 1 })).toEqual(["9♦", "K♣", "8♠", "4♦"]);
  });

  it("lies first or last where it was carried to either end of the run", () => {
    expect(laidOut(RUN, { ...TAKEN, from: 2, to: 0 })).toEqual(["4♦", "9♦", "8♠", "K♣"]);
    expect(laidOut(RUN, { ...TAKEN, from: 1, to: RUN.length - 1 })).toEqual(["9♦", "4♦", "K♣", "8♠"]);
  });

  it("holds every card of the run, whichever card was carried and wherever it came to lie", () => {
    for (const from of RUN.keys()) {
      for (const to of RUN.keys()) {
        expect([...laidOut(RUN, { ...TAKEN, from, to })].sort()).toEqual([...RUN].sort());
      }
    }
  });

  it("leaves the run as it lies where it was carried to the place it came from", () => {
    expect(laidOut(RUN, { ...TAKEN, from: 2, to: 2 })).toEqual(RUN);
  });

  it("leaves the run as it lies where the place taken from is one the run holds no card at", () => {
    expect(laidOut(RUN, { ...TAKEN, from: RUN.length, to: 0 })).toEqual(RUN);
  });

  it("leaves the run as it lies while no card is being carried through it at all", () => {
    expect(laidOut(RUN, null)).toEqual(RUN);
  });
});

describe("a card taken hold of", () => {
  it("lies where it lay until it is carried off, which is a run standing as it stood", () => {
    expect(TAKEN.from).toBe(1);
    expect(TAKEN.to).toBe(1);
    expect(TAKEN.by).toEqual({ across: 0, down: 0 });
    expect(moved(TAKEN)).toBe(false);
    expect(laidOut(RUN, TAKEN)).toEqual(RUN);
  });

  it("is held where the hand took it, which is what it hangs from as it travels", () => {
    expect(TAKEN.held).toEqual({ across: 10, down: 5 });
  });

  it("says there is an order to lay down once the pointer has carried it to another place", () => {
    const carried = carriedFrom(TAKEN, { across: 320, down: 480 });

    expect(carried.to).toBe(2);
    expect(moved(carried)).toBe(true);
  });

  it("stands under the hand carrying it wherever the run has opened, which is the card the player moves", () => {
    for (const across of [100, 155, 260, 380, 640]) {
      const carried = carriedFrom(TAKEN, { across, down: 470 });
      const middle = PLACES.middles.at(carried.to);

      expect(middle).toBeDefined();
      expect((middle ?? 0) + carried.held.across + carried.by.across).toBe(across);
      expect(PLACES.along + carried.held.down + carried.by.down).toBe(470);
    }
  });

  it("keeps the place it was taken from however far it is carried", () => {
    expect(carriedFrom(TAKEN, { across: 4000, down: 500 }).from).toBe(1);
    expect(carriedFrom(carriedFrom(TAKEN, { across: 400, down: 500 }), { across: 100, down: 500 }).from).toBe(1);
  });

  it("carries nothing where nothing was taken hold of", () => {
    expect(carriedTo(null, PLACES, { across: 300, down: 500 })).toBeNull();
  });
});

describe("the hand on a card", () => {
  it("reads as a press where it has gone as good as nowhere from the point it set out from", () => {
    expect(travelled(TAKEN, { across: 210, down: 505 })).toBe(false);
    expect(travelled(TAKEN, { across: 213, down: 503 })).toBe(false);
  });

  it("reads as carrying the card once it has taken it anywhere at all", () => {
    expect(travelled(TAKEN, { across: 250, down: 505 })).toBe(true);
    expect(travelled(TAKEN, { across: 210, down: 475 })).toBe(true);
  });

  it("reads as carrying a card taken a whole place along, which stands barely off the place it reached", () => {
    const carried = carriedFrom(TAKEN, { across: 310, down: 505 });

    expect(carried.to).toBe(2);
    expect(Math.abs(carried.by.across)).toBeLessThanOrEqual(A_NUDGE);
    expect(travelled(carried, { across: 310, down: 505 })).toBe(true);
  });
});

describe("the order letting a carried card go sends", () => {
  it("is the run as it lies in front of the player, which is the reading the drawing of it stands by", () => {
    expect(sent(RUN, { ...TAKEN, from: 0, to: 2 })).toEqual(["8♠", "4♦", "9♦", "K♣"]);
    expect(sent(RUN, carriedFrom(TAKEN, { across: 400, down: 500 }))).toEqual(["9♦", "4♦", "K♣", "8♠"]);
  });

  it("is that order however far from the run the card was let go, since the run is what was being read", () => {
    expect(sent(RUN, carriedFrom(TAKEN, { across: 4000, down: 4000 }))).toEqual(["9♦", "4♦", "K♣", "8♠"]);
  });

  it("is nothing where the card was carried home again, which leaves the order the table already holds", () => {
    expect(sent(RUN, TAKEN)).toBeNull();
    expect(
      sent(RUN, carriedFrom(carriedFrom(TAKEN, { across: 400, down: 500 }), { across: 205, down: 500 })),
    ).toBeNull();
  });

  it("is nothing where no card was carried through the run at all", () => {
    expect(sent(RUN, null)).toBeNull();
  });
});

describe("the handling one place of a run states", () => {
  it("takes hold of the card pressed and holds the pointer to it, so the card follows it from then on", () => {
    const holding: Holding = { pointer: null };
    let taken: Point | null = null;
    const answers = handled(
      handling({
        grasp: (at) => {
          taken = at;
        },
      }),
    );

    answers.onPointerDown?.(aPress(PRESSED, { across: 210, down: 505 }, holding));

    expect(holding.pointer).toBe(POINTER);
    expect(taken).toEqual({ across: 210, down: 505 });
  });

  it("takes nothing hold of under a press made by a button standing beside the pointer's own", () => {
    const holding: Holding = { pointer: null };
    let taken: Point | null = null;
    const answers = handled(
      handling({
        grasp: (at) => {
          taken = at;
        },
      }),
    );

    answers.onPointerDown?.(aPress(BESIDES, { across: 210, down: 505 }, holding));

    expect(holding.pointer).toBeNull();
    expect(taken).toBeNull();
  });

  it("carries the card to every point the pointer stands at", () => {
    let reached: Point | null = null;
    const answers = handled(
      handling({
        carry: (at) => {
          reached = at;
        },
      }),
    );

    answers.onPointerMove?.(aPress(PRESSED, { across: 340, down: 470 }, { pointer: null }));

    expect(reached).toEqual({ across: 340, down: 470 });
  });

  it("lets the card go at the point the pointer let it go, which is the answer a carry always reaches", () => {
    let released: Point | null = null;
    const answers = handled(
      handling({
        release: (at) => {
          released = at;
        },
      }),
    );

    answers.onPointerUp?.(aPress(PRESSED, { across: 380, down: 520 }, { pointer: null }));

    expect(released).toEqual({ across: 380, down: 520 });
  });

  it("leaves the run as it stood where the carry is taken out of the player's hand", () => {
    let abandoned = false;
    const answers = handled(
      handling({
        abandon: () => {
          abandoned = true;
        },
      }),
    );

    answers.onPointerCancel?.();

    expect(abandoned).toBe(true);
  });

  it("draws a card where the run puts it, and a card in hand where the pointer has carried it", () => {
    expect(handled(handling({ travel: null })).style).toBeUndefined();
    expect(handled(handling({ travel: { across: 12, down: -30 } })).style).toEqual({
      transform: "translate(12px, -30px)",
    });
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
