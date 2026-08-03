import { type FormEvent, type ReactElement, useState } from "react";

import { takeSeat } from "../play/useSeat";

/**
 * How a tab that was opened at the bare address takes a seat.
 *
 * The host prints one address per seat as it opens a table, so a person joins by opening the line they were
 * handed and reads none of this. It stands for the tab opened without one, and for watching a table whose name
 * is known while its tokens are not.
 */
export function Joining(): ReactElement {
  const [table, setTable] = useState("");
  const [token, setToken] = useState("");

  const join = (event: FormEvent): void => {
    event.preventDefault();
    takeSeat({ table: table.trim(), token: token.trim() === "" ? null : token.trim() });
  };

  return (
    <form className="notice" onSubmit={join}>
      <p>Open the address the table was announced under, or name it here.</p>
      <label>
        Table
        <input value={table} onChange={(event) => setTable(event.target.value)} placeholder="green-baize" />
      </label>
      <label>
        Token
        <input value={token} onChange={(event) => setToken(event.target.value)} placeholder="a seat's own token" />
      </label>
      <button type="submit" disabled={table.trim() === ""}>
        {token.trim() === "" ? "Watch the table" : "Take the seat"}
      </button>
    </form>
  );
}
