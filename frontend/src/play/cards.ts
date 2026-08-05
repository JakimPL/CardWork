import type { CardOrJoker, ProjectedCard, ZoneView } from "../api/views";

/**
 * The cards lying at a run of positions of one zone, one apiece for every position the zone holds.
 *
 * A position a zone has since given up yields no card at all, so a run read twice is the same length only where
 * every position it names still holds one — which is what tells a hand that has changed from a hand that has not.
 */
export function cardsAt(zone: ZoneView | undefined, indices: number[]): ProjectedCard[] {
  const cards = zone?.cards ?? [];
  return indices.map((index) => cards[index]).filter((card) => card !== undefined);
}

/**
 * Whether two runs read as the same cards lying in the same order.
 *
 * A run of cards nobody at this seat reads is the same run however it is permuted, which is what a position of a
 * stock names: the place, rather than whichever card happens to lie in it.
 */
export function sameRun(one: ProjectedCard[], other: ProjectedCard[]): boolean {
  return one.length === other.length && one.every((card, place) => sameCard(card, other[place]));
}

/** Whether two places hold the one card, which two places holding none of it read as. */
function sameCard(one: ProjectedCard, other: ProjectedCard | undefined): boolean {
  if (one === null || other === null || other === undefined) {
    return one === other;
  }

  return one.face_down === other.face_down && sameFace(one.card, other.card);
}

/** Whether two cards are the one card, which a rank and a suit name and a joker names by the colour it was dealt in. */
function sameFace(one: CardOrJoker, other: CardOrJoker): boolean {
  if ("rank" in one) {
    return "rank" in other && one.rank === other.rank && one.suit === other.suit;
  }

  return !("rank" in other) && one.red === other.red;
}
