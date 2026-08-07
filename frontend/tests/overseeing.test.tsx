import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { Overseeing } from "../src/table/Overseeing";

describe("the overseer's panel before the lobby has answered", () => {
  it("names itself and reads as reading the lobby, since the panel holds no table of its own", () => {
    const panel = renderToStaticMarkup(<Overseeing admin="oversee-999" />);

    expect(panel).toContain("Overseeing the lobby");
    expect(panel).toContain("Reading the lobby");
  });
});
