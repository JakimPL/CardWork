import type { Gesture, Layout } from "../src/api/layout";
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

/** The table as it is played, for a test reading what a prospect lights up. */
export function aPlaying(standing: Prospect): Playing {
  return { standing, hint: "", sending: false, pick: IDLE, commit: IDLE, clear: IDLE };
}
