import type { components } from "./schema";

/**
 * The vocabulary a game states its arrangement in, as the table answers a request for a layout.
 *
 * Every name here is generated from the OpenAPI document the endpoints publish, so the shapes an interface
 * draws are the ones `cardwork.presentation` declares and no field is written twice. `/layout` is the one
 * answer that stands apart from the game's own state, which is what leaves it a schema to generate from.
 */
export type Layout = components["schemas"]["Layout"];
export type Slot = components["schemas"]["Slot"];
export type Gesture = components["schemas"]["Gesture"];
export type Plaque = components["schemas"]["Plaque"];
export type Readout = components["schemas"]["Readout"];
export type Tally = components["schemas"]["Tally"];

export type Spread = components["schemas"]["Spread"];
export type Commit = components["schemas"]["Commit"];
export type Scope = components["schemas"]["Scope"];
