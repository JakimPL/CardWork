import type { GatheringView, Guest, Tint } from "../api/gathering";

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

/** The guest reading the page, and nothing where the company reads nobody by that name. */
export function me(gathering: GatheringView): Guest | null {
  return gathering.company.find((guest) => guest.name === gathering.mine) ?? null;
}

/** The seat the guest reading the page holds, and nothing while they are standing. */
export function mySeat(gathering: GatheringView): number | null {
  return me(gathering)?.seat ?? null;
}

/** The guests holding a seat, who are the players the deal is dealt to and the ones a commitment is asked of. */
export function seatedGuests(gathering: GatheringView): Guest[] {
  return gathering.company.filter((guest) => guest.seat !== null);
}

/** Whether the guest reading the page gathered the table, whose say governs it while it is settled host by host. */
export function iAmHost(gathering: GatheringView): boolean {
  return me(gathering)?.host ?? false;
}

/** Whether the guest reading the page has committed to the settings as they stand. */
export function iAmReady(gathering: GatheringView): boolean {
  return me(gathering)?.ready ?? false;
}

/**
 * Whether the guest reading the page may call the deal.
 *
 * A democratic table leaves the deal to every seat, as it leaves the settling; a host-governed one keeps it to
 * the host alone, so a seated guest reads it as the wait it is until the host calls it.
 */
export function mayDeal(gathering: GatheringView): boolean {
  return gathering.democratic || iAmHost(gathering);
}

/** Whether every seat is taken and every seated guest has committed, which is the whole of what the deal waits on. */
export function everyoneReady(gathering: GatheringView): boolean {
  return emptySeats(gathering).length === 0 && seatedGuests(gathering).every((guest) => guest.ready);
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
 * A gathering is dealt once every seat is taken and every seated guest has committed to the settings, and by a
 * guest holding a seat at it. Each is what the server refuses on, so what is read here is the sentence a person
 * is shown before they meet the refusal: a seat still to be taken first, and a commitment still to be given once
 * the table is full.
 */
export function holdingUpTheDeal(gathering: GatheringView): string | null {
  if (!hasSay(gathering)) {
    return STANDING;
  }

  const empty = emptySeats(gathering);
  if (empty.length > 0) {
    return empty.length === 1 ? "One seat still to be taken" : `${empty.length} seats still to be taken`;
  }

  const waiting = seatedGuests(gathering).filter((guest) => !guest.ready).length;
  if (waiting > 0) {
    return waiting === 1 ? "One player still to ready" : `${waiting} players still to ready`;
  }

  return null;
}

/**
 * The one press the room carries a seated guest through, from committing to the settings to calling the deal.
 *
 * `stand` is for the guest holding no seat, who neither commits nor deals. `ready` is for a seated guest while
 * anything holds the deal up: they commit to the settings or take that commitment back, and `pending` reads what
 * the table still waits on. `deal` stands once nothing does and the guest may call it. `wait` stands then for a
 * seated guest a host-governed table leaves the deal to the host: they are ready and the table is, and the press
 * is the host's to make.
 */
export type Commit =
  | { readonly act: "stand" }
  | { readonly act: "ready"; readonly ready: boolean; readonly pending: string }
  | { readonly act: "deal" }
  | { readonly act: "wait" };

/** How the room's one press reads for the guest reading it, out of where the gathering and their seat stand. */
export function commitOf(gathering: GatheringView): Commit {
  if (!hasSay(gathering)) {
    return { act: "stand" };
  }

  const pending = holdingUpTheDeal(gathering);
  if (pending !== null) {
    return { act: "ready", ready: iAmReady(gathering), pending };
  }

  return mayDeal(gathering) ? { act: "deal" } : { act: "wait" };
}
