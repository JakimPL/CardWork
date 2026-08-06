import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { Arriving } from "../src/table/Arriving";
import { CODE, TABLE } from "./rooms";

function drawn(code: string | null): string {
  return renderToStaticMarkup(<Arriving table={TABLE} code={code} />);
}

describe("the page a guest arrives at a table from", () => {
  it("names the table they are arriving at", () => {
    expect(drawn(CODE)).toContain(TABLE);
  });

  it("offers the code the address carried, so a guest handed a line names only themselves", () => {
    expect(drawn(CODE)).toContain(`value="${CODE}"`);
  });

  it("reads the code out beside it, which is the form one person passes to another", () => {
    expect(drawn(CODE)).toContain("K Q A J 7 2");
  });

  it("stands the code empty for a tab that reached the table another way", () => {
    const page = drawn(null);

    expect(page).toContain("a hand of six ranks");
    expect(page).not.toContain(CODE);
  });

  it("reads out nothing for a code that reads as no hand of ranks", () => {
    expect(drawn("hello")).not.toContain('class="reading"');
  });

  it("holds the arrival back until a name and a code have both been offered", () => {
    expect(drawn(null)).toContain('disabled=""');
  });
});
