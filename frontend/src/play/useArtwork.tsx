import { createContext, type ReactElement, type ReactNode, useContext, useEffect, useState } from "react";

import type { Artwork } from "../api/artwork";
import { readArtwork } from "../api/artwork";

/** What a page draws with until a table has stated a pack, and what a table drawing no pack draws with. */
const GLYPHS = null;

/**
 * The pack every card of the page is drawn from, held for the whole page rather than by a seat or a zone.
 *
 * A test states the pack a card is read against outright, which is what leaves the reading of a drawing apart
 * from the serving of one.
 */
export const Drawn = createContext<Artwork | null>(GLYPHS);

interface DrawingProps {
  children: ReactNode;
}

/**
 * The page under the pack its table serves, read once as the page opens.
 *
 * A table states which cards it is drawn with as it answers for its artwork, and a page that has yet to read
 * that draws the glyphs it carries: the table is legible from the first frame and takes the artwork on as it
 * arrives. A pack is one thing for a whole page, so it is read here and by every card where it is drawn.
 */
export function Drawing({ children }: DrawingProps): ReactElement {
  const [artwork, setArtwork] = useState<Artwork | null>(GLYPHS);

  useEffect(() => {
    const drawing = { held: true };
    const draw = (pack: Artwork | null): void => {
      if (drawing.held) {
        setArtwork(pack);
      }
    };

    readArtwork()
      .then(draw)
      .catch(() => {
        draw(GLYPHS);
      });

    return () => {
      drawing.held = false;
    };
  }, []);

  return <Drawn value={artwork}>{children}</Drawn>;
}

/** The pack one card is drawn from, which a page told of none draws the glyphs it carries for. */
export function useArtwork(): Artwork | null {
  return useContext(Drawn);
}
