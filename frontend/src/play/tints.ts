import type { Tint } from "../api/layout";

/**
 * The tints a company is told apart by, in the order the room hands them out, which mirrors
 * `cardwork.presentation.tint.Tint` and `cardserver.gathering.TINTS`.
 *
 * The vocabulary is generated from the endpoints and the order it is offered in is the page's to hold, the way
 * `play/codes.ts` holds the ranks a code is written from: a row of swatches has to know which eight there are
 * and which of them the first guest to arrive was handed.
 */
export const TINTS: Tint[] = ["rose", "coral", "amber", "lemon", "teal", "azure", "indigo", "violet"];
