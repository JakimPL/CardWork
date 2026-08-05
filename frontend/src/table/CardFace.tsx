import type { ReactElement } from "react";

import type { Artwork } from "../api/artwork";
import type { CardOrJoker, ProjectedCard } from "../api/views";
import { useArtwork } from "../play/useArtwork";
import { drawnAt } from "./artwork";
import { classes } from "./classes";
import { clicking } from "./clicks";
import type { Handling } from "./dragging";
import { handled } from "./dragging";

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
  handling: Handling | null;
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
 *
 * A card of a run whose order is its owner's to set is taken hold of where it lies and carried to another place
 * in that run, and it draws faded while it travels, so a player reads the run as it is about to lie.
 *
 * A table opened with a pack of artwork draws every card as the picture that pack holds for it, and the same
 * element carries it: what a card is called, how it lies and what a press does with it are the drawing of a
 * card whichever way its face is arrived at.
 */
export function CardFace({ card, selected, dimmed, arriving, onPick, handling }: CardFaceProps): ReactElement {
  const artwork = useArtwork();
  const marks = classes(
    "card",
    ...facing(card),
    ...drawnFrom(artwork),
    selected && "selected",
    dimmed && "dimmed",
    arriving && "arriving",
    handling !== null && "sortable",
    handling !== null && handling.carried && "carried",
  );
  const label = card === null ? UNREAD : named(faceOf(card.card));
  const drawn = artwork === null ? glyphs(card) : picture(artwork, card);
  const handles = handled(handling);

  if (onPick === null) {
    return (
      <div className={marks} aria-label={label} {...handles}>
        {drawn}
      </div>
    );
  }

  return (
    <button
      type="button"
      className={marks}
      aria-label={label}
      aria-pressed={selected}
      onClick={clicking(onPick)}
      {...handles}
    >
      {drawn}
    </button>
  );
}

/** How a place in a zone reads: the back of a card, or a face in the colour its suit draws in. */
function facing(card: ProjectedCard): string[] {
  if (card === null) {
    return ["back"];
  }

  return ["face", RED_SUITS.has(faceOf(card.card).suit) ? "red" : "black", card.face_down ? "concealed" : ""];
}

/**
 * What the pack in service asks of the drawing of a card, which a page drawing its own glyphs asks none of.
 *
 * A pack states how its pictures take to being drawn at another size and whether they carry their own corners,
 * so the sheet is told both and every card of the table is drawn as the pack was written.
 */
function drawnFrom(artwork: Artwork | null): (string | false)[] {
  if (artwork === null) {
    return [];
  }

  return ["drawn", artwork.pixelated && "pixelated", artwork.cornered && "cornered"];
}

/**
 * One place of a zone as the pack in service draws it, which is the picture that pack holds for the card.
 *
 * The card is named by the label the element already carries, so the picture stands as the drawing of it and
 * a reader reaching the page by its words is told the card once.
 *
 * The card is what a player takes hold of, and the picture leaves the carrying to it: a run is laid out by
 * moving the cards of it, so a table drawing from a pack is dragged the same way as one drawing its own glyphs.
 */
function picture(artwork: Artwork, card: ProjectedCard): ReactElement {
  return <img className="art" src={drawnAt(artwork, card)} alt="" draggable={false} />;
}

/** The marks a page draws a card by on its own, where a card nobody reads draws as the back the sheet paints. */
function glyphs(card: ProjectedCard): ReactElement | null {
  return card === null ? null : shown(faceOf(card.card));
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
