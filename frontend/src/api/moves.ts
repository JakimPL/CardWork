import type { components } from "./schema";

/**
 * A move as a client states it, and the answer a table meets one with.
 *
 * These are generated from the OpenAPI document as well, since `POST /moves` declares the request it takes
 * and the sequence it answers with. A move served back to a client — inside a view or an event — carries the
 * same shapes, which is what lets an interface match one it was offered to the gesture that sends it.
 */
export type Move = components["schemas"]["Move"];
export type AnyAction = components["schemas"]["AnyAction"];
export type ActionKind = components["schemas"]["ActionKind"];
export type MoveRequest = components["schemas"]["MoveRequest"];
export type MoveAccepted = components["schemas"]["MoveAccepted"];
