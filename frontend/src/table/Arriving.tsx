import { type ReactElement, type SyntheticEvent, useState } from "react";

import { arrive } from "../api/lobby";
import { reasonOf } from "../api/refusal";
import { arrivalIn } from "../play/arriving";
import { ranksIn, readOut } from "../play/codes";
import { arrivedAt, leave } from "../play/useStanding";
import { Founding } from "./Founding";

/** The longest a name reads at a table, which mirrors `cardserver.schemas.NAME_LONGEST`. */
const NAME_LONGEST = 24;

interface ArrivingProps {
  table: string | null;
  code: string | null;
  tables: string[] | null;
}

/**
 * How a person arrives at a table: the table, the code that admits them, and the name the company reads them by.
 *
 * The whole of an arrival is stated here at once. The address a host announces carries the table and the code, so
 * a guest opening the line they were handed names themselves and nothing more; a tab opened at the bare address
 * is offered the tables gathering, the one a host usually holds already chosen, and names a table itself where
 * the host answers none. A person who was handed no line may open a table of their own from here instead, which
 * seats them as its host.
 *
 * A code is what one person says and another writes down — spaced, hyphenated or in lower case, all of them the
 * same hand of ranks. What is typed reads back rank by rank, and the arrival goes up once a table, a whole code
 * and a name stand together.
 *
 * The token the arrival mints goes into the address in the code's place, so a reload rejoins as the same guest
 * and no name is asked again.
 */
export function Arriving({ table, code, tables }: ArrivingProps): ReactElement {
  const [stated, setStated] = useState(table ?? "");
  const [name, setName] = useState("");
  const [offered, setOffered] = useState(code ?? "");
  const [trouble, setTrouble] = useState<string | null>(null);
  const [knocking, setKnocking] = useState(false);
  const [founding, setFounding] = useState(false);

  const gathering = tables ?? [];
  const joining = stated === "" ? (gathering[0] ?? "") : stated;
  const arrival = arrivalIn({ table: joining, code: offered, name });

  if (founding) {
    return <Founding back={() => setFounding(false)} />;
  }

  const knock = (event: SyntheticEvent): void => {
    event.preventDefault();
    if (arrival === null) {
      return;
    }

    setKnocking(true);
    setTrouble(null);
    arrive(arrival.table, { code: arrival.code, name: arrival.name })
      .then((admitted) => {
        arrivedAt({ table: arrival.table, token: admitted.token });
      })
      .catch((refusal: unknown) => {
        setTrouble(reasonOf(refusal));
        setKnocking(false);
      });
  };

  return (
    <form className="notice" onSubmit={knock}>
      {table === null ? (
        <p>Name the table gathering here, yourself, and the code that admits you.</p>
      ) : (
        <p>
          Table <strong>{table}</strong> is gathering. Name yourself to join the company.
        </p>
      )}
      {table === null && (
        <label>
          Table
          {gathering.length === 0 ? (
            <input value={joining} onChange={(event) => setStated(event.target.value)} placeholder="green-baize" />
          ) : (
            <select value={joining} onChange={(event) => setStated(event.target.value)}>
              {gathering.map((one) => (
                <option key={one} value={one}>
                  {one}
                </option>
              ))}
            </select>
          )}
        </label>
      )}
      <label>
        Name
        <input
          value={name}
          maxLength={NAME_LONGEST}
          onChange={(event) => setName(event.target.value)}
          placeholder="what the table calls you"
        />
      </label>
      <label>
        Code
        <input value={offered} onChange={(event) => setOffered(event.target.value)} placeholder="a hand of six ranks" />
      </label>
      {ranksIn(offered) !== null && <p className="reading">{readOut(offered)}</p>}
      {trouble !== null && <p className="trouble">{trouble}</p>}
      <div className="choices">
        <button type="submit" disabled={knocking || arrival === null}>
          {knocking ? "Arriving" : "Arrive at the table"}
        </button>
        {table === null && (
          <button type="button" onClick={() => setFounding(true)}>
            Open a new table
          </button>
        )}
        {table !== null && (
          <button type="button" onClick={leave}>
            Name another table
          </button>
        )}
      </div>
    </form>
  );
}
