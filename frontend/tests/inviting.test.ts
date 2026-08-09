import { describe, expect, it } from "vitest";

import { invitationTo } from "../src/play/joining";
import { CODE, TABLE } from "./rooms";

describe("the line a guest at the table passes on", () => {
  it("names the table and the code it gathers on, both of them in the fragment", () => {
    const line = invitationTo(TABLE, CODE, new URL("http://127.0.0.1:8421/"));

    expect(line).toBe(`http://127.0.0.1:8421/#table=${TABLE}&code=${CODE}`);
  });

  it("carries neither of them in the path, which is the half of an address a server logs", () => {
    const line = invitationTo(TABLE, CODE, new URL("http://127.0.0.1:8421/"));
    const [address] = line.split("#");

    expect(address).not.toContain(CODE);
    expect(address).not.toContain(TABLE);
  });

  it("follows the address the page itself was reached at, so a table read over a home network hands out one that reaches it", () => {
    const line = invitationTo(TABLE, CODE, new URL("http://192.168.1.5:8421/"));

    expect(line).toBe(`http://192.168.1.5:8421/#table=${TABLE}&code=${CODE}`);
  });

  it("keeps whatever path the page stands at, since the interface answers where it is mounted", () => {
    const line = invitationTo(TABLE, CODE, new URL("https://cards.jakim.it/play/"));

    expect(line).toBe(`https://cards.jakim.it/play/#table=${TABLE}&code=${CODE}`);
  });
});
