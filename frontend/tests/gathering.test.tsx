import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Choice, GatheringView } from "../src/api/gathering";
import { Gathering } from "../src/table/Gathering";
import { aChoice, aGathering, aGuest, aSeatedGathering, CODE, MINE, OFFERINGS, TABLE } from "./rooms";

/** A press that does nothing, since what these read is the drawing of a room rather than what follows one. */
const IDLE = (): void => undefined;

/** The options one control of the room lists, read out of the label it stands under. */
function optionsOf(room: string, label: string): string[] {
  const control = new RegExp(`${label}<select[^>]*>(.*?)</select>`).exec(room);
  return [...(control?.[1] ?? "").matchAll(/<option[^>]*>([^<]*)<\/option>/g)].map((option) => option[1] ?? "");
}

function drawn(gathering: GatheringView): string {
  return renderToStaticMarkup(
    <Gathering
      gathering={gathering}
      offerings={OFFERINGS}
      connection="following"
      trouble={null}
      claim={IDLE}
      settle={IDLE}
      callTheDeal={IDLE}
    />,
  );
}

describe("the room a table gathers in", () => {
  it("names the table and the guest reading it", () => {
    const room = drawn(aGathering([aGuest(MINE, null)]));

    expect(room).toContain(TABLE);
    expect(room).toContain(MINE);
  });

  it("reads the code out, so a guest already at the table can pass it to the next one", () => {
    const room = drawn(aGathering([aGuest(MINE, null)]));

    expect(room).toContain("K Q A J 7 2");
    expect(room).not.toContain(CODE);
  });

  it("stands one place per seat of the table the company settled on", () => {
    const room = drawn(aGathering([], { choice: aChoice({ players: 4 }) }));

    expect([...room.matchAll(/class="place /g)]).toHaveLength(4);
  });

  it("reads each place by the guest holding it, and as empty where nobody does", () => {
    const room = drawn(aGathering([aGuest("Grace", 1)]));

    expect(room).toContain("Grace");
    expect([...room.matchAll(/>empty</g)]).toHaveLength(2);
  });

  it("marks the place the guest reading it holds, which is the one they may stand up from", () => {
    const room = drawn(aGathering([aGuest(MINE, 1)]));

    expect([...room.matchAll(/class="place taken own"/g)]).toHaveLength(1);
    expect(room).toContain("Stand up");
    expect([...room.matchAll(/>Sit here</g)]).toHaveLength(2);
  });

  it("marks a guest whose page is closed as away, and one holding it open as present", () => {
    const room = drawn(aGathering([aGuest("Grace", 0), aGuest("Alan", 1, false)]));

    expect([...room.matchAll(/class="guest present"/g)]).toHaveLength(1);
    expect([...room.matchAll(/class="guest away"/g)]).toHaveLength(1);
  });

  it("names the guests standing by, which is everyone watching the room", () => {
    const room = drawn(aGathering([aGuest("Grace", 0), aGuest(MINE, null)]));

    expect(room).toContain("Standing by:");
    expect(room).toContain(MINE);
  });

  it("names nobody standing by at a gathering where every guest is sitting", () => {
    expect(drawn(aSeatedGathering(3))).not.toContain("Standing by");
  });
});

describe("what the room offers to play", () => {
  it("lists every game the host holds the rules of, by the title each of them reads under", () => {
    const room = drawn(aSeatedGathering(3));

    for (const offering of OFFERINGS) {
      expect(room).toContain(offering.title);
    }
  });

  it("lists the tables the game settled on seats, and none it does not", () => {
    const room = drawn(aGathering([aGuest(MINE, 0)], { choice: aChoice({ game: "climbing", players: 2 }) }));

    expect(optionsOf(room, "Players")).toEqual(["2", "3", "4", "5"]);
  });

  it("offers the counts of decks a game is dealt from where it admits more than one", () => {
    const room = drawn(aGathering([aGuest(MINE, 0)], { choice: aChoice({ game: "passing" }) }));

    expect(room).toContain("Decks");
  });

  it("offers no choice of decks for a game dealt from one count of them", () => {
    const room = drawn(aGathering([aGuest(MINE, 0)], { choice: aChoice({ game: "climbing" }) }));

    expect(room).not.toContain("Decks");
  });

  it("reads out how long the match runs", () => {
    const room = drawn(aGathering([aGuest(MINE, 0)]));

    expect(room).toContain("Runs to 3 rounds");
  });

  it("leaves every control to the guests sitting at the table", () => {
    const room = drawn(aGathering([aGuest(MINE, null)]));

    expect(room).toContain("Take a seat to settle what is played");
    expect([...room.matchAll(/<select disabled=""/g)].length).toBeGreaterThan(0);
  });
});

describe("the press that deals the table", () => {
  it("stands ready once a seated guest reads every place taken", () => {
    const room = drawn(aSeatedGathering(3));

    expect(room).toContain("Deal the cards");
    expect(room).not.toContain('<button type="button" disabled="">Deal');
  });

  it("says what holds it up while something does", () => {
    const room = drawn(aGathering([aGuest(MINE, 0)]));

    expect(room).toContain("2 seats still to be taken");
  });
});

describe("a choice the host offers nowhere", () => {
  it("leaves the table it was settled at readable, since the room draws what the gathering says", () => {
    const unheld: Choice = aChoice({ game: "bridge", players: 4 });
    const room = drawn(aGathering([aGuest(MINE, 0)], { choice: unheld }));

    expect(optionsOf(room, "Players")).toEqual(["4"]);
    expect(room).not.toContain("Decks");
  });
});
