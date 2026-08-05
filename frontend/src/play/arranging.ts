import type { ProjectedCard, ZoneId, ZoneView } from "../api/views";
import { sameRun } from "./cards";

/**
 * An order a player laid a zone of their own out in, and the zone as it stood when they laid it.
 *
 * A command takes a moment to reach the table and come back, and the order a player laid down in that moment is
 * theirs to keep looking at. The cards it was laid over are what say when the table has caught up: the zone reads
 * as those cards for exactly as long as the commit carrying this order is still on its way.
 */
export interface Laid {
  zone: ZoneId;
  order: number[];
  stood: ProjectedCard[];
}

/** One order laid down, with the cards it was laid over, read out of the zone as it stood at that moment. */
export function laidFrom(zones: Record<ZoneId, ZoneView>, zone: ZoneId, order: number[]): Laid {
  return { zone, order, stood: zones[zone]?.cards ?? [] };
}

/**
 * The order a player has laid one zone out in, and none where the table has come to hold that zone itself.
 *
 * A zone reading as the cards the order was laid over is a zone the table has yet to lay out, so the order the
 * player is looking at is theirs until it arrives. The commit carrying it leaves the zone reading as that order,
 * and a table that moved on for reasons of its own leaves it reading as something else again: either way the
 * page reads the table from then on.
 */
export function laidIn(laid: Laid | null, zone: ZoneId, zones: Record<ZoneId, ZoneView>): number[] | null {
  if (laid?.zone !== zone) {
    return null;
  }

  return sameRun(laid.stood, zones[zone]?.cards ?? []) ? laid.order : null;
}
