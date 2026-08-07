import type { Gesture, Interludes, Layout, Plaque, Slot } from "../src/api/layout";
import type { Move } from "../src/api/moves";
import type { Cursor, EventView, PositionView, ProjectedCard, ZoneChange, ZoneId } from "../src/api/views";
import type { Arrivals } from "../src/play/arrivals";
import type { Prospect } from "../src/play/selection";
import { TINTS } from "../src/play/tints";
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

/** The two zones a `showdown` seat holds beside its hand: the blind it picks in, and the place a card is sealed in. */
export function blindOf(seat: number): ZoneId {
  return `blind:${seat}`;
}

export function trayOf(seat: number): ZoneId {
  return `tray:${seat}`;
}

export function aBlind(seat: number): Slot {
  return { zone: blindOf(seat), label: "Blind", seat, spread: "stack", place: 1, counted: true };
}

export function aTray(seat: number): Slot {
  return { zone: trayOf(seat), label: "Sealed", seat, spread: "slot", place: 2, counted: false };
}

/** The seats around this one, each with the cards the table reads of them. */
export const AROUND: Slot[] = SEATS.filter((seat) => seat !== SEAT).map(aHolding);

/** A table of any size, every seat of it holding a hand the rest of the table reads the backs of. */
export function aTableOf(players: number, observer: number): Layout {
  const seats = [...Array(players).keys()];
  return aLayout({
    observer,
    players,
    slots: seats.map(aHolding),
    plaques: seats.map((seat) => ({ seat, name: `Seat ${seat}`, tint: null, counts: [] })),
  });
}

/** A plaque for every seat, each counting the hand that seat holds. */
export const PLAQUES: Plaque[] = SEATS.map((seat) => ({
  seat,
  name: `Seat ${seat}`,
  tint: null,
  counts: [{ zone: handOf(seat), label: "Cards" }],
}));

/** The same plaques as a table dealt out of a gathering carries them, each seat under a tint of its own. */
export const TINTED: Plaque[] = PLAQUES.map((plaque, seat) => ({ ...plaque, tint: TINTS[seat] ?? null }));

export const SEATED: Cursor = {
  phase: "passing",
  to_act: [1],
  points: [3, 5, 8],
  round_number: 2,
  winner: null,
};

/** The two phases a match played in rounds pauses at, as `presets.match_interludes` states them. */
export const BETWEEN_ROUNDS = "between_rounds";
export const MATCH_OVER = "match_over";
export const INTERLUDES: Interludes = { [BETWEEN_ROUNDS]: "round", [MATCH_OVER]: "match" };

/** A cursor standing at one of those two, which is a round closed or a match played out. */
export function atRest(phase: string, points: number[], round_points: number[]): Cursor {
  return { phase, to_act: [], points, round_number: 2, winner: null, round_points };
}

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

/** A gesture for a turn given up, which names no card and lands on no place, as a game allowing a pass states it. */
export const PASSING: Gesture = {
  kind: "pass",
  group: null,
  picked: null,
  commit: "word",
  target: null,
  caption: "Pass",
};

/** A second gesture a word sends, which is the shape a claim a seat makes about its whole holding takes. */
export const CLAIMING: Gesture = {
  kind: "declare",
  group: null,
  picked: null,
  commit: "word",
  target: null,
  caption: "Claim the rest",
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
    zones: Object.fromEntries(
      Object.entries(zones).map(([zone, cards]) => [zone, { id: zone, owner: null, arrangeable: false, cards }]),
    ),
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
    interludes: INTERLUDES,
    award: "highest",
    cues: true,
    ...layout,
  };
}

/** The same position, with the moves the table says this seat may make. */
export function offering(view: PositionView, legal: Move[]): PositionView {
  return { ...view, legal };
}

/** The same position, with one zone the table says this seat lays out in whatever order it pleases. */
export function sortable(view: PositionView, zone: ZoneId): PositionView {
  const held = view.zones[zone] ?? { id: zone, owner: SEAT, arrangeable: false, cards: [] };
  return { ...view, zones: { ...view.zones, [zone]: { ...held, arrangeable: true } } };
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

/** The turn given up, which names its seat and nothing besides. */
export function aPass(): Move {
  return { player: SEAT, action: { kind: "pass" } };
}

/** A claim made about a whole zone, which names its cards by naming none of them. */
export function aClaim(): Move {
  return { player: SEAT, action: { kind: "declare", claim: "the rest", indices: [] } };
}

/** Cards seen to land in one zone, as the commit that laid them there leaves the table reading. */
export function landing(zone: ZoneId, cards: number): Arrivals {
  return new Map([[zone, cards]]);
}

/** A click that does nothing, since what these tests read is the drawing rather than what follows one. */
const IDLE = (): void => undefined;

/** A seat that has laid no order of its own down, which is a page drawing every zone as the table holds it. */
const LAID_NONE = (): number[] | null => null;

/** The table as it is played, for a test reading what a prospect comes to. */
export function aPlaying(standing: Prospect): Playing {
  return {
    standing,
    hint: "",
    sending: false,
    pick: IDLE,
    commit: IDLE,
    say: IDLE,
    arrange: IDLE,
    laidIn: LAID_NONE,
    clear: IDLE,
  };
}
