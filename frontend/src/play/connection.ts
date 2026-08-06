/** How a client stands with the stream it is following, whether that is a table in play or a table gathering. */
export type Connection = "joining" | "following" | "resuming" | "refused";

/** What a client following a stream says of itself, in the words a person reads. */
export const CONNECTIONS: Record<Connection, string> = {
  joining: "Joining",
  following: "Live",
  resuming: "Reconnecting",
  refused: "Disconnected",
};
