import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { Artwork } from "../src/api/artwork";
import type { ProjectedCard } from "../src/api/views";
import { Drawn } from "../src/play/useArtwork";
import { drawnAt } from "../src/table/artwork";
import { CardFace } from "../src/table/CardFace";
import { shaping } from "../src/table/sizing";
import { card } from "./tables";

/** The Kare pack as it lands on disk, which is pixel artwork upscaled whole and cut to its own corners. */
const KARE: Artwork = {
  pack: "kare",
  extension: "png",
  width: 284,
  height: 384,
  pixelated: true,
  cornered: true,
  backs: ["crosshatch", "castle"],
  back: "crosshatch",
};

/** The drawn pack, which is a card per file at a shape of its own and takes to any size it is drawn at. */
const SVG: Artwork = {
  pack: "svg",
  extension: "svg",
  width: 167,
  height: 243,
  pixelated: false,
  cornered: true,
  backs: ["atlas"],
  back: "atlas",
};

/** The card standing for any other, which the pack draws in the colour it was dealt in. */
const joker = (red: boolean): ProjectedCard => ({ card: { red }, face_down: false });

/** One place of a zone as a page holding that pack draws it. */
const drawn = (place: ProjectedCard, artwork: Artwork | null): string =>
  renderToStaticMarkup(
    <Drawn value={artwork}>
      <CardFace card={place} selected={false} dimmed={false} arriving={false} onPick={null} />
    </Drawn>,
  );

describe("the picture a pack holds for one card", () => {
  it("names a court card by the word its rank is spelled with", () => {
    expect(drawnAt(KARE, card("Q", "♥"))).toBe("/artwork/queen_of_hearts.png");
    expect(drawnAt(KARE, card("A", "♠"))).toBe("/artwork/ace_of_spades.png");
  });

  it("names a card that counts for itself by the figure it reads as", () => {
    expect(drawnAt(KARE, card("10", "♦"))).toBe("/artwork/10_of_diamonds.png");
    expect(drawnAt(KARE, card("2", "♣"))).toBe("/artwork/2_of_clubs.png");
  });

  it("names each joker by the colour it was dealt in", () => {
    expect(drawnAt(KARE, joker(true))).toBe("/artwork/red_joker.png");
    expect(drawnAt(KARE, joker(false))).toBe("/artwork/black_joker.png");
  });

  it("draws a card nobody at this seat reads as the back this table lies them under", () => {
    expect(drawnAt(KARE, null)).toBe("/artwork/back_crosshatch.png");
    expect(drawnAt(SVG, null)).toBe("/artwork/back_atlas.svg");
  });

  it("reads every picture in the kind of file the pack was written in", () => {
    expect(drawnAt(SVG, card("K", "♣"))).toBe("/artwork/king_of_clubs.svg");
  });
});

describe("a card drawn from a pack", () => {
  it("stands the picture of the card where the page draws marks of its own", () => {
    const place = drawn(card("9", "♦"), KARE);

    expect(place).toContain('<img class="art" src="/artwork/9_of_diamonds.png" alt=""/>');
    expect(place).not.toContain('class="index"');
  });

  it("draws a card nobody reads as the back the table serves", () => {
    const place = drawn(null, KARE);

    expect(place).toContain('src="/artwork/back_crosshatch.png"');
    expect(place).toContain('class="card back drawn');
  });

  it("says the pixel artwork is drawn square and carries its own corners", () => {
    expect(drawn(card("9", "♦"), KARE)).toContain('class="card face red drawn pixelated cornered"');
  });

  it("draws a pack written to be read at any size as the sheet reads any picture", () => {
    const place = drawn(card("9", "♦"), SVG);

    expect(place).toContain('class="card face red drawn cornered"');
    expect(place).toContain('src="/artwork/9_of_diamonds.svg"');
  });

  it("names the card in the words a reader reaching the page by them is told it by", () => {
    expect(drawn(card("9", "♦"), KARE)).toContain('aria-label="9♦"');
    expect(drawn(null, KARE)).toContain('aria-label="a card nobody at this seat reads"');
  });

  it("keeps the marks a table is read by, whichever way the face of a card is arrived at", () => {
    expect(drawn(card("9", "♦", true), KARE)).toContain("concealed");
  });
});

describe("a table serving no pack", () => {
  it("draws every card from the glyphs the page carries", () => {
    const place = drawn(card("9", "♦"), null);

    expect(place).toContain('class="card face red"');
    expect(place).toContain(">9</span>");
    expect(place).not.toContain("<img");
  });

  it("draws a card nobody reads as the back the sheet paints", () => {
    expect(drawn(null, null)).toBe('<div class="card back" aria-label="a card nobody at this seat reads"></div>');
  });
});

describe("the shape every card of a page is drawn to", () => {
  it("is the size the pack in service was written at", () => {
    expect(shaping(KARE)).toStrictEqual({ "--card-aspect-width": 284, "--card-aspect-height": 384 });
    expect(shaping(SVG)).toStrictEqual({ "--card-aspect-width": 167, "--card-aspect-height": 243 });
  });

  it("is the sheet's own where the page draws the glyphs it carries", () => {
    expect(shaping(null)).toStrictEqual({});
  });
});
