import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { Closed } from "../src/table/Closed";

describe("how a tab reads once the table it followed was broken up", () => {
  it("names the table closed and offers the way on to another", () => {
    const screen = renderToStaticMarkup(<Closed table="green-baize" reason={null} />);

    expect(screen).toContain("green-baize");
    expect(screen).toContain("was closed");
    expect(screen).toContain("Name another table");
  });

  it("reads out the word the close left behind where it carried one", () => {
    const screen = renderToStaticMarkup(<Closed table="green-baize" reason="The host stepped away" />);

    expect(screen).toContain("The host stepped away");
    expect(screen).toContain('class="reason"');
  });

  it("leaves no line for a reason where the close carried none", () => {
    const screen = renderToStaticMarkup(<Closed table="green-baize" reason={null} />);

    expect(screen).not.toContain('class="reason"');
  });
});
