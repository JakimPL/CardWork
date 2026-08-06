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

/**
 * A press of the other button, which the page answers itself.
 *
 * The browser answers this one with a menu of its own, and a page that means something by the press says so by
 * taking it over. It travels up from wherever it landed, so a right-click on a card, on a heap or on the felt
 * all reach the one answer the page holds for it.
 */
export function answering(answer: () => void): (event: MouseEvent) => void {
  return (event) => {
    event.preventDefault();
    answer();
  };
}
