import type { MouseEvent } from "react";

/**
 * A click that does one thing and leaves the page nothing to make of it.
 *
 * The page puts the selection down when a click reaches it, which is how clicking away from the cards clears
 * one. A click a card or a place has already answered stops where it was answered.
 */
export function clicking(answer: () => void): (event: MouseEvent) => void {
  return (event) => {
    event.stopPropagation();
    answer();
  };
}
