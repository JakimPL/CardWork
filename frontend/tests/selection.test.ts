import { describe, expect, it } from "vitest";

import type { Layout } from "../src/api/layout";
import type { PositionView } from "../src/api/views";
import type { Prospect, Selection } from "../src/play/selection";
import {
  isOpen,
  isSelected,
  leadsNowhere,
  offersOf,
  offerTo,
  pickedUp,
  picksIn,
  prospect,
} from "../src/play/selection";
import {
  aDiscard,
  aGive,
  aLayout,
  aPass,
  aTake,
  aView,
  card,
  DISCARDING,
  GIVING,
  HAND,
  offering,
  PASSING,
  PILE,
  TAKING,
} from "./tables";

const TURN = aLayout({ gestures: [TAKING, GIVING] });
const SETS = aLayout({ gestures: [DISCARDING] });

/** A table whose turn a seat may give up, which lays out the gesture that says as much beside the others. */
const CHOICE = aLayout({ gestures: [TAKING, GIVING, PASSING] });

const DEALT = aView({ [HAND]: [card("9", "♦"), card("9", "♠"), card("9", "♥"), card("4", "♦")] }, 1);

/** The whole of one turn of `passing`, which is either card of the hand exchanged or passed. */
const A_TURN = offering(DEALT, [aTake([0]), aTake([2]), aGive(2, [0]), aGive(2, [2])]);

/** A hand three of whose cards read as one rank, which is a discard of two of them or all three. */
const A_SET = offering(DEALT, [aDiscard([0, 1]), aDiscard([0, 2]), aDiscard([1, 2]), aDiscard([0, 1, 2])]);

/** A turn a card answers or a word does, and a turn the word is the whole of. */
const A_TURN_OR_A_WORD = offering(DEALT, [aTake([0]), aGive(2, [0]), aPass()]);
const A_WORD_ALONE = offering(DEALT, [aPass()]);

const standing = (layout: Layout, view: PositionView, selection: Selection | null): Prospect =>
  prospect(offersOf(layout, view), selection);

describe("a move read through the gesture that makes it", () => {
  it("names the zone the cards are picked in and the place the move is sent onto", () => {
    const offers = offersOf(TURN, offering(DEALT, [aTake([2])]));

    expect(offers).toHaveLength(1);
    expect(offers[0]?.picked).toBe(HAND);
    expect(offers[0]?.indices).toEqual([2]);
    expect(offers[0]?.target).toEqual({ commit: "zone", zone: PILE });
    expect(offers[0]?.caption).toBe(TAKING.caption);
  });

  it("takes the seat a move commits onto from the move itself", () => {
    const offers = offersOf(TURN, offering(DEALT, [aGive(2, [0])]));

    expect(offers[0]?.target).toEqual({ commit: "seat", seat: 2 });
  });

  it("tells two moves of one kind apart by the group each names", () => {
    const other = aLayout({ gestures: [{ ...TAKING, group: "stack", target: "stack" }] });

    expect(offersOf(other, offering(DEALT, [aTake([0])]))).toHaveLength(0);
  });

  it("offers no move the layout states no gesture for", () => {
    expect(offersOf(SETS, offering(DEALT, [aTake([0])]))).toHaveLength(0);
  });
});

describe("what a table says can be played", () => {
  it("holds open every card some move names while nothing is picked up", () => {
    const open = standing(TURN, A_TURN, null).open;

    expect([...(open.get(HAND) ?? [])].sort()).toEqual([0, 2]);
    expect(open.has(PILE)).toBe(false);
  });

  it("arms nothing until cards are picked up, so no card click sends a move", () => {
    const bare = standing(TURN, A_TURN, null);

    expect(bare.armed).toHaveLength(0);
    expect(bare.targets).toHaveLength(0);
  });

  it("names the places one picked card can be sent, each of them once", () => {
    const held = standing(TURN, A_TURN, { zone: HAND, indices: [0] });

    expect(held.armed).toHaveLength(2);
    expect(held.targets).toEqual([
      { commit: "zone", zone: PILE },
      { commit: "seat", seat: 2 },
    ]);
  });

  it("says which move a place sends, and none for a place nothing reaches", () => {
    const held = standing(TURN, A_TURN, { zone: HAND, indices: [0] });

    expect(offerTo(held, { commit: "zone", zone: PILE })?.move).toEqual(aTake([0]));
    expect(offerTo(held, { commit: "seat", seat: 0 })).toBeNull();
  });

  it("holds a card no move names apart from the cards in play", () => {
    const bare = standing(TURN, A_TURN, null);

    expect(isOpen(bare, HAND, 3)).toBe(false);
    expect(picksIn(bare, HAND)).toBe(true);
    expect(picksIn(bare, PILE)).toBe(false);
  });
});

describe("a card a press stops at", () => {
  it("is the card no move names, in a zone some move picks in", () => {
    const bare = standing(TURN, A_TURN, null);

    expect(leadsNowhere(bare, HAND, 3)).toBe(true);
    expect(leadsNowhere(bare, HAND, 0)).toBe(false);
  });

  it("is no card of a zone no move picks in, since that zone poses no choice", () => {
    const bare = standing(TURN, A_TURN, null);

    expect(leadsNowhere(bare, PILE, 0)).toBe(false);
  });

  it("is no card of a table this seat owes no move to", () => {
    const resting = standing(TURN, DEALT, null);

    expect(leadsNowhere(resting, HAND, 0)).toBe(false);
    expect(leadsNowhere(resting, HAND, 3)).toBe(false);
  });

  it("is the card a move holding those in hand could not name beside them", () => {
    const held = standing(SETS, A_SET, { zone: HAND, indices: [0] });

    expect(leadsNowhere(held, HAND, 1)).toBe(false);
    expect(leadsNowhere(held, HAND, 3)).toBe(true);
  });

  it("is no card already in hand, which a press puts back down", () => {
    const held = standing(SETS, A_SET, { zone: HAND, indices: [0, 1] });

    expect(leadsNowhere(held, HAND, 0)).toBe(false);
    expect(leadsNowhere(held, HAND, 1)).toBe(false);
  });
});

describe("a selection of several cards", () => {
  it("holds open the cards a longer move could still name, and none of those in hand", () => {
    const held = standing(SETS, A_SET, { zone: HAND, indices: [0] });

    expect([...(held.open.get(HAND) ?? [])].sort()).toEqual([1, 2]);
    expect(held.armed).toHaveLength(0);
  });

  it("arms the move naming exactly the cards in hand while a longer one stays open", () => {
    const held = standing(SETS, A_SET, { zone: HAND, indices: [0, 1] });

    expect(held.armed.map((offer) => offer.indices)).toEqual([[0, 1]]);
    expect([...(held.open.get(HAND) ?? [])]).toEqual([2]);
  });

  it("arms the longest move once every card of it is in hand", () => {
    const held = standing(SETS, A_SET, { zone: HAND, indices: [0, 1, 2] });

    expect(held.armed.map((offer) => offer.indices)).toEqual([[0, 1, 2]]);
    expect(held.open.size).toBe(0);
  });

  it("holds a selection no move could grow out of, and holds nothing open for it", () => {
    const held = standing(SETS, A_SET, { zone: HAND, indices: [3] });

    expect(held.armed).toHaveLength(0);
    expect(held.open.size).toBe(0);
  });
});

describe("a move sent by its word", () => {
  it("is made in no zone and lands on no place", () => {
    const offers = offersOf(CHOICE, A_WORD_ALONE);

    expect(offers).toHaveLength(1);
    expect(offers[0]?.picked).toBeNull();
    expect(offers[0]?.indices).toEqual([]);
    expect(offers[0]?.target).toBeNull();
    expect(offers[0]?.caption).toBe(PASSING.caption);
  });

  it("stands ready while the hand is empty, and no place sends it", () => {
    const bare = standing(CHOICE, A_TURN_OR_A_WORD, null);

    expect(bare.said.map((offer) => offer.move)).toEqual([aPass()]);
    expect(bare.targets).toEqual([]);
    expect(offerTo(bare, { commit: "zone", zone: PILE })).toBeNull();
  });

  it("is put out of reach by the first card picked up, which arms the moves naming it", () => {
    const held = standing(CHOICE, A_TURN_OR_A_WORD, { zone: HAND, indices: [0] });

    expect(held.said).toEqual([]);
    expect(held.targets).toEqual([
      { commit: "zone", zone: PILE },
      { commit: "seat", seat: 2 },
    ]);
  });

  it("holds no card open, since it is about none", () => {
    const bare = standing(CHOICE, A_WORD_ALONE, null);

    expect(bare.open.size).toBe(0);
    expect(bare.said).toHaveLength(1);
  });

  it("leaves the cards of a turn it is the whole of reading as cards", () => {
    const bare = standing(CHOICE, A_WORD_ALONE, null);

    expect(picksIn(bare, HAND)).toBe(false);
    expect(leadsNowhere(bare, HAND, 0)).toBe(false);
    expect(pickedUp(bare, HAND, 0)).toBeNull();
  });
});

describe("clicking one card", () => {
  it("picks up a card a move names", () => {
    const bare = standing(TURN, A_TURN, null);

    expect(pickedUp(bare, HAND, 2)).toEqual({ zone: HAND, indices: [2] });
  });

  it("puts down a card already in hand, and puts the selection down with the last of them", () => {
    const held = standing(SETS, A_SET, { zone: HAND, indices: [0, 1] });

    expect(pickedUp(held, HAND, 0)).toEqual({ zone: HAND, indices: [1] });
    expect(pickedUp(standing(SETS, A_SET, { zone: HAND, indices: [1] }), HAND, 1)).toBeNull();
  });

  it("adds a card a longer move names, in the order a hand reads", () => {
    const held = standing(SETS, A_SET, { zone: HAND, indices: [2] });

    expect(pickedUp(held, HAND, 0)).toEqual({ zone: HAND, indices: [0, 2] });
  });

  it("starts afresh on a card no move names beside those in hand", () => {
    const held = standing(TURN, A_TURN, { zone: HAND, indices: [0] });

    expect(pickedUp(held, HAND, 2)).toEqual({ zone: HAND, indices: [2] });
  });

  it("puts the selection down where no move names the card at all", () => {
    const held = standing(TURN, A_TURN, { zone: HAND, indices: [0] });

    expect(pickedUp(held, HAND, 3)).toBeNull();
    expect(pickedUp(held, PILE, 0)).toBeNull();
  });

  it("reads back the cards in hand, and only in the zone they were picked in", () => {
    const held = standing(TURN, A_TURN, { zone: HAND, indices: [0] });

    expect(isSelected(held, HAND, 0)).toBe(true);
    expect(isSelected(held, HAND, 2)).toBe(false);
    expect(isSelected(held, PILE, 0)).toBe(false);
  });
});
