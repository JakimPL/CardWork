import { describe, expect, it } from "vitest";

import { advanced, applyCommit, reachedBy } from "../src/play/commits";
import { aCommit, aView, card, HAND, PILE, SEATED, sortable, STACK } from "./tables";

describe("a commit applied to the view a client holds", () => {
  it("stands the client one commit further on than the number the commit took", () => {
    const held = aView({ [HAND]: [card("9", "♦")] }, 4);

    expect(applyCommit(held, aCommit(4, [])).seq).toBe(5);
  });

  it("leaves every zone it read the same way as it stood", () => {
    const held = aView({ [HAND]: [card("9", "♦")], [STACK]: [] }, 4);

    const after = applyCommit(held, aCommit(4, [{ zone: STACK, before: [], after: [card("8", "♠")] }]));

    expect(after.zones[HAND]).toEqual(held.zones[HAND]);
    expect(after.zones[STACK]?.cards).toEqual([card("8", "♠")]);
  });

  it("takes the cursor and the moves it carries in place of the ones held", () => {
    const held = aView({ [HAND]: [] }, 4);
    const settled = { ...SEATED, phase: "decided", to_act: [], winner: 1 };

    const after = applyCommit(held, aCommit(4, [], settled));

    expect(after.state).toEqual(settled);
    expect(after.observer).toBe(held.observer);
  });

  it("holds a zone the client had not seen where a change names one, as a zone it may not lay out", () => {
    const held = aView({ [HAND]: [] }, 4);

    const after = applyCommit(held, aCommit(4, [{ zone: PILE, before: [], after: [null, null] }]));

    expect(after.zones[PILE]).toEqual({ id: PILE, owner: null, arrangeable: false, cards: [null, null] });
  });

  it("lays a hand out in the order the seat laid down, and leaves that order the seat's own to set again", () => {
    const run = [card("J", "♠"), card("7", "♥"), card("10", "♦")];
    const held = sortable(aView({ [HAND]: run }, 1), HAND);
    const laid = [card("7", "♥"), card("10", "♦"), card("J", "♠")];

    const after = applyCommit(held, aCommit(1, [{ zone: HAND, before: run, after: laid }]));

    expect(after.zones[HAND]?.cards).toEqual(laid);
    expect(after.zones[HAND]?.arrangeable).toBe(true);
  });

  it("reads the same either way round, so a commit met twice changes nothing the second time", () => {
    const held = aView({ [HAND]: [card("9", "♦")] }, 4);
    const commit = aCommit(4, [{ zone: HAND, before: [card("9", "♦")], after: [card("2", "♣")] }]);

    expect(applyCommit(applyCommit(held, commit), commit)).toEqual(applyCommit(held, commit));
  });
});

describe("a commit off the stream", () => {
  it("is taken up where it is the one the client stands waiting for", () => {
    const held = aView({ [HAND]: [card("9", "♦")] }, 4);

    expect(advanced(held, aCommit(4, [])).seq).toBe(5);
  });

  it("leaves a position read afresh where it stands, since the commit is already in hand", () => {
    const read = aView({ [HAND]: [card("2", "♣")] }, 6);

    const after = advanced(read, aCommit(4, [{ zone: HAND, before: [], after: [card("9", "♦")] }]));

    expect(after).toBe(read);
  });

  it("says which commit a client asks for next, which is what a stream opened afresh picks up at", () => {
    expect(reachedBy(aCommit(4, []))).toBe(5);
  });
});
