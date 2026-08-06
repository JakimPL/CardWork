import type { ReactElement } from "react";

import type { Direction, Lying, Ordering } from "../play/ordering";
import { orderedBy, turnedTo } from "../play/ordering";
import { clicking } from "./clicks";

/** The orders a hand can be put in, in the order a player is offered them. */
const ORDERINGS: Ordering[] = ["rank", "suit"];

/** What each of them is called on the press that applies it, and what that press does said in full. */
const CALLED: Record<Ordering, string> = { rank: "Rank", suit: "Suit" };
const SPELLED: Record<Ordering, string> = { rank: "Sort by rank", suit: "Sort by suit" };

/** Which end the next press reads the order from, drawn as an arrow and read out as a word. */
const ARROWS: Record<Direction, string> = { up: "↑", down: "↓" };
const WAYS: Record<Direction, string> = { up: "ascending", down: "descending" };

interface SortingProps {
  run: Lying[];
  onSort: (order: number[]) => void;
}

/**
 * The presses that put a run in order, which stand at the end of the name of the zone they order.
 *
 * The order of a hand is the player's own, so what sets it lies with the hand: two words beside the name of the
 * zone, each lettered with the end it is about to read the order from. A press names the order the whole run comes
 * to lie in, which is the reading a card carried through it by hand sends, so a hand sorted and a hand laid out
 * reach the table by the one road.
 *
 * @param run - the cards as the player reads them now, which the order is worked out from and sent as.
 * @param onSort - the order laid down, which the zone holding the run sends on the player's behalf.
 */
export function Sorting({ run, onSort }: SortingProps): ReactElement {
  return (
    <span className="sorting">
      {ORDERINGS.map((by) => {
        const way = turnedTo(run, by);
        const naming = `${SPELLED[by]}, ${WAYS[way]}`;
        return (
          <button
            key={by}
            type="button"
            className="sort"
            title={naming}
            aria-label={naming}
            onClick={clicking(() => {
              onSort(orderedBy(run, by, way));
            })}
          >
            {CALLED[by]}
            <span aria-hidden="true">{ARROWS[way]}</span>
          </button>
        );
      })}
    </span>
  );
}
