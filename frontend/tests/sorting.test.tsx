import type { PointerEvent } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { PositionView } from "../src/api/views";
import { NOTHING_LANDED } from "../src/play/arrivals";
import { prospect } from "../src/play/selection";
import type { Playing } from "../src/play/usePlay";
import type { Carry, Handling, Places, Point, Shift } from "../src/table/dragging";
import {
  carriedTo,
  grasped,
  handled,
  heldAt,
  laidOut,
  moved,
  nearest,
  over,
  placesOf,
  restingOn,
  sent,
  travelled,
} from "../src/table/dragging";
import type { Placement } from "../src/table/placing";
import { own, shared } from "../src/table/placing";
import { Zones } from "../src/table/Zones";
import { aLayout, aPlaying, aView, card, DEALT_FROM, HAND, HELD, LAID_ON, PILE, sortable, STACK } from "./tables";

/** The run these tests carry cards through, which is a hand of four read by its ranks. */
const RUN = ["9♦", "8♠", "4♦", "K♣"];

/**
 * Where that run is drawn: four places a hundred apart, all of them at the one height a run lies at, each card
 * of it reaching wider than the places stand apart — which is a fan, where each card covers the one before. The
 * order of it is this seat's own to set, which is what a carry through it lays down.
 */
const PLACES: Places = {
  middles: [100, 200, 300, 400],
  along: 500,
  reach: { across: 140, down: 190 },
  orderable: true,
};

/** The same run with the table keeping the order of it, which is a run carried out of and never through. */
const KEPT: Places = { ...PLACES, orderable: false };

/** The press a pointer makes of itself, and one it makes of a button standing beside that. */
const PRESSED = 0;
const BESIDES = 2;

/** The pointer these tests press with, which is the one a card takes hold of. */
const POINTER = 7;

/** How far a hand may wander and still read as a press, which is what a card carried a place along outruns. */
const A_NUDGE = 4;

/** Where the hand takes hold of a card of a fan to press the part of it that lies over the card before it. */
const AN_EDGE: Point = { across: 140, down: 505 };

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
const TAKEN = grasped(1, [], PLACES, { across: 210, down: 505 });

/** The third card of the run pressed with the first already in hand, which takes hold of the two of them. */
const GATHERED = grasped(2, [0, 2], PLACES, { across: 310, down: 505 });

/** How one place of a run is handled, which a test states the part of it that it means to read. */
function handling(answers: Partial<Handling>): Handling {
  return {
    carried: false,
    laid: false,
    travel: null,
    grasp: IDLE,
    carry: IDLE,
    release: IDLE,
    abandon: IDLE,
    leave: IDLE,
    ...answers,
  };
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

/** Cards the hand has carried, which stand off the places the run draws them by however far they have come. */
interface Carried extends Carry {
  by: Shift;
}

/** The carry one point states of the cards in hand, which every point states of cards taken hold of. */
function pressedTo(taken: Carry, at: Point): Carry {
  const carried = carriedTo(taken, PLACES, at);
  if (carried === null) {
    throw new Error("cards taken hold of are carried by every point the pointer stands at");
  }

  return carried;
}

/** The same, of a point the hand has carried the cards to, which is cards standing off their places. */
function carriedFrom(taken: Carry, at: Point): Carried {
  const carried = pressedTo(taken, at);
  if (carried.by === null) {
    throw new Error("cards the hand has carried anywhere stand off the places the run draws them");
  }

  return { ...carried, by: carried.by };
}

/** Where the run draws the card the hand pressed, which is what the block of cards in hand hangs from. */
function pressedAt(carried: Carry): number {
  const place = heldAt(carried).at(carried.rank);
  if (place === undefined) {
    throw new Error("the cards in hand hold the card the hand pressed among them");
  }

  return place;
}

/** Where one place of the run is drawn, for a test reading a card against the place it stands at. */
function middleOf(place: number): number {
  const middle = PLACES.middles.at(place);
  if (middle === undefined) {
    throw new Error("a card lies at a place the run draws");
  }

  return middle;
}

function drawing(view: PositionView, place: Placement, playing: Playing): string {
  const slots = place === "own" ? own(LAYOUT) : shared(LAYOUT);
  return renderToStaticMarkup(
    <Zones place={place} slots={slots} view={view} arrivals={NOTHING_LANDED} playing={playing} />,
  );
}

function drawn(view: PositionView, place: Placement): string {
  return drawing(view, place, RESTING);
}

/** The cards of one drawing, in the order the page draws them, each read by the name it carries. */
function named(drawing: string): string[] {
  return [...drawing.matchAll(/aria-label="([^"]*)"/g)].map((mark) => mark[1] ?? "");
}

/** How many cards of one drawing a player may take hold of. */
function grippable(drawing: string): number {
  return [...drawing.matchAll(/carryable/g)].length;
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
    expect(laidOut(RUN, { ...TAKEN, from: [0], to: 2 })).toEqual(["8♠", "4♦", "9♦", "K♣"]);
  });

  it("reads the same way carried back the other way, which is the run read from the far end", () => {
    expect(laidOut(RUN, { ...TAKEN, from: [3], to: 1 })).toEqual(["9♦", "K♣", "8♠", "4♦"]);
  });

  it("lies first or last where it was carried to either end of the run", () => {
    expect(laidOut(RUN, { ...TAKEN, from: [2], to: 0 })).toEqual(["4♦", "9♦", "8♠", "K♣"]);
    expect(laidOut(RUN, { ...TAKEN, from: [1], to: RUN.length - 1 })).toEqual(["9♦", "4♦", "K♣", "8♠"]);
  });

  it("holds every card of the run, whichever card was carried and wherever it came to lie", () => {
    for (const from of RUN.keys()) {
      for (const to of RUN.keys()) {
        expect([...laidOut(RUN, { ...TAKEN, from: [from], to })].sort()).toEqual([...RUN].sort());
      }
    }
  });

  it("leaves the run as it lies where it was carried to the place it came from", () => {
    expect(laidOut(RUN, { ...TAKEN, from: [2], to: 2 })).toEqual(RUN);
  });

  it("leaves the run as it lies where the place taken from is one the run holds no card at", () => {
    expect(laidOut(RUN, { ...TAKEN, from: [RUN.length], to: 0 })).toEqual(RUN);
  });

  it("leaves the run as it lies while no card is being carried through it at all", () => {
    expect(laidOut(RUN, null)).toEqual(RUN);
  });

  it("leaves the run as it lies while the hand is carrying the card clear of it", () => {
    expect(laidOut(RUN, { ...TAKEN, from: [0], to: null, by: { across: 30, down: -400 } })).toEqual(RUN);
  });
});

describe("the cards one press takes hold of", () => {
  it("are the cards in hand where the card pressed is one of them", () => {
    expect(GATHERED.from).toEqual([0, 2]);
    expect(GATHERED.rank).toBe(1);
  });

  it("are that card alone where the cards in hand are other cards of the run", () => {
    const alone = grasped(1, [0, 2], PLACES, { across: 210, down: 505 });

    expect(alone.from).toEqual([1]);
    expect(alone.rank).toBe(0);
  });

  it("are that card alone where the player is holding nothing at all", () => {
    expect(TAKEN.from).toEqual([1]);
    expect(TAKEN.rank).toBe(0);
  });

  it("lie in the order the run reads them, whichever order the player picked them up in", () => {
    const picked = grasped(2, [2, 0], PLACES, { across: 310, down: 505 });

    expect(picked.from).toEqual([0, 2]);
    expect(picked.rank).toBe(1);
  });
});

describe("cards carried together", () => {
  it("come to lie in a block at the place they were let go at, whichever places they came out of", () => {
    expect(laidOut(RUN, { ...GATHERED, to: 1 })).toEqual(["8♠", "9♦", "4♦", "K♣"]);
  });

  it("lie along the end of the run the hand carried them past, since a run holds the cards it holds", () => {
    const far = carriedFrom(GATHERED, { across: 470, down: 505 });
    const near = carriedFrom(GATHERED, { across: 40, down: 505 });

    expect(far.to).toBe(RUN.length - GATHERED.from.length);
    expect(laidOut(RUN, far)).toEqual(["8♠", "K♣", "9♦", "4♦"]);
    expect(near.to).toBe(0);
    expect(laidOut(RUN, near)).toEqual(["9♦", "4♦", "8♠", "K♣"]);
  });

  it("say there is an order to lay down even where the first of them stays where it lay", () => {
    expect(moved({ ...GATHERED, to: 0 })).toBe(true);
    expect(laidOut(RUN, { ...GATHERED, to: 0 })).toEqual(["9♦", "4♦", "8♠", "K♣"]);
  });

  it("say there is none where the run already reads them as the block they are", () => {
    expect(moved({ ...GATHERED, from: [1, 2], to: 1 })).toBe(false);
  });

  it("stand off their places by the one shift, with the pressed card under the hand", () => {
    const carried = carriedFrom(GATHERED, { across: 250, down: 470 });

    expect(heldAt(carried)).toEqual([0, 1]);
    expect(carried.by).toEqual({ across: 40, down: -35 });
    expect(middleOf(pressedAt(carried)) + carried.held.across + carried.by.across).toBe(250);
    expect(PLACES.along + carried.held.down + carried.by.down).toBe(470);
  });

  it("keep the places they came out of while the hand is carrying them clear of the run", () => {
    const away = carriedFrom(GATHERED, { across: 310, down: 900 });

    expect(away.to).toBeNull();
    expect(heldAt(away)).toEqual([0, 2]);
  });
});

describe("a card taken hold of", () => {
  it("lies where it lay until it is carried off, which is a run standing as it stood", () => {
    expect(TAKEN.to).toBeNull();
    expect(TAKEN.by).toBeNull();
    expect(moved(TAKEN)).toBe(false);
    expect(laidOut(RUN, TAKEN)).toEqual(RUN);
  });

  it("is held where the hand took it, which is what it hangs from as it travels", () => {
    expect(TAKEN.held).toEqual({ across: 10, down: 5 });
  });

  it("lies where it lay under a hand that has gone as good as nowhere, which is what a click leaves it", () => {
    const still = pressedTo(TAKEN, { across: 213, down: 503 });

    expect(still.to).toBeNull();
    expect(still.by).toBeNull();
    expect(moved(still)).toBe(false);
  });

  it("lies where it lay pressed by the part of it lying over the card before it, which no click carries", () => {
    const edge = grasped(1, [], PLACES, AN_EDGE);
    const still = pressedTo(edge, AN_EDGE);

    expect(edge.held).toEqual({ across: -60, down: 5 });
    expect(still.to).toBeNull();
    expect(sent(RUN, still)).toBeNull();
  });

  it("goes where the card goes rather than where the pointer within it stands, whichever part was pressed", () => {
    const edge = grasped(1, [], PLACES, AN_EDGE);

    expect(carriedFrom(edge, { across: 240, down: 505 }).to).toBe(2);
    expect(carriedFrom(edge, { across: 190, down: 505 }).to).toBe(1);
  });

  it("stays carried once it has been carried, however far back towards the press the hand comes", () => {
    const carried = carriedFrom(TAKEN, { across: 260, down: 505 });

    expect(carriedFrom(carried, { across: 211, down: 506 }).by).not.toBeNull();
  });

  it("says there is an order to lay down once the pointer has carried it to another place", () => {
    const carried = carriedFrom(TAKEN, { across: 320, down: 480 });

    expect(carried.to).toBe(2);
    expect(moved(carried)).toBe(true);
  });

  it("stands under the hand carrying it wherever the run draws it, which is the card the player moves", () => {
    for (const across of [100, 155, 260, 380, 640]) {
      const carried = carriedFrom(TAKEN, { across, down: 470 });

      expect(middleOf(pressedAt(carried)) + carried.held.across + carried.by.across).toBe(across);
      expect(PLACES.along + carried.held.down + carried.by.down).toBe(470);
    }
  });

  it("keeps the place it was taken from however far it is carried", () => {
    expect(carriedFrom(TAKEN, { across: 4000, down: 500 }).from).toEqual([1]);
    expect(carriedFrom(carriedFrom(TAKEN, { across: 400, down: 500 }), { across: 100, down: 500 }).from).toEqual([1]);
  });

  it("carries nothing where nothing was taken hold of", () => {
    expect(carriedTo(null, PLACES, { across: 300, down: 500 })).toBeNull();
  });
});

describe("a card of a run whose order the table keeps", () => {
  it("travels under the hand with the run standing as it stood, wherever the hand carries it", () => {
    const taken = grasped(1, [], KEPT, { across: 210, down: 505 });
    const carried = carriedTo(taken, KEPT, { across: 260, down: 505 });

    expect(carried?.to).toBeNull();
    expect(carried?.by).toEqual({ across: 50, down: 0 });
    expect(laidOut(RUN, carried)).toEqual(RUN);
    expect(sent(RUN, carried)).toBeNull();
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

describe("the place of a run one point stands over", () => {
  it("is the place whose card covers it, which a point at the middle of one stands over", () => {
    expect(over(PLACES, { across: 100, down: 500 })).toBe(0);
  });

  it("is the later of two places whose cards cover it, which is the card drawn over the other", () => {
    expect(over(PLACES, { across: 260, down: 500 })).toBe(2);
  });

  it("is the last place of the run for a point past the middle of it, which no card is drawn over", () => {
    expect(over(PLACES, { across: 460, down: 500 })).toBe(3);
  });

  it("is none for a point standing clear of the run, above it, below it or beyond either end", () => {
    expect(over(PLACES, { across: 260, down: 300 })).toBeNull();
    expect(over(PLACES, { across: 260, down: 700 })).toBeNull();
    expect(over(PLACES, { across: 20, down: 500 })).toBeNull();
    expect(over(PLACES, { across: 480, down: 500 })).toBeNull();
  });
});

describe("the place a hand rests on having laid a card down at it", () => {
  it("is the place the card came to lie at, which the hand that carried it there is still on", () => {
    const carried = carriedFrom(TAKEN, { across: 310, down: 505 });

    expect(restingOn(carried, PLACES, { across: 310, down: 505 })).toBe(2);
  });

  it("is the place the pressed card came to lie at, of the cards a hand carried together", () => {
    const carried = carriedFrom(GATHERED, { across: 210, down: 505 });

    expect(heldAt(carried)).toEqual([0, 1]);
    expect(restingOn(carried, PLACES, { across: 210, down: 505 })).toBe(1);
  });

  it("is none where the hand let the card go over the card lying beside it", () => {
    const carried = carriedFrom(TAKEN, { across: 250, down: 505 });

    expect(carried.to).toBe(1);
    expect(restingOn(carried, PLACES, { across: 250, down: 505 })).toBeNull();
  });

  it("is none where the hand came off the run altogether", () => {
    const carried = carriedFrom(TAKEN, { across: 310, down: 900 });

    expect(restingOn(carried, PLACES, { across: 310, down: 900 })).toBeNull();
  });

  it("is none where the press carried the card nowhere at all, since a click lays nothing down", () => {
    expect(restingOn(pressedTo(TAKEN, { across: 212, down: 504 }), PLACES, { across: 212, down: 504 })).toBeNull();
  });
});

describe("where a run draws its places", () => {
  it("is nothing at all for a run the page draws none of, which is a zone no card is taken hold of in", () => {
    expect(placesOf(null, true)).toBeNull();
  });
});

describe("the order letting the carried cards go sends", () => {
  it("is the run as it lies in front of the player, which is the reading the drawing of it stands by", () => {
    expect(sent(RUN, { ...TAKEN, from: [0], to: 2 })).toEqual(["8♠", "4♦", "9♦", "K♣"]);
    expect(sent(RUN, carriedFrom(TAKEN, { across: 400, down: 500 }))).toEqual(["9♦", "4♦", "K♣", "8♠"]);
  });

  it("is nothing where the cards were carried home again, which leaves the order the table already holds", () => {
    expect(sent(RUN, TAKEN)).toBeNull();
    expect(
      sent(RUN, carriedFrom(carriedFrom(TAKEN, { across: 400, down: 500 }), { across: 205, down: 500 })),
    ).toBeNull();
  });

  it("is nothing where the hand carried the cards clear of the run, which leaves them somewhere else to go", () => {
    expect(sent(RUN, carriedFrom(TAKEN, { across: 4000, down: 4000 }))).toBeNull();
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

  it("says when the hand has come off the card, which is what a card laid down under one is read against", () => {
    let off = false;
    const answers = handled(
      handling({
        leave: () => {
          off = true;
        },
      }),
    );

    answers.onPointerLeave?.();

    expect(off).toBe(true);
  });

  it("draws a card where the run puts it, and a card in hand where the pointer has carried it", () => {
    expect(handled(handling({ travel: null })).style).toBeUndefined();
    expect(handled(handling({ travel: { across: 12, down: -30 } })).style).toEqual({
      transform: "translate(12px, -30px)",
    });
  });

  it("gives it nothing where the run is one no card is taken hold of in, so the card is carried nowhere", () => {
    expect(handled(null)).toEqual({});
  });
});

describe("a zone the table says this seat lays out", () => {
  it("offers every card of it to be taken hold of, and marks the run as one to grip", () => {
    const hand = drawn(sortable(POSITION, HAND), "own");

    expect(grippable(hand)).toBe(3);
    expect([...hand.matchAll(/carryable/g)]).toHaveLength(3);
  });

  it("draws the run in the order the player laid it, while the table has yet to hand that order back", () => {
    const laid = drawing(sortable(POSITION, HAND), "own", { ...RESTING, laidIn: () => [2, 0, 1] });

    expect(named(laid)).toEqual(["4♦", "9♦", "8♠"]);
  });

  it("draws the run as the table holds it where a laid order names some other run than the one drawn", () => {
    const laid = drawing(sortable(POSITION, HAND), "own", { ...RESTING, laidIn: () => [0, 1] });

    expect(named(laid)).toEqual(["9♦", "8♠", "4♦"]);
  });

  it("draws the cards as it drew them, since ordering a run stands beside playing out of it", () => {
    const held = drawn(POSITION, "own");
    const laid = drawn(sortable(POSITION, HAND), "own");

    expect([...laid.matchAll(/class="card face/g)]).toHaveLength([...held.matchAll(/class="card face/g)].length);
    expect(laid).not.toContain("carried");
  });
});

describe("a zone whose order the table keeps", () => {
  it("offers no card of the shared table to be taken hold of, since no move of this seat picks in it", () => {
    expect(grippable(drawn(POSITION, "shared"))).toBe(0);
  });

  it("offers none of this seat's own where the table has said nothing of the order being its to set", () => {
    expect(grippable(drawn(POSITION, "own"))).toBe(0);
    expect(drawn(POSITION, "own")).not.toContain("carryable");
  });

  it("offers none of a heap read by the card on top of it, whatever the table says of its order", () => {
    expect(grippable(drawn(sortable(POSITION, STACK), "shared"))).toBe(0);
  });

  it("offers the one card of a heap read out to the last of them, which is a run drawn whole", () => {
    const last = aView({ [STACK]: [card("2", "♣")] }, 4);

    expect(grippable(drawn(sortable(last, STACK), "shared"))).toBe(1);
  });
});
