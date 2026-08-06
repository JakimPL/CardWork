import { type ReactElement, type SyntheticEvent, useState } from "react";

import { standAt } from "../play/useStanding";

/**
 * How a tab that was opened at the bare address reaches a table.
 *
 * The host prints the address of the table it gathers, so a person joins by opening the line they were handed
 * and reads none of this. It stands for the tab opened without one, and the code may be left for the arrival
 * to ask for.
 */
export function Joining(): ReactElement {
  const [table, setTable] = useState("");
  const [code, setCode] = useState("");

  const join = (event: SyntheticEvent): void => {
    event.preventDefault();
    standAt(table.trim(), code.trim() === "" ? null : code.trim());
  };

  return (
    <form className="notice" onSubmit={join}>
      <p>Open the address the table was announced under, or name it here.</p>
      <label>
        Table
        <input value={table} onChange={(event) => setTable(event.target.value)} placeholder="green-baize" />
      </label>
      <label>
        Code
        <input value={code} onChange={(event) => setCode(event.target.value)} placeholder="a hand of six ranks" />
      </label>
      <button type="submit" disabled={table.trim() === ""}>
        Reach the table
      </button>
    </form>
  );
}
