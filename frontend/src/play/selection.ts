import type { Commit, Gesture, Layout } from "../api/layout";
import type { AnyAction, Move } from "../api/moves";
import type { PositionView, ProjectedCard, ZoneId, ZoneView } from "../api/views";
import { cardsAt, sameRun } from "./cards";

/** The three ways a move is sent, which mirror `cardwork.presentation.commit.Commit`. */
const ZONE = "zone" satisfies Commit;
const SEAT = "seat" satisfies Commit;
const WORD = "word" satisfies Commit;

/**
 * The place a player points at to send a move: a zone of the table, or the seat the move itself names.
 *
 * A move said by its word is sent by pressing the one thing standing for it, so it stands beside these places
 * rather than among them.
 */
export type Target = { commit: typeof ZONE; zone: ZoneId } | { commit: typeof SEAT; seat: number };

/** The cards a player has picked up, which lie in one zone since one gesture picks in one. */
export interface Selection {
  zone: ZoneId;
  indices: number[];
}

/**
 * A selection as it was made: the cards picked up, and the cards that lay at the positions naming them.
 *
 * A move quotes positions, so what a selection stands for is the cards lying at those positions. Keeping the ones
 * it was made on is what lets the page tell a table that has moved on from a hand that has.
 */
export interface Held {
  selection: Selection;
  picked: ProjectedCard[];
}

/**
 * One move a seat may make, as the gesture that makes it states it.
 *
 * A served move names positions and a group; the gesture matching it says which zone those positions are in
 * and where the move is sent. Resolving the two here is what leaves the rest of the interface pointing at
 * cards and places rather than reading intents.
 *
 * A move about no card is made in no zone and sent by no place, so it reads as naming neither: what it takes to
 * send is the caption it carries.
 */
export interface Offered {
  move: Move;
  picked: ZoneId | null;
  indices: number[];
  target: Target | null;
  caption: string;
}

/**
 * Everything a player may do to the table as it stands, out of the moves the table says are open.
 *
 * `open` names, per zone, the positions a click would take up: with nothing picked it is every card any move
 * names, which is the standing hint that these are the cards in play, and with cards in hand it narrows to the
 * ones a move holding those could still name. `armed` are the moves the selection stands complete for, `targets`
 * the places those are pointed at, and `said` the ones a word sends — so a selection alone commits nothing, and
 * what sends it is a point at a place or a press where the words are.
 */
export interface Prospect {
  offers: Offered[];
  selection: Selection | null;
  open: Map<ZoneId, Set<number>>;
  armed: Offered[];
  targets: Target[];
  said: Offered[];
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
 * A move is armed when the cards in hand are exactly the cards it names, so an empty hand arms a move naming
 * none of them and the first card picked up disarms it.
 */
export function prospect(offers: Offered[], selection: Selection | null): Prospect {
  const candidates = offers.filter((offer) => follows(offer, selection));
  const armed = candidates.filter((offer) => sameCards(offer.indices, heldIn(selection)));
  return {
    offers,
    selection,
    open: openIn(candidates, selection),
    armed,
    targets: distinctTargets(armed),
    said: saidOf(armed),
  };
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
  return standing.armed.find((offer) => offer.target !== null && keyOf(offer.target) === keyOf(target)) ?? null;
}

/**
 * The moves a word sends, out of every move the table offers, whichever of them the cards in hand arm.
 *
 * A move landing on no place is one said by its word, since a gesture stating a place states where it lands. So
 * these are the moves an interface draws the words of, and `armed` says which of the words drawn may be pressed:
 * a turn holding one of these has somewhere to say it for as long as the table offers it.
 */
export function wordsOf(standing: Prospect): Offered[] {
  return standing.offers.filter((offer) => offer.target === null);
}

/** Whether the cards in hand are the cards a move names, which is what leaves that move ready to send. */
export function isArmed(standing: Prospect, offer: Offered): boolean {
  return standing.armed.includes(offer);
}

/**
 * The one move a word sends where a turn stands ready to say a single move, and none where it stands ready to
 * say two.
 *
 * A keystroke says a move where a turn leaves no question which move it means. Where two stand ready at once,
 * which of them is said belongs to the player, so each is said by pressing the words drawn for it.
 */
export function saidAlone(standing: Prospect): Offered | null {
  return standing.said.length === 1 ? (standing.said[0] ?? null) : null;
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

/** One selection with the cards it was made on, read out of the zone as it stood at the moment of the picking. */
export function heldFrom(zones: Record<ZoneId, ZoneView>, selection: Selection): Held {
  return { selection, picked: cardsAt(zones[selection.zone], selection.indices) };
}

/**
 * Whether a selection still names the cards it was made on, which is what leaves it standing in a player's hand.
 *
 * A table moves on for reasons of its own: another seat plays, another seat sorts the cards it is holding, the
 * rules settle a round. A selection outlives every commit that leaves its own cards lying where they lay, and
 * comes back down as they move — which is the moment its positions would come to name other cards than the ones
 * a player picked up.
 */
export function stands(held: Held, zones: Record<ZoneId, ZoneView>): boolean {
  return sameRun(held.picked, cardsAt(zones[held.selection.zone], held.selection.indices));
}

/**
 * One move as the gesture matching it states it, and none where the two disagree about where it lands.
 *
 * A gesture stating a place stands for a move only once that place is named, so a commit onto a seat holds for a
 * move naming one. A gesture said by its word lands on no place, and states the move naming none.
 */
function offered(layout: Layout, move: Move): Offered | null {
  const gesture = layout.gestures.find((candidate) => matches(candidate, move.action));
  if (gesture === undefined) {
    return null;
  }

  const target = targetOf(gesture, move.action);
  if (target === null && gesture.commit !== WORD) {
    return null;
  }

  return {
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

/**
 * The place a gesture sends a move onto, and none where the move lands on no place a player points at.
 *
 * Each way of sending a move is answered for in turn, so a fourth added to the vocabulary says here what it
 * lands on: a zone commit names its zone, a seat commit takes the seat from a move naming one, and a move said
 * by its word is pressed where its words are.
 */
function targetOf(gesture: Gesture, action: AnyAction): Target | null {
  switch (gesture.commit) {
    case ZONE:
      return gesture.target === null ? null : { commit: ZONE, zone: gesture.target };
    case SEAT:
      return action.kind === "give" ? { commit: SEAT, seat: action.target_player } : null;
    case WORD:
      return null;
  }
}

/**
 * Whether a move could still be the one being built, which every move is while nothing is picked up.
 *
 * A move made in no zone stands only while the hand is empty, since a card picked up is a card it never names.
 */
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

/** The places the armed moves are pointed at, each named a single time, out of the ones a place sends. */
function distinctTargets(armed: Offered[]): Target[] {
  const named = new Map<string, Target>();
  for (const offer of armed) {
    if (offer.target !== null) {
      named.set(keyOf(offer.target), offer.target);
    }
  }

  return [...named.values()];
}

/** The armed moves a word sends, which reach the table by the caption they carry rather than by a place. */
function saidOf(armed: Offered[]): Offered[] {
  return armed.filter((offer) => offer.target === null);
}

/** The cards in hand, which reads as none of them while nothing is picked up. */
function heldIn(selection: Selection | null): number[] {
  return selection === null ? [] : selection.indices;
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
