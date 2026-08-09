import { describe, expect, it } from "vitest";

import {
  commitOf,
  emptySeats,
  everyoneReady,
  hasSay,
  holderOf,
  holdingUpTheDeal,
  iAmHost,
  iAmReady,
  mayDeal,
  mine,
  mySeat,
  seatsOf,
  standingBy,
} from "../src/play/company";
import { aChoice, aGathering, aGuest, aSeatedGathering, MINE } from "./rooms";

describe("the places at a gathering", () => {
  it("stands one per seat of the table the company settled on", () => {
    const gathering = aGathering([], { choice: aChoice({ players: 4 }) });

    expect(seatsOf(gathering)).toEqual([0, 1, 2, 3]);
  });

  it("reads each place by the guest holding it, and as empty where nobody does", () => {
    const gathering = aGathering([aGuest("Grace", 1)]);

    expect(holderOf(gathering, 1)?.name).toBe("Grace");
    expect(holderOf(gathering, 0)).toBeNull();
  });

  it("counts the places nobody holds, which are the ones the deal waits on", () => {
    const gathering = aGathering([aGuest("Grace", 1)]);

    expect(emptySeats(gathering)).toEqual([0, 2]);
  });

  it("reads the guests holding no seat as the company standing by", () => {
    const gathering = aGathering([aGuest("Grace", 1), aGuest(MINE, null), aGuest("Alan", null)]);

    expect(standingBy(gathering).map((guest) => guest.name)).toEqual([MINE, "Alan"]);
  });
});

describe("the guest reading the page", () => {
  it("holds the seat the company reads them at", () => {
    const gathering = aGathering([aGuest(MINE, 2), aGuest("Grace", 0)]);

    expect(mySeat(gathering)).toBe(2);
    expect(mine(gathering, 2)).toBe(true);
    expect(mine(gathering, 0)).toBe(false);
  });

  it("holds no seat while they are standing by", () => {
    const gathering = aGathering([aGuest(MINE, null)]);

    expect(mySeat(gathering)).toBeNull();
  });

  it("holds no seat at a gathering they are absent from, which the company never read them at", () => {
    const gathering = aGathering([aGuest("Grace", 0)]);

    expect(mySeat(gathering)).toBeNull();
  });

  it("holds a say over what is played once they are sitting at the table", () => {
    expect(hasSay(aGathering([aGuest(MINE, 1)]))).toBe(true);
    expect(hasSay(aGathering([aGuest(MINE, null)]))).toBe(false);
  });
});

describe("what holds the deal up", () => {
  it("is the seat a guest standing by has yet to take", () => {
    const gathering = aGathering([aGuest(MINE, null)]);

    expect(holdingUpTheDeal(gathering)).toBe("Take a seat to deal");
  });

  it("is the one place still standing empty, named in the singular", () => {
    const gathering = aGathering([aGuest(MINE, 0), aGuest("Grace", 1)]);

    expect(holdingUpTheDeal(gathering)).toBe("One seat still to be taken");
  });

  it("is the count of places still standing empty where several are", () => {
    const gathering = aGathering([aGuest(MINE, 0)]);

    expect(holdingUpTheDeal(gathering)).toBe("2 seats still to be taken");
  });

  it("is the commitment a seated guest has yet to give once every place is taken", () => {
    const gathering = aSeatedGathering(3);

    expect(holdingUpTheDeal(gathering)).toBe("3 players still to ready");
  });

  it("is the one commitment still to be given, named in the singular", () => {
    const gathering = aGathering([
      aGuest(MINE, 0, true, "rose", false),
      aGuest("Grace", 1, true, "teal", true),
      aGuest("Alan", 2, true, "amber", true),
    ]);

    expect(holdingUpTheDeal(gathering)).toBe("One player still to ready");
  });

  it("is nothing at all once every place is taken and every seated guest has committed", () => {
    const gathering = aSeatedGathering(3, true);

    expect(holdingUpTheDeal(gathering)).toBeNull();
    expect(everyoneReady(gathering)).toBe(true);
  });

  it("counts nobody ready until every seat is taken, since an empty seat holds the deal up first", () => {
    const gathering = aGathering([aGuest(MINE, 0, true, "rose", true)]);

    expect(everyoneReady(gathering)).toBe(false);
    expect(holdingUpTheDeal(gathering)).toBe("2 seats still to be taken");
  });
});

describe("the say the guest reading the page holds", () => {
  it("reads whether they gathered the table and whether they have committed", () => {
    const gathering = aGathering([aGuest(MINE, 0, true, "rose", true, true)]);

    expect(iAmHost(gathering)).toBe(true);
    expect(iAmReady(gathering)).toBe(true);
  });

  it("gathers nothing and commits to nothing where the company reads nobody by their name", () => {
    const gathering = aGathering([aGuest("Grace", 0, true, "rose", true, true)]);

    expect(iAmHost(gathering)).toBe(false);
    expect(iAmReady(gathering)).toBe(false);
  });

  it("may deal a democratic table from any seat, and a host-governed one from the host's alone", () => {
    expect(mayDeal(aGathering([aGuest(MINE, 0)], { democratic: true }))).toBe(true);
    expect(mayDeal(aGathering([aGuest(MINE, 0, true, "rose", false, false)], { democratic: false }))).toBe(false);
    expect(mayDeal(aGathering([aGuest(MINE, 0, true, "rose", false, true)], { democratic: false }))).toBe(true);
  });
});

describe("the one press the room carries a seated guest through", () => {
  it("stands the guest up where they hold no seat, since a player is who commits and deals", () => {
    expect(commitOf(aGathering([aGuest(MINE, null)]))).toEqual({ act: "stand" });
  });

  it("asks a seated guest to commit while a seat is still to be taken", () => {
    expect(commitOf(aGathering([aGuest(MINE, 0)]))).toEqual({
      act: "ready",
      ready: false,
      pending: "2 seats still to be taken",
    });
  });

  it("reads the guest's own commitment back once it is given, so the press takes it back", () => {
    const gathering = aGathering([
      aGuest(MINE, 0, true, "rose", true),
      aGuest("Grace", 1, true, "teal", false),
      aGuest("Alan", 2, true, "amber", true),
    ]);

    expect(commitOf(gathering)).toEqual({ act: "ready", ready: true, pending: "One player still to ready" });
  });

  it("becomes the deal itself once every seat is taken and every seated guest has committed", () => {
    expect(commitOf(aSeatedGathering(3, true))).toEqual({ act: "deal" });
  });

  it("becomes the deal for the host of a host-governed table the company has committed to", () => {
    const gathering = aGathering(
      [
        aGuest(MINE, 0, true, "rose", true, true),
        aGuest("Grace", 1, true, "teal", true),
        aGuest("Alan", 2, true, "amber", true),
      ],
      { democratic: false },
    );

    expect(commitOf(gathering)).toEqual({ act: "deal" });
  });

  it("waits on the host where a host-governed table keeps the deal to them", () => {
    const gathering = aGathering(
      [
        aGuest(MINE, 0, true, "rose", true, false),
        aGuest("Grace", 1, true, "teal", true, true),
        aGuest("Alan", 2, true, "amber", true),
      ],
      { democratic: false },
    );

    expect(commitOf(gathering)).toEqual({ act: "wait" });
  });
});
