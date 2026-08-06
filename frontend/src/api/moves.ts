import type { components } from "./schema";

/**
 * The two commands a client sends, and the answer a table meets either of them with.
 *
 * These are generated from the OpenAPI document as well, since `POST /moves` and `POST /arrangements` declare
 * the requests they take and the sequence they answer with. A move served back to a client — inside a view or
 * an event — carries the same shapes, which is what lets an interface match one it was offered to the gesture
 * that sends it.
 */
export type Move = components["schemas"]["Move"];
export type AnyAction = components["schemas"]["AnyAction"];
export type ActionKind = components["schemas"]["ActionKind"];
export type MoveRequest = components["schemas"]["MoveRequest"];
export type ArrangementRequest = components["schemas"]["ArrangementRequest"];
export type CommandAccepted = components["schemas"]["CommandAccepted"];
