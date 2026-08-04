import type { Gesture, Layout, Plaque, Slot } from "../src/api/layout";
import type { Move } from "../src/api/moves";
import type { Cursor, EventView, PositionView, ProjectedCard, ZoneChange, ZoneId } from "../src/api/views";
import type { Arrivals } from "../src/play/arrivals";
import type { Prospect } from "../src/play/selection";
import type { Playing } from "../src/play/usePlay";

/** The table these tests read, which is one hand, one heap, and a cursor holding a figure of its own. */
export const HAND = "hand:1";
export const STACK = "stack";
export const PILE = "pile";

/** The seat these tests play as, which is the middle one of three. */
export const SEAT = 1;

/** Every seat of that table, and the zone each of them holds its cards in. */
export const SEATS = [0, 1, 2];

export function handOf(seat: number): ZoneId {
  return `hand:${seat}`;
}

/** The three zones a table of `passing` lays out, as the seat playing it reads them. */
export const HELD: Slot = { zone: HAND, label: "Your hand", seat: SEAT, spread: "fan", place: 0, counted: false };
export const DEALT_FROM: Slot = { zone: PILE, label: "Pile", seat: null, spread: "stack", place: 0, counted: true };
export const LAID_ON: Slot = { zone: STACK, label: "Stack", seat: null, spread: "stack", place: 1, counted: true };

/** The hand of one other seat as the rest of the table reads it, which lies where that seat sits. */
export function aHolding(seat: number): Slot {
  return { zone: handOf(seat), label: "Hand", seat, spread: "fan", place: 0, counted: true };
}

/** The seats around this one, each with the cards the table reads of them. */
export const AROUND: Slot[] = SEATS.filter((seat) => seat !== SEAT).map(aHolding);

/** A plaque for every seat, each counting the hand that seat holds. */
export const PLAQUES: Plaque[] = SEATS.map((seat) => ({
  seat,
  name: `Seat ${seat}`,
  counts: [{ zone: handOf(seat), label: "Cards" }],
}));

export const SEATED: Cursor = {
  phase: "passing",
  to_act: [1],
  points: [3, 5, 8],
  round_number: 2,
  winner: null,
};

/** The two gestures `passing` states for a seat, as its own layout module states them. */
export const TAKING: Gesture = {
  kind: "take",
  group: PILE,
  picked: HAND,
  commit: "zone",
  target: PILE,
  caption: "Exchange this card for the top of the pile",
};

export const GIVING: Gesture = {
  kind: "give",
  group: null,
  picked: HAND,
  commit: "seat",
  target: null,
  caption: "Pass this card to the next seat",
};

/** A gesture taking a card off a heap the table shares onto the seat's own hand, as a game drawing from stock does. */
export const DRAWING: Gesture = {
  kind: "take",
  group: PILE,
  picked: PILE,
  commit: "zone",
  target: HAND,
  caption: "Draw this card into your hand",
};

/** A gesture sending several cards at once, which is the shape a game discarding a set of them takes. */
export const DISCARDING: Gesture = {
  kind: "discard",
  group: HAND,
  picked: HAND,
  commit: "zone",
  target: STACK,
  caption: "Discard these cards onto the stack",
};

/** One readable card, stated by rank so a test says which card it means. */
export function card(rank: string, suit: string, face_down = false): ProjectedCard {
  return { card: { rank, suit }, face_down };
}

export function aView(zones: Record<string, ProjectedCard[]>, seq: number, state: Cursor = SEATED): PositionView {
  return {
    observer: SEAT,
    seq,
    zones: Object.fromEntries(Object.entries(zones).map(([zone, cards]) => [zone, { id: zone, owner: null, cards }])),
    state,
    legal: [],
  };
}

export function aCommit(seq: number, changes: ZoneChange[], state: Cursor = SEATED): EventView {
  return { seq, observer: SEAT, move: null, changes, state, legal: [] };
}

export function aLayout(layout: Partial<Layout>): Layout {
  return {
    title: "Passing",
    observer: SEAT,
    players: 3,
    slots: [],
    gestures: [],
    plaques: [],
    readouts: [],
    phases: {},
    ...layout,
  };
}

/** The same position, with the moves the table says this seat may make. */
export function offering(view: PositionView, legal: Move[]): PositionView {
  return { ...view, legal };
}

export function aTake(indices: number[]): Move {
  return { player: SEAT, action: { kind: "take", group: PILE, indices } };
}

export function aGive(seat: number, indices: number[]): Move {
  return { player: SEAT, action: { kind: "give", target_player: seat, indices } };
}

export function aDiscard(indices: number[]): Move {
  return { player: SEAT, action: { kind: "discard", group: HAND, indices } };
}

/** Cards seen to land in one zone, as the commit that laid them there leaves the table reading. */
export function landing(zone: ZoneId, cards: number): Arrivals {
  return new Map([[zone, cards]]);
}

/** A click that does nothing, since what these tests read is the drawing rather than what follows one. */
const IDLE = (): void => undefined;

/** The table as it is played, for a test reading what a prospect comes to. */
export function aPlaying(standing: Prospect): Playing {
  return { standing, hint: "", sending: false, pick: IDLE, commit: IDLE, clear: IDLE };
}
