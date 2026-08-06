import type { Artwork } from "../api/artwork";
import { pictureOf } from "../api/artwork";
import type { CardOrJoker, ProjectedCard } from "../api/views";

/** How a pack spells the ranks whose face is a word, where the ranks that count for themselves stand as they read. */
const SPELLED_RANKS: Record<string, string> = { A: "ace", J: "jack", Q: "queen", K: "king" };

/** How a pack spells each suit, read off the glyph a card carries as `cardwork.cards.Suit` states it. */
const SPELLED_SUITS: Record<string, string> = { "♠": "spades", "♥": "hearts", "♦": "diamonds", "♣": "clubs" };

/** The names the two jokers are written under, which is the colour each of them was dealt in. */
const RED_JOKER = "red_joker";
const BLACK_JOKER = "black_joker";

/** The word a card back is written under, ahead of the design it draws. */
const BACK = "back";

/**
 * Where the pack in service draws one place of a zone: the card standing there, or the back it lies under.
 *
 * Every pack writes the same names, so this one mapping reaches whichever of them a table was opened with and
 * the size and the extension the pictures were written at come from the pack itself. It mirrors the names
 * `scripts.assets.packs` writes a pack under, which is the whole of what the build and the page agree on.
 */
export function drawnAt(artwork: Artwork, card: ProjectedCard): string {
  return pictureOf(artwork, card === null ? backing(artwork.back) : naming(card.card));
}

/** The name one card is written under, which is the rank and the suit as a pack spells them. */
function naming(card: CardOrJoker): string {
  if ("rank" in card) {
    return `${SPELLED_RANKS[card.rank] ?? card.rank}_of_${SPELLED_SUITS[card.suit] ?? card.suit}`;
  }

  return card.red ? RED_JOKER : BLACK_JOKER;
}

/** The name one card back is written under, which is the design it draws. */
function backing(design: string): string {
  return `${BACK}_${design}`;
}
