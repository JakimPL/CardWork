import { describe, expect, it } from "vitest";

import {
  dealReading,
  dealReady,
  emptySeats,
  hasSay,
  holderOf,
  holdingUpTheDeal,
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
    expect(dealReady(gathering)).toBe(false);
  });

  it("is the one place still standing empty, named in the singular", () => {
    const gathering = aGathering([aGuest(MINE, 0), aGuest("Grace", 1)]);

    expect(holdingUpTheDeal(gathering)).toBe("One seat still to be taken");
  });

  it("is the count of places still standing empty where several are", () => {
    const gathering = aGathering([aGuest(MINE, 0)]);

    expect(holdingUpTheDeal(gathering)).toBe("2 seats still to be taken");
  });

  it("is nothing at all once a seated guest reads every place taken", () => {
    const gathering = aSeatedGathering(3);

    expect(holdingUpTheDeal(gathering)).toBeNull();
    expect(dealReady(gathering)).toBe(true);
    expect(dealReading(gathering)).toBe("Deal the cards");
  });

  it("is what the button calling for the deal reads while something does", () => {
    const gathering = aGathering([aGuest(MINE, 0)]);

    expect(dealReading(gathering)).toBe(holdingUpTheDeal(gathering));
  });
});
