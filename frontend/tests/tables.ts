import type { Layout } from "../src/api/layout";
import type { Cursor, EventView, PositionView, ProjectedCard, ZoneChange } from "../src/api/views";

/** The table these tests read, which is one hand, one heap, and a cursor holding a figure of its own. */
export const HAND = "hand:1";
export const STACK = "stack";
export const PILE = "pile";

export const SEATED: Cursor = {
  phase: "passing",
  to_act: [1],
  points: [3, 5, 8],
  round_number: 2,
  winner: null,
};

/** One readable card, stated by rank so a test says which card it means. */
export function card(rank: string, suit: string, face_down = false): ProjectedCard {
  return { card: { rank, suit }, face_down };
}

export function aView(zones: Record<string, ProjectedCard[]>, seq: number, state: Cursor = SEATED): PositionView {
  return {
    observer: 1,
    seq,
    zones: Object.fromEntries(
      Object.entries(zones).map(([zone, cards]) => [zone, { id: zone, owner: null, cards }]),
    ),
    state,
    legal: [],
  };
}

export function aCommit(seq: number, changes: ZoneChange[], state: Cursor = SEATED): EventView {
  return { seq, observer: 1, move: null, changes, state, legal: [] };
}

export function aLayout(layout: Partial<Layout>): Layout {
  return {
    title: "Passing",
    observer: 1,
    players: 3,
    slots: [],
    gestures: [],
    plaques: [],
    readouts: [],
    phases: {},
    ...layout,
  };
}
