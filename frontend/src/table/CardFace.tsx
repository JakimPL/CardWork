import type { ReactElement } from "react";

import type { CardOrJoker, ProjectedCard } from "../api/views";
import { classes } from "./classes";
import { clicking } from "./clicks";

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

/** What a card nobody at this seat reads is called, for a reader who reaches the page by its words. */
const UNREAD = "a card nobody at this seat reads";

/** The rank and suit one card draws as. */
interface Face {
  rank: string;
  suit: string;
}

interface CardFaceProps {
  card: ProjectedCard;
  selected: boolean;
  dimmed: boolean;
  arriving: boolean;
  onPick: (() => void) | null;
}

/**
 * One place in a zone as it is read: the card standing there, or the back of one standing for a card unread.
 *
 * A card an observer is served is one it is entitled to read, so it draws its face whichever way up it lies.
 * A card lying face down is marked as such all the same, since that is what the rest of the table cannot read
 * and what the player holding it knows.
 *
 * A card in hand stands raised out of the run it was picked from, which is the one mark a card carries for being
 * chosen. A card a click stops at fades back, so what a player reads plainly is what a press carries further —
 * the cards in play at a glance, and the cards a selection could still grow by once one is in hand.
 *
 * A card that has just been laid where it lies comes in from the hand it was played out of, which is what a
 * player watching the table sees happen.
 */
export function CardFace({ card, selected, dimmed, arriving, onPick }: CardFaceProps): ReactElement {
  const marks = classes("card", ...drawing(card), selected && "selected", dimmed && "dimmed", arriving && "arriving");
  const label = card === null ? UNREAD : named(faceOf(card.card));
  const pips = card === null ? null : shown(faceOf(card.card));

  if (onPick === null) {
    return (
      <div className={marks} aria-label={label}>
        {pips}
      </div>
    );
  }

  return (
    <button type="button" className={marks} aria-label={label} aria-pressed={selected} onClick={clicking(onPick)}>
      {pips}
    </button>
  );
}

/** How a place in a zone is drawn: the back of a card, or a face in the colour its suit reads in. */
function drawing(card: ProjectedCard): string[] {
  if (card === null) {
    return ["back"];
  }

  return ["face", RED_SUITS.has(faceOf(card.card).suit) ? "red" : "black", card.face_down ? "concealed" : ""];
}

/** The rank and suit one card draws as, which a joker takes the colour it was dealt in. */
function faceOf(card: CardOrJoker): Face {
  if ("rank" in card) {
    return { rank: card.rank, suit: card.suit };
  }

  return { rank: JOKER_MARK, suit: card.red ? RED_JOKER : BLACK_JOKER };
}

/** What one card is called, which is the rank and the suit as they are written. */
function named(face: Face): string {
  return `${face.rank}${face.suit}`;
}

/**
 * The two marks a face carries: the index in the corner, and the suit across the middle.
 *
 * A card is read by its corner, which is the part of it a card lying over it leaves showing, so a hand of any
 * size reads by running an eye down the left edge of it. The middle says the same thing at the size a heap and
 * a single card are read across a table at.
 */
function shown(face: Face): ReactElement {
  return (
    <>
      <span className="index">
        <span className="rank">{face.rank}</span>
        <span className="suit">{face.suit}</span>
      </span>
      <span className="pip">{face.suit}</span>
    </>
  );
}
