import type { Commit, Gesture, Layout } from "../api/layout";
import type { AnyAction, Move } from "../api/moves";
import type { PositionView, ZoneId } from "../api/views";

/** The two places a move is sent onto, which mirror `cardwork.presentation.commit.Commit`. */
const ZONE = "zone" satisfies Commit;
const SEAT = "seat" satisfies Commit;

/** The place a player points at to send a move: a zone of the table, or the seat the move itself names. */
export type Target = { commit: typeof ZONE; zone: ZoneId } | { commit: typeof SEAT; seat: number };

/** The cards a player has picked up, which lie in one zone since one gesture picks in one. */
export interface Selection {
  zone: ZoneId;
  indices: number[];
}

/**
 * One move a seat may make, as the gesture that makes it states it.
 *
 * A served move names positions and a group; the gesture matching it says which zone those positions are in
 * and where the move is sent. Resolving the two here is what leaves the rest of the interface pointing at
 * cards and places rather than reading intents.
 */
export interface Offered {
  move: Move;
  picked: ZoneId | null;
  indices: number[];
  target: Target;
  caption: string;
}

/**
 * Everything a player may do to the table as it stands, out of the moves the table says are open.
 *
 * `open` names, per zone, the positions a click would take up: with nothing picked it is every card any move
 * names, which is the standing hint that these are the cards in play, and with cards in hand it narrows to the
 * ones a move holding those could still name. `armed` are the moves the selection stands complete for, and
 * `targets` the places they are sent onto — so a selection alone commits nothing, and pointing at a place is
 * what sends it.
 */
export interface Prospect {
  offers: Offered[];
  selection: Selection | null;
  open: Map<ZoneId, Set<number>>;
  armed: Offered[];
  targets: Target[];
}

/** The moves this seat may make, each read through its gesture, out of the position it was served. */
export function offersOf(layout: Layout, view: PositionView): Offered[] {
  return view.legal.flatMap((move) => {
    const offer = offered(layout, move);
    return offer === null ? [] : [offer];
  });
}

/**
 * What the offered moves come to for one selection: what may be picked next, and what is ready to send.
 *
 * A move naming no card at all is armed by no selection, since a selection is how cards are named.
 */
export function prospect(offers: Offered[], selection: Selection | null): Prospect {
  const candidates = offers.filter((offer) => follows(offer, selection));
  const armed = candidates.filter(
    (offer) => selection !== null && offer.indices.length > 0 && sameCards(offer.indices, selection.indices),
  );
  return { offers, selection, open: openIn(candidates, selection), armed, targets: distinctTargets(armed) };
}

/** Whether the player has this card in hand. */
export function isSelected(standing: Prospect, zone: ZoneId, index: number): boolean {
  const held = standing.selection;
  return held !== null && held.zone === zone && held.indices.includes(index);
}

/** Whether picking this card up leads somewhere, which is what leaves a card reading plainly. */
export function isOpen(standing: Prospect, zone: ZoneId, index: number): boolean {
  return standing.open.get(zone)?.has(index) ?? false;
}

/**
 * Whether a click on that card leads nowhere, which is what a card standing out of play reads as.
 *
 * A zone some move picks in holds cards a click carries further and cards it stops at, and telling the two
 * apart is the whole of what a player needs drawn. A zone no move picks in poses no choice at all, so its cards
 * read as cards and nothing more, and so do the cards of a table this seat owes no move to.
 */
export function leadsNowhere(standing: Prospect, zone: ZoneId, index: number): boolean {
  return picksIn(standing, zone) && !isSelected(standing, zone, index) && !isOpen(standing, zone, index);
}

/** Whether any move at all picks its cards in that zone, which is what makes its cards worth clicking. */
export function picksIn(standing: Prospect, zone: ZoneId): boolean {
  return standing.offers.some((offer) => offer.picked === zone);
}

/** The move a place sends, and none where pointing at that place sends nothing yet. */
export function offerTo(standing: Prospect, target: Target): Offered | null {
  return standing.armed.find((offer) => keyOf(offer.target) === keyOf(target)) ?? null;
}

/**
 * What the selection becomes when a player clicks one card, which is the whole of picking cards up.
 *
 * A card already in hand is put back down, and the last one down leaves nothing selected. A card a move could
 * name beside those in hand joins them. Anything else starts afresh on that card, or puts the selection down
 * where no move names the card at all — so a click always leaves the player somewhere they can see.
 */
export function pickedUp(standing: Prospect, zone: ZoneId, index: number): Selection | null {
  const held = standing.selection;
  if (held !== null && held.zone === zone) {
    if (held.indices.includes(index)) {
      return putDown(held, index);
    }

    if (isOpen(standing, zone, index)) {
      return { zone, indices: ordered([...held.indices, index]) };
    }
  }

  return pickable(standing.offers, zone, index) ? { zone, indices: [index] } : null;
}

/** One move as the gesture matching it states it, and none where the layout states no gesture for it. */
function offered(layout: Layout, move: Move): Offered | null {
  const gesture = layout.gestures.find((candidate) => matches(candidate, move.action));
  if (gesture === undefined) {
    return null;
  }

  const target = targetOf(gesture, move.action);
  return target === null
    ? null
    : {
        move,
        picked: gesture.picked,
        indices: ordered(indicesOf(move.action)),
        target,
        caption: gesture.caption,
      };
}

/** Whether a move carrying that action is the move a gesture makes, which mirrors `Gesture.matches`. */
function matches(gesture: Gesture, action: AnyAction): boolean {
  return gesture.kind === action.kind && (gesture.group === null || gesture.group === groupOf(action));
}

/** The group an intent names beside its positions, which mirrors `cardwork.moves.actions.group_of`. */
function groupOf(action: AnyAction): string | null {
  switch (action.kind) {
    case "play":
    case "take":
    case "discard":
      return action.group;
    case "pass":
    case "give":
    case "reject":
    case "declare":
      return null;
  }
}

/**
 * The positions an intent names, which mirrors `cardwork.moves.actions.indices_of`.
 *
 * A pass names its turn alone, so it reads as no position at all: a selection is a run of cards, and a move
 * that is about none of them is one a player states some other way than by pointing at cards.
 */
function indicesOf(action: AnyAction): number[] {
  return action.kind === "pass" ? [] : action.indices;
}

/** The place a gesture sends a move onto, which a seat commit takes from the move itself. */
function targetOf(gesture: Gesture, action: AnyAction): Target | null {
  if (gesture.commit === ZONE) {
    return gesture.target === null ? null : { commit: ZONE, zone: gesture.target };
  }

  return action.kind === "give" ? { commit: SEAT, seat: action.target_player } : null;
}

/** Whether a move could still be the one being built, which every move is while nothing is picked up. */
function follows(offer: Offered, selection: Selection | null): boolean {
  if (selection === null) {
    return true;
  }

  return offer.picked === selection.zone && selection.indices.every((index) => offer.indices.includes(index));
}

/**
 * Per zone, the positions a click would add to what is already in hand.
 *
 * A move made in no zone holds nothing open, since it is about no card: what a player does with one is stated
 * elsewhere than among the cards.
 */
function openIn(candidates: Offered[], selection: Selection | null): Map<ZoneId, Set<number>> {
  const open = new Map<ZoneId, Set<number>>();
  for (const candidate of candidates) {
    if (candidate.picked === null) {
      continue;
    }

    const held = selection !== null && selection.zone === candidate.picked ? selection.indices : [];
    const further = candidate.indices.filter((index) => !held.includes(index));
    if (further.length > 0) {
      const gathered = open.get(candidate.picked) ?? new Set<number>();
      for (const index of further) {
        gathered.add(index);
      }

      open.set(candidate.picked, gathered);
    }
  }

  return open;
}

/** The places the armed moves are sent onto, each named a single time. */
function distinctTargets(armed: Offered[]): Target[] {
  const named = new Map<string, Target>();
  for (const offer of armed) {
    named.set(keyOf(offer.target), offer.target);
  }

  return [...named.values()];
}

/** One name per place, which is how two moves are told to be sent onto the same one. */
function keyOf(target: Target): string {
  return target.commit === ZONE ? `${ZONE}:${target.zone}` : `${SEAT}:${target.seat}`;
}

/** The selection left when one card is put back down, and none once the last of them is. */
function putDown(held: Selection, index: number): Selection | null {
  const left = held.indices.filter((taken) => taken !== index);
  return left.length === 0 ? null : { zone: held.zone, indices: left };
}

/** Whether any move names that card, which is what a fresh selection of it would rest on. */
function pickable(offers: Offered[], zone: ZoneId, index: number): boolean {
  return offers.some((offer) => offer.picked === zone && offer.indices.includes(index));
}

/** Whether two sets of positions name the same cards, both of them holding each position once. */
function sameCards(one: number[], other: number[]): boolean {
  return one.length === other.length && one.every((index) => other.includes(index));
}

/** The positions in the order a hand reads, each named a single time. */
function ordered(indices: number[]): number[] {
  return [...new Set(indices)].sort((one, other) => one - other);
}
