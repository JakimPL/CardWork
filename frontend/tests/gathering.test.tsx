import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Choice, GatheringView, Tint } from "../src/api/gathering";
import { TINTS } from "../src/play/tints";
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
      tint={IDLE}
      settle={IDLE}
      ready={IDLE}
      govern={IDLE}
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

/** The tints two guests of these tests play under, which are two the company holds apart. */
const HERS: Tint = "teal";
const HIS: Tint = "amber";

describe("the colours the company is told apart by", () => {
  it("reads each place under the tint the guest holding it plays in", () => {
    const room = drawn(aGathering([aGuest("Grace", 1, true, HIS)]));

    expect(room).toContain(`class="place taken" data-tint="${HIS}"`);
    expect([...room.matchAll(/class="place empty"[^>]*data-tint/g)]).toHaveLength(0);
  });

  it("offers a swatch for every tint the room hands out", () => {
    const room = drawn(aGathering([aGuest(MINE, null, true, HERS)]));

    expect([...room.matchAll(/class="swatch/g)]).toHaveLength(TINTS.length);
  });

  it("marks the one the guest reading the room holds, which is the one they are drawn in", () => {
    const room = drawn(aGathering([aGuest(MINE, null, true, HERS)]));

    expect(room).toContain(`class="swatch own" data-tint="${HERS}" title="${HERS}, yours"`);
  });

  it("leaves a tint another guest holds to them, and says whose it is", () => {
    const room = drawn(aGathering([aGuest(MINE, null, true, HERS), aGuest("Grace", 0, true, HIS)]));

    expect(room).toContain(`data-tint="${HIS}" title="${HIS}, held by Grace"`);
    expect([...room.matchAll(/class="swatch"[^>]*disabled=""/g)]).toHaveLength(1);
  });

  it("offers the tints nobody holds, since a guest takes one of those by pressing it", () => {
    const room = drawn(aGathering([aGuest(MINE, null, true, HERS)]));

    expect([...room.matchAll(/title="[a-z]+, free to take"/g)]).toHaveLength(TINTS.length - 1);
    expect([...room.matchAll(/class="swatch"[^>]*disabled=""/g)]).toHaveLength(0);
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

describe("the move hints the table may put out", () => {
  it("offers a seated guest the toggle, lit where the choice settled the hints on", () => {
    const room = drawn(aGathering([aGuest(MINE, 0)], { choice: aChoice({ cues: true }) }));

    expect(room).toContain("Light the cards a seat may play");
    expect(room).toMatch(/class="cues"><input type="checkbox" checked=""/);
  });

  it("reads the toggle out unlit where the choice turned the hints off", () => {
    const room = drawn(aGathering([aGuest(MINE, 0)], { choice: aChoice({ cues: false }) }));

    expect(room).toMatch(/class="cues"><input type="checkbox"\/>/);
  });

  it("leaves the toggle to the guests holding a seat, so a guest standing by reads it fixed", () => {
    const room = drawn(aGathering([aGuest(MINE, null)]));

    expect(room).toMatch(/class="cues"><input type="checkbox"[^>]*disabled=""/);
  });
});

describe("the one press the room carries a seated guest through", () => {
  it("asks a seated guest to commit, and says what the table still waits on", () => {
    const room = drawn(aGathering([aGuest(MINE, 0)]));

    expect(room).toContain(">Ready</button>");
    expect(room).toContain("2 seats still to be taken");
    expect(room).not.toContain("Deal the cards");
  });

  it("reads the guest's own commitment back once it is given, so the press takes it back", () => {
    const room = drawn(aGathering([aGuest(MINE, 0, true, "rose", true)], { choice: aChoice({ players: 2 }) }));

    expect(room).toContain('aria-pressed="true"');
    expect(room).toContain("Ready ✓");
    expect(room).toContain("One seat still to be taken");
  });

  it("becomes the deal itself once every seat is taken and every seated guest has committed", () => {
    const room = drawn(aSeatedGathering(3, true));

    expect(room).toContain("Deal the cards");
    expect(room).not.toContain(">Ready</button>");
  });

  it("waits on the host where a host-governed table keeps the deal to them", () => {
    const company = [
      aGuest(MINE, 0, true, "rose", true, false),
      aGuest("Grace", 1, true, "teal", true, true),
      aGuest("Alan", 2, true, "amber", true, false),
    ];
    const room = drawn(aGathering(company, { democratic: false }));

    expect(room).toContain("Waiting for the host to deal");
    expect(room).not.toContain("Deal the cards");
  });

  it("stands a guest holding no seat up, since a player is who commits and deals", () => {
    const room = drawn(aGathering([aGuest(MINE, null)]));

    expect(room).toContain("Take a seat to deal");
  });
});

describe("the commitment the company reads of one another", () => {
  it("marks each seated guest ready or not, so the company reads who is waiting on whom", () => {
    const company = [aGuest(MINE, 0, true, "rose", true), aGuest("Grace", 1, true, "teal", false)];
    const room = drawn(aGathering(company, { choice: aChoice({ players: 2 }) }));

    expect([...room.matchAll(/class="standing ready">Ready</g)]).toHaveLength(1);
    expect([...room.matchAll(/class="standing unready">Not ready</g)]).toHaveLength(1);
  });

  it("names the guest who gathered the table, whose say governs it host by host", () => {
    const room = drawn(aGathering([aGuest("Grace", 0, true, "teal", true, true)], { choice: aChoice({ players: 1 }) }));

    expect(room).toContain('class="badge host">host</span>');
  });
});

describe("the say over how the table is governed", () => {
  it("offers the host the toggle that hands the say to the table or keeps it to themselves", () => {
    const room = drawn(aGathering([aGuest(MINE, 0, true, "rose", false, true)], { choice: aChoice({ players: 1 }) }));

    expect(room).toContain("Everyone at the table may change the settings");
    expect(room).toContain('type="checkbox"');
  });

  it("shows a seated guest who is not the host no such toggle", () => {
    const room = drawn(aGathering([aGuest(MINE, 0, true, "rose", false, false)], { choice: aChoice({ players: 1 }) }));

    expect(room).not.toContain("Everyone at the table may change the settings");
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
