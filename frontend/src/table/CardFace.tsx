import type { ReactElement } from "react";

import type { CardOrJoker, ProjectedCard } from "../api/views";
import { classes } from "./classes";

/**
 * The suits that draw in red, whose values are the glyphs themselves as `cardwork.cards.suit` states them.
 *
 * A card arrives carrying its own glyph, so drawing one takes no table of artwork: the rank and the suit are
 * the face. Which of the four is red is the one thing a reader has to be told.
 */
const RED_SUITS = new Set(["♥", "♦"]);

/** The face a joker draws, which is the mark and the colour it stands as. */
const JOKER_MARK = "*";
const RED_JOKER = "♥";
const BLACK_JOKER = "♠";

interface CardFaceProps {
  card: ProjectedCard;
}

/**
 * One place in a zone as it is read: the card standing there, or the back of one standing for a card unread.
 *
 * A card an observer is served is one it is entitled to read, so it draws its face whichever way up it lies.
 * A card lying face down is marked as such all the same, since that is what the rest of the table cannot read
 * and what the player holding it knows.
 */
export function CardFace({ card }: CardFaceProps): ReactElement {
  if (card === null) {
    return <div className="card back" aria-label="a card nobody at this seat reads" />;
  }

  const face = faceOf(card.card);
  const red = RED_SUITS.has(face.suit);
  return (
    <div
      className={classes("card", "face", red ? "red" : "black", card.face_down && "concealed")}
      aria-label={`${face.rank}${face.suit}`}
    >
      <span className="rank">{face.rank}</span>
      <span className="suit">{face.suit}</span>
    </div>
  );
}

/** The rank and suit one card draws as, which a joker takes the colour it was dealt in. */
function faceOf(card: CardOrJoker): { rank: string; suit: string } {
  if ("rank" in card) {
    return { rank: card.rank, suit: card.suit };
  }

  return { rank: JOKER_MARK, suit: card.red ? RED_JOKER : BLACK_JOKER };
}
