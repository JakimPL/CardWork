import type { CSSProperties } from "react";

import type { Artwork } from "../api/artwork";
import type { Slot, Spread } from "../api/layout";
import type { PositionView, ProjectedCard, ZoneView } from "../api/views";
import type { Offered } from "../play/selection";
import type { Placement, Ring, Station } from "./placing";
import { linesOf } from "./placing";

/** The name the sheet reads the closest a run of cards may lie under, as a part of a card's width. */
const CLOSEST = "--closest";

/** The name the sheet reads a group's width under, in cards rather than pixels. */
const WIDTHS = "--widths";

/** The names the sheet reads one line by: how many cards wide it lies, and how many of them lie over another. */
const FILLING = "--filling";
const FANNED = "--fanned";

/** The names the sheet reads a line's partings under: between the zones along it, and between the cards inside them. */
const PARTED = "--parted";
const JOINTED = "--jointed";

/** The names the sheet reads the widest cut across the felt by: the cards standing along it, and their partings. */
const CARDS_ACROSS = "--cards-across";
const PARTED_ACROSS = "--parted-across";
const JOINTED_ACROSS = "--jointed-across";

/** One zone, which is the run a line has no parting to either side of. */
const ONE_ZONE = 1;

/** None of a thing, which is the depth of a middle nothing is shared at and the parting a lone zone stands with. */
const NOTHING = 0;

/** The names the sheet reads the proportions of a card under, both in the units the artwork was written in. */
const ASPECT_WIDTH = "--card-aspect-width";
const ASPECT_HEIGHT = "--card-aspect-height";

/** The names the sheet reads how the seats stand round the table under: up its sides, facing it, and in boxes. */
const STACKED = "--stacked";
const ABREAST = "--abreast";
const BOXES = "--boxes";

/** The names the sheet reads how deep the table lies under: the lines in the middle, and the lines at a seat. */
const LAID = "--laid";
const DEEPEST = "--deepest";

/** The two placements the felt divides its height between, which are the middle of the table and the seats round it. */
const MIDDLE: Placement = "shared";
const SEATED: Placement = "theirs";

/** One seat, which is the fewest a side of the table ever stands. */
const ONE_SEAT = 1;

/** Both sides of the table, which is how many seats stand across it in a box of their own where the sides hold any. */
const BOTH_SIDES = 2;

/** The words a turn is said in, which no group on the felt holds: those stand in the panel a player plays from. */
const SAID_NOWHERE: Offered[] = [];

/**
 * The least of a card a fan leaves showing, as a part of a card's width.
 *
 * A card is read by its corner, which is the part of it the card lying over it leaves showing. The index drawn
 * there stands at `0.17` of a card's height and is inset from the left edge of it, so the widest rank asks for
 * three-tenths of a card's width — measured at every height the games draw a card at, the floor the index rests
 * on at the smallest of them included. Both the index and the part left showing scale with the card, so a figure
 * stated as a part of a card's width holds at any size.
 *
 * A run standing for cards nobody at this seat reads says that cards lie where it lies and nothing besides, so it
 * closes to half of that and an edge apiece carries the whole of what there is to read.
 */
const A_CORNER = 0.3;
const AN_EDGE = 0.15;

/** One card, which is the room a heap takes and the first card of any run. */
const ONE_CARD = 1;

/** One card lying over another, which is the fewest a line's spare room is divided among. */
const ONE_LAP = 1;

/** How fine a figure the sheet is handed, which is a hundredth of the area either way. */
const FINENESS = 100;

/** A style carrying a figure the sheet works its geometry out from, beside the properties React names. */
type Measured = CSSProperties & Record<string, number>;

/**
 * One zone as the fitting reads it: how its cards lie against each other, how many lie there, and the closest
 * they may lie to one another.
 */
export interface Run {
  spread: Spread;
  held: number;
  closest: number;
}

/**
 * The closest a run of cards may lie, handed to the style sheet so a fan closes up rather than running off.
 *
 * The sheet works the rest out from there: a fan lies as open as a fan opens where its line has room to spare and
 * closes towards this figure as the line fills, so how far a run lies open follows the room it has rather than the
 * cards it holds.
 *
 * @param zone - the zone as this seat is served it, which is what says how its cards are read.
 */
export function fanning(zone: ZoneView | undefined): Measured {
  return { [CLOSEST]: closestIn(zone) };
}

/**
 * How wide a group of zones lies, counted in cards.
 *
 * A card is as tall as the room its group has for it: the panel a player plays from draws a hand of three at the
 * full height the window affords, and a hand of seventeen beside a row of five at the height their width leaves,
 * both read off one figure saying how many cards wide the group lies. A group standing in two lines is as wide as
 * the wider of them, so every card of it is drawn at one size. What that figure comes to in pixels is the sheet's,
 * since the proportions of a card belong to the drawing of one.
 *
 * A fan is counted at the closest its cards may lie, which is the tightest it will ever be drawn, so a group asks
 * for the width it takes at its tightest and the cards give way only once even that overflows. What the room left
 * over comes to is the sheet's, which spends it opening the fans back up.
 *
 * A group carries its partings as well — the ones between the zones lying along a line, and the ones between the
 * cards a zone lays side by side — since a group measured to the width it was handed keeps the room those take out
 * of the width its cards are drawn to, and neither of them is a width the cards themselves can be counted in.
 *
 * @param lines - the zones of the group, gathered into the lines they lie in.
 */
export function spanning(lines: Run[][]): Measured {
  return {
    [WIDTHS]: rounded(widthOf(lines)),
    [PARTED]: partingIn(lines),
    [JOINTED]: jointingIn(lines),
  };
}

/**
 * What one line of a group states for itself: how many cards wide it lies, and how many of them lie over another.
 *
 * The sheet spends the room a line has over the width its cards ask for on the cards that lie over another, so a
 * fan opens into whatever that line was left. Both figures are the line's own rather than the group's, so a fan on
 * the narrower of two lines opens into the room that line has rather than into the room the wider one left.
 *
 * @param runs - the zones lying along the line, in the order they stand along it.
 */
export function lining(runs: Run[]): Measured {
  const laps = runs.reduce((count, run) => count + lapping(run), NOTHING);
  return {
    [FILLING]: rounded(Math.max(ONE_CARD, filling(runs))),
    [FANNED]: Math.max(ONE_LAP, laps),
  };
}

/**
 * How the seats crowd a table, handed to the sheet so every card on the felt is drawn at one size.
 *
 * The seats up one side share the height the table has for them, so a table of seven draws the cards of a seat
 * smaller than a table of four does. The width goes by what the seats hold rather than by a share settled in
 * advance: the felt is as many cards wide as the widest cut across it, and the width one card is drawn to follows
 * from that. So a seat holding more cards is handed more of the felt rather than larger cards, and the seats round
 * a table draw alike wherever they sit.
 *
 * Every card on the table is drawn at that one height, the heaps in the middle with them: what a player reads of
 * another seat is a card the size of the card on the pile, since both of them are cards lying on the same table.
 * The height the felt has left over once every name and every count on it is written is shared out among the lines
 * of cards standing one above another, so the seats and the middle are handed the figures they need to work it
 * out: how many lines the middle lies in, and how many the deepest seat stands in.
 *
 * The boxes the seats are drawn in and the partings inside them are counted beside the cards, since a cut across
 * the felt holds all three and only the sheet knows what any of them comes to in pixels.
 *
 * @param ring - the seats round the table, gathered by the side of it they sit at.
 * @param middle - the zones every seat shares, which lie between them.
 * @param view - the table as this seat is served it, which is where the cards of a zone are counted.
 */
export function crowding(ring: Ring, middle: Slot[], view: PositionView): Measured {
  const flanked = ring.left.length > 0 || ring.right.length > 0;
  const seated = [...ring.left, ...ring.across, ...ring.right];
  const depths = seated.map((station) => linesOf(SEATED, station.slots).length);
  const cut = cutting(ring, middle, view);
  return {
    [STACKED]: Math.max(ONE_SEAT, ring.left.length, ring.right.length),
    [ABREAST]: Math.max(ONE_SEAT, ring.across.length),
    [BOXES]: (flanked ? BOTH_SIDES : NOTHING) + ring.across.length,
    [LAID]: middle.length === 0 ? NOTHING : linesOf(MIDDLE, middle).length,
    [DEEPEST]: Math.max(NOTHING, ...depths),
    [CARDS_ACROSS]: rounded(Math.max(ONE_CARD, cut.cards)),
    [PARTED_ACROSS]: cut.parted,
    [JOINTED_ACROSS]: cut.jointed,
  };
}

/**
 * How tall a card stands to its width, handed to the sheet so a pack is drawn at the shape it was written in.
 *
 * Every card is measured from one height, and the width follows from these two figures: a table opened with a
 * pack states the size its pictures were written at, and a table drawing the glyphs the page carries keeps the
 * proportions the sheet holds for them.
 *
 * @param artwork - the pack in service, where a table was opened with one.
 */
export function shaping(artwork: Artwork | null): Measured {
  return artwork === null ? {} : { [ASPECT_WIDTH]: artwork.width, [ASPECT_HEIGHT]: artwork.height };
}

/**
 * Each line of a group as the fitting reads it, with the words of a turn taking the room of a card among them.
 *
 * The reading is the group as it stands rather than as it is drawn, so anything measuring a group before the page
 * holds one — a hand weighed against the width the window has for it — asks the same question of the same figures.
 *
 * @param lines - the zones of the group, gathered into the lines they lie in.
 * @param view - the table as this seat is served it, which is where the cards of a zone are counted.
 * @param said - the moves a turn is said in words by, which lie at the end of the last line.
 */
export function measuring(lines: Slot[][], view: PositionView, said: Offered[]): Run[][] {
  return lines.map((line, index) => [
    ...line.map((slot) => reading(slot, view)),
    ...(index === lines.length - 1 ? saying(said) : []),
  ]);
}

/** One zone as the fitting reads it, which is how its cards lie and how many of them the observer is served. */
function reading(slot: Slot, view: PositionView): Run {
  const zone = view.zones[slot.zone];
  return { spread: slot.spread, held: zone?.cards.length ?? 0, closest: closestIn(zone) };
}

/**
 * The least of a card one zone leaves showing, which is the corner its cards are read by or an edge apiece.
 *
 * A run whose order this seat lays out itself is the run it picks its cards out of, so every card of it keeps the
 * corner carrying its index showing. A run holding a card lying face up is read by everybody at the table, so it
 * keeps its corner too. A run of backs and a run held face down under an order the table keeps say that cards lie
 * where they lie and nothing besides, so those close to an edge apiece. A zone standing nowhere on the table is
 * read as a run of cards would be, since it stands for the place one is drawn at.
 *
 * The one place the reading is made, so the figure the sheet is handed and the figure a group's width was measured
 * at cannot come apart.
 */
function closestIn(zone: ZoneView | undefined): number {
  if (zone === undefined) {
    return A_CORNER;
  }

  return zone.arrangeable || zone.cards.some(lyingFaceUp) ? A_CORNER : AN_EDGE;
}

/** Whether one place of a zone holds a card lying face up, which is a card everybody at the table reads. */
function lyingFaceUp(card: ProjectedCard): boolean {
  return card !== null && !card.face_down;
}

/** The room the words of a turn take, which is a card apiece and none at all where a turn is said in none. */
function saying(said: Offered[]): Run[] {
  return said.length === 0 ? [] : [{ spread: "row", held: said.length, closest: A_CORNER }];
}

/** How many cards wide one zone lies: a heap reads by one card, a row by all of them, a fan by its closest. */
function running(run: Run): number {
  switch (run.spread) {
    case "stack":
    case "slot":
      return ONE_CARD;
    case "row":
      return Math.max(ONE_CARD, run.held);
    case "fan":
      return run.held <= ONE_CARD ? ONE_CARD : ONE_CARD + (run.held - ONE_CARD) * run.closest;
  }
}

/** How many cards of one zone lie over another, which is every card of a fan past the first and none elsewhere. */
function lapping(run: Run): number {
  return run.spread === "fan" ? Math.max(NOTHING, run.held - ONE_CARD) : NOTHING;
}

/** How many partings lie inside one zone: a row lays every card of itself apart, and the rest draw a single card. */
function jointing(run: Run): number {
  return run.spread === "row" ? Math.max(NOTHING, run.held - ONE_CARD) : NOTHING;
}

/** How many cards wide one line lies, which is the room the runs standing along it take together. */
function filling(runs: Run[]): number {
  return runs.reduce((room, run) => room + running(run), NOTHING);
}

/** How many cards wide a group lies, which is the widest of the lines it lies in. */
function widthOf(lines: Run[][]): number {
  return Math.max(ONE_CARD, ...lines.map(filling));
}

/** How many partings lie between the zones of a group, counted along the line standing the most of them. */
function partingIn(lines: Run[][]): number {
  return Math.max(NOTHING, ...lines.map((line) => line.length - ONE_ZONE));
}

/** How many partings lie between the cards a group lays side by side, counted along the line standing the most. */
function jointingIn(lines: Run[][]): number {
  return Math.max(NOTHING, ...lines.map((line) => line.reduce((count, run) => count + jointing(run), NOTHING)));
}

/**
 * What one group of zones takes out of a cut across the felt: the cards it lies as many wide as, and its partings.
 *
 * The three are counted apart because they are three different widths — a card, a parting between zones, and a
 * parting between cards laid side by side — and what each comes to in pixels is the sheet's to say.
 */
interface Cut {
  cards: number;
  parted: number;
  jointed: number;
}

/** A cut across nothing at all, which is what a side standing empty and a middle sharing nothing take. */
const BARE: Cut = { cards: NOTHING, parted: NOTHING, jointed: NOTHING };

/**
 * The widest cut across the felt, which is what the width of one card is worked out from.
 *
 * A seat up a side of the table stands as wide as the widest seat at that side, since the seats there stand one
 * above another. The seats facing the near edge stand side by side, and the zones every seat shares lie beneath
 * them, so the middle of the felt is as wide as the greater of those two. The three columns stand alongside each
 * other, which is the cut every card on the felt is measured by.
 *
 * @param ring - the seats round the table, gathered by the side of it they sit at.
 * @param middle - the zones every seat shares, which lie between them.
 * @param view - the table as this seat is served it, which is where the cards of a zone are counted.
 */
function cutting(ring: Ring, middle: Slot[], view: PositionView): Cut {
  const facing = alongside(cutsOf(ring.across, view));
  const shared = middle.length === 0 ? BARE : cutOf(MIDDLE, middle, view);
  return alongside([widest(cutsOf(ring.left, view)), widest(cutsOf(ring.right, view)), widest([facing, shared])]);
}

/** The seats at one side of the table as a cut across the felt counts them, one cut apiece. */
function cutsOf(seats: Station[], view: PositionView): Cut[] {
  return seats.map((station) => cutOf(SEATED, station.slots, view));
}

/** One group of zones as a cut across the felt counts it, which is the group as the fitting already reads it. */
function cutOf(place: Placement, slots: Slot[], view: PositionView): Cut {
  const lines = measuring(linesOf(place, slots), view, SAID_NOWHERE);
  return { cards: widthOf(lines), parted: partingIn(lines), jointed: jointingIn(lines) };
}

/** What groups standing side by side take, which is what all of them take together. */
function alongside(cuts: Cut[]): Cut {
  return cuts.reduce(
    (along, cut) => ({
      cards: along.cards + cut.cards,
      parted: along.parted + cut.parted,
      jointed: along.jointed + cut.jointed,
    }),
    BARE,
  );
}

/** What groups standing one above another take, which is what the widest of them takes. */
function widest(cuts: Cut[]): Cut {
  return cuts.reduce(
    (over, cut) => ({
      cards: Math.max(over.cards, cut.cards),
      parted: Math.max(over.parted, cut.parted),
      jointed: Math.max(over.jointed, cut.jointed),
    }),
    BARE,
  );
}

/** One figure at the fineness the sheet is handed, which is a hundredth of the area the cards lie in. */
function rounded(part: number): number {
  return Math.round(part * FINENESS) / FINENESS;
}
