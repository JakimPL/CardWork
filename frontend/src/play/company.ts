import type { GatheringView, Guest, Tint } from "../api/gathering";

/** What the button calling for the deal reads once nothing stands in the way of it. */
const DEAL = "Deal the cards";

/** What a guest standing at the gathering is told, since the players of the game are the ones who settle it. */
const STANDING = "Take a seat to deal";

/** Every seat of the table the company settled on, which is what a page draws a place for. */
export function seatsOf(gathering: GatheringView): number[] {
  return [...Array(gathering.choice.players).keys()];
}

/** The guest holding one seat, and nothing where it stands empty. */
export function holderOf(gathering: GatheringView, seat: number): Guest | null {
  return gathering.company.find((guest) => guest.seat === seat) ?? null;
}

/** The guests at the gathering who hold no seat, which is everyone watching it. */
export function standingBy(gathering: GatheringView): Guest[] {
  return gathering.company.filter((guest) => guest.seat === null);
}

/** The seats of the table nobody holds, which are the ones the deal waits on. */
export function emptySeats(gathering: GatheringView): number[] {
  return seatsOf(gathering).filter((seat) => holderOf(gathering, seat) === null);
}

/** The seat the guest reading the page holds, and nothing while they are standing. */
export function mySeat(gathering: GatheringView): number | null {
  return gathering.company.find((guest) => guest.name === gathering.mine)?.seat ?? null;
}

/** Whether this seat is the one the guest reading the page holds. */
export function mine(gathering: GatheringView, seat: number): boolean {
  return mySeat(gathering) === seat;
}

/** The tint the guest reading the page plays under, and nothing where the company reads nobody by that name. */
export function myTint(gathering: GatheringView): Tint | null {
  return gathering.company.find((guest) => guest.name === gathering.mine)?.tint ?? null;
}

/** The guest holding one tint, and nothing where it stands free for whoever takes it. */
export function tintHeldBy(gathering: GatheringView, tint: Tint): Guest | null {
  return gathering.company.find((guest) => guest.tint === tint) ?? null;
}

/**
 * Whether the guest reading the page holds a say over what the table plays and when it is dealt.
 *
 * This mirrors `cardserver.gathering.SeatedSay`: standing at a gathering is watching it and taking a seat is
 * joining the game, so the players of the game settle what is played. The page reads it to draw its controls
 * as the server would answer them, and the server answers for itself either way.
 */
export function hasSay(gathering: GatheringView): boolean {
  return mySeat(gathering) !== null;
}

/**
 * What stands in the way of the deal, and nothing where the table may be dealt as it stands.
 *
 * A gathering is dealt once every seat is taken, and by a guest holding a seat at it. Both are what the server
 * refuses on, so what is read here is the sentence a person is shown before they meet the refusal.
 */
export function holdingUpTheDeal(gathering: GatheringView): string | null {
  if (!hasSay(gathering)) {
    return STANDING;
  }

  const empty = emptySeats(gathering);
  if (empty.length > 0) {
    return empty.length === 1 ? "One seat still to be taken" : `${empty.length} seats still to be taken`;
  }

  return null;
}

/** What the button calling for the deal reads, which is what holds the deal up while something does. */
export function dealReading(gathering: GatheringView): string {
  return holdingUpTheDeal(gathering) ?? DEAL;
}

/** Whether the deal may be called for as the gathering stands. */
export function dealReady(gathering: GatheringView): boolean {
  return holdingUpTheDeal(gathering) === null;
}
