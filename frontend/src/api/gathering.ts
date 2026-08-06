import type { components } from "./schema";

/**
 * The vocabulary a table is gathered in, as the lobby answers a page settling what to play.
 *
 * Every name here is generated from the OpenAPI document the endpoints publish, so a control the page draws
 * lists what the host says it offers and no field is written twice.
 */
export type Offering = components["schemas"]["Offering"];
export type Capacity = components["schemas"]["Capacity"];
export type Choice = components["schemas"]["Choice"];
export type Conclusion = components["schemas"]["Conclusion"];

export type Guest = components["schemas"]["Guest"];
export type GatheringView = components["schemas"]["GatheringView"];

export type Arriving = components["schemas"]["Arriving"];
export type Admitted = components["schemas"]["Admitted"];
export type Claiming = components["schemas"]["Claiming"];
export type Choosing = components["schemas"]["Choosing"];
export type Dealing = components["schemas"]["Dealing"];
