import { bodyOf } from "./parsing";

/** Where a table serves the pack it draws with, which mirrors `cardtable.artwork.ARTWORK`. */
const ARTWORK = "/artwork";

/** The name a pack states itself under, which mirrors `cardtable.artwork.MANIFEST`. */
const MANIFEST = "manifest.json";

/**
 * The pack one table draws with, stated by hand as a mirror of `cardtable.artwork.ServedPack`.
 *
 * The pictures are files a table serves rather than an answer it composes, so this shape stands beside the
 * projections in `views.ts` instead of arriving with the generated schema. Every card of a pack is named for
 * the rank and the suit it draws, so what a page is told besides is the size a card was written at, how the
 * artwork takes to being drawn at another size, whether it carries its own edge, which backs landed with it,
 * and the one this table lies its face-down cards under.
 */
export interface Artwork {
  pack: string;
  extension: string;
  width: number;
  height: number;
  pixelated: boolean;
  cornered: boolean;
  backs: string[];
  back: string;
}

/**
 * The pack this table draws with, read once as the page opens.
 *
 * A table states a pack where one was fetched and configured for it, and answers otherwise with nothing at
 * all, which is what a page drawing the glyphs it carries reads.
 */
export async function readArtwork(): Promise<Artwork | null> {
  const response = await fetch(`${ARTWORK}/${MANIFEST}`);
  return response.ok ? bodyOf<Artwork>(response) : null;
}

/** The address one picture of the pack in service stands at, which is the name it was written under. */
export function pictureOf(artwork: Artwork, drawn: string): string {
  return `${ARTWORK}/${drawn}.${artwork.extension}`;
}
