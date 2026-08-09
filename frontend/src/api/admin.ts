import { asking, SENDING, STATING, stating } from "./requests";
import type { components } from "./schema";

/**
 * The vocabulary the overseer reads and runs the lobby through, generated from the admin routes the server
 * publishes.
 *
 * Every one of these answers behind the token the host was started under, which no guest holds: the panel names
 * the tables the lobby holds, the terms it holds them under, and the levers over both.
 */
export type LobbyView = components["schemas"]["LobbyView"];
export type LobbySetting = components["schemas"]["LobbySetting"];
export type TableCard = components["schemas"]["TableCard"];
export type Posting = components["schemas"]["Posting"];
export type Closing = components["schemas"]["Closing"];
export type Creation = components["schemas"]["Creation"];

const ADMIN_LOBBY = "/admin/lobby";
const ADMIN_TABLES = "/admin/tables";
const ADMIN_REAP = "/admin/reap";
const CLOSING = "closing";

/** The header the overseer offers the admin token in, which mirrors `cardserver.identity.headers.ADMIN_HEADER`. */
export const ADMIN_HEADER = "X-Admin-Token";

/** What the reap route is told, which is nothing: it clears away every table too stale to keep and names them. */
const NOTHING = {};

/** The headers the overseer speaks through, which carry the admin token and nothing a guest would offer. */
export function overseeing(admin: string): Record<string, string> {
  return { [ADMIN_HEADER]: admin };
}

/** The whole lobby as the overseer reads it: every table it holds, and the terms it holds them under. */
export function readLobby(admin: string): Promise<LobbyView> {
  return asking<LobbyView>(ADMIN_LOBBY, overseeing(admin));
}

/** Settle the terms the lobby is held under: how many tables stand at once, and who may open one. */
export function settleLobby(admin: string, setting: LobbySetting): Promise<LobbyView> {
  return stating<LobbyView, LobbySetting>(ADMIN_LOBBY, STATING, overseeing(admin), setting);
}

/** Gather a table on the company's behalf, answering with the card that carries the code it admits on. */
export function postTable(admin: string, posting: Posting): Promise<TableCard> {
  return stating<TableCard, Posting>(ADMIN_TABLES, SENDING, overseeing(admin), posting);
}

/** Break one table up whether it is gathering or in play, and answer with the lobby it leaves behind. */
export function closeTable(admin: string, table: string, closing: Closing): Promise<LobbyView> {
  return stating<LobbyView, Closing>(closed(table), SENDING, overseeing(admin), closing);
}

/** Clear away every table nobody is at that has sat too long, and answer with the names cleared. */
export function reapTables(admin: string): Promise<string[]> {
  return stating<string[], Record<string, never>>(ADMIN_REAP, SENDING, overseeing(admin), NOTHING);
}

/** The address the closing of one table stands at, which the overseer breaks it up through. */
function closed(table: string): string {
  return `${ADMIN_TABLES}/${encodeURIComponent(table)}/${CLOSING}`;
}
