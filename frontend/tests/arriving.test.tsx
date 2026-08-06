import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Arrival } from "../src/play/arriving";
import { arrivalIn } from "../src/play/arriving";
import { Arriving } from "../src/table/Arriving";
import { CODE, TABLE } from "./rooms";

/** Another table gathering here, which is what makes the tables offered a choice rather than the one answer. */
const ANOTHER = "back-room";

/** The tables a host answers where the read went nowhere, which leaves a table to be named by hand. */
const NONE_GATHERING: string[] = [];

interface Standing {
  table: string | null;
  code: string | null;
  tables: string[] | null;
}

/** The arrival as it stands for a tab handed the whole announced address, which is the usual way in. */
const ANNOUNCED: Standing = { table: TABLE, code: CODE, tables: null };

/** The arrival as it stands for a tab opened at the bare address, which knows no table until the host says. */
const BARE: Standing = { table: null, code: null, tables: null };

function drawn(standing: Standing): string {
  return renderToStaticMarkup(<Arriving table={standing.table} code={standing.code} tables={standing.tables} />);
}

describe("the page a guest arrives at a table from", () => {
  it("names the table the address carried", () => {
    expect(drawn(ANNOUNCED)).toContain(TABLE);
  });

  it("offers the code the address carried, so a guest handed a line names only themselves", () => {
    expect(drawn(ANNOUNCED)).toContain(`value="${CODE}"`);
  });

  it("reads the code out beside it, which is the form one person passes to another", () => {
    expect(drawn(ANNOUNCED)).toContain("K Q A J 7 2");
  });

  it("stands the code empty for a tab that reached the table another way", () => {
    const page = drawn({ ...ANNOUNCED, code: null });

    expect(page).toContain("a hand of six ranks");
    expect(page).not.toContain(CODE);
  });

  it("reads out nothing for a code that reads as no hand of ranks", () => {
    expect(drawn({ ...ANNOUNCED, code: "hello" })).not.toContain('class="reading"');
  });

  it("holds the arrival back until a table, a code and a name all stand there", () => {
    expect(drawn({ ...ANNOUNCED, code: null })).toContain('disabled=""');
  });

  it("offers a way back to another table where the address named one", () => {
    expect(drawn(ANNOUNCED)).toContain("Name another table");
  });
});

describe("the table a guest arriving from the bare address joins", () => {
  it("offers the tables gathering here, so nobody who was handed no address guesses at a name", () => {
    const page = drawn({ ...BARE, tables: [TABLE, ANOTHER] });

    expect(page).toContain("<select");
    expect(page).toContain(`<option value="${TABLE}"`);
    expect(page).toContain(`<option value="${ANOTHER}"`);
  });

  it("stands at the first table gathering, which is the whole of the choice where a host holds one", () => {
    const page = drawn({ ...BARE, tables: [TABLE] });

    expect(page).toContain(`<option value="${TABLE}" selected=""`);
  });

  it("leaves the table to be named where the host answers none", () => {
    const page = drawn({ ...BARE, tables: NONE_GATHERING });

    expect(page).toContain('placeholder="green-baize"');
    expect(page).not.toContain("<select");
  });

  it("leaves the table to be named where the host was not read at all", () => {
    expect(drawn(BARE)).toContain('placeholder="green-baize"');
  });

  it("offers no way back, since a table named here is the way back", () => {
    expect(drawn(BARE)).not.toContain("Name another table");
  });
});

interface ArrivalCase {
  description: string;
  stated: Arrival;
  arrival: Arrival | null;
}

const WHOLE: Arrival = { table: TABLE, code: CODE, name: "Ada" };

const CASES: ArrivalCase[] = [
  {
    description: "a table, a whole code and a name, which is everything the lobby is told",
    stated: WHOLE,
    arrival: WHOLE,
  },
  {
    description: "a code written the way one person passes it to another, which reads as the same hand",
    stated: { ...WHOLE, code: "kq-aj 72" },
    arrival: WHOLE,
  },
  {
    description: "a table and a name typed with spaces around them, which the table is told without",
    stated: { ...WHOLE, table: ` ${TABLE} `, name: " Ada " },
    arrival: WHOLE,
  },
  {
    description: "no table, which names nowhere to arrive at",
    stated: { ...WHOLE, table: "  " },
    arrival: null,
  },
  {
    description: "no name, which the company would read nobody by",
    stated: { ...WHOLE, name: "" },
    arrival: null,
  },
  {
    description: "a code short of a whole hand of ranks",
    stated: { ...WHOLE, code: "KQA" },
    arrival: null,
  },
  {
    description: "a code that reads as no hand of ranks at all",
    stated: { ...WHOLE, code: "hello!" },
    arrival: null,
  },
];

describe("the arrival what a guest stated stands as", () => {
  it.each(CASES)("$description", ({ stated, arrival }) => {
    expect(arrivalIn(stated)).toEqual(arrival);
  });
});
