import { type ReactElement, type SyntheticEvent, useState } from "react";

import { arrive } from "../api/lobby";
import { reasonOf } from "../api/refusal";
import { codeIn, ranksIn, readOut } from "../play/codes";
import { arrivedAt, leave } from "../play/useStanding";

/** The longest a name reads at a table, which mirrors `cardserver.schemas.NAME_LONGEST`. */
const NAME_LONGEST = 24;

interface ArrivingProps {
  table: string;
  code: string | null;
}

/**
 * How a person arrives at a table: the name the company will read them by, and the code that admits them.
 *
 * The address the host announced carries the code, so a guest opening the line they were handed offers a name
 * and nothing else. A tab that reached the table another way asks for the code as well, which is what one
 * person says and another writes down — spaced, hyphenated or in lower case, all of them the same hand of ranks.
 * What is typed reads back rank by rank, and the arrival goes up once a whole code stands there.
 *
 * The token the arrival mints goes into the address in the code's place, so a reload rejoins as the same guest
 * and no name is asked again.
 */
export function Arriving({ table, code }: ArrivingProps): ReactElement {
  const [name, setName] = useState("");
  const [offered, setOffered] = useState(code ?? "");
  const [trouble, setTrouble] = useState<string | null>(null);
  const [knocking, setKnocking] = useState(false);

  const knock = (event: SyntheticEvent): void => {
    event.preventDefault();
    setKnocking(true);
    setTrouble(null);
    arrive(table, { code: offered.trim(), name: name.trim() })
      .then((admitted) => {
        arrivedAt({ table, token: admitted.token });
      })
      .catch((refusal: unknown) => {
        setTrouble(reasonOf(refusal));
        setKnocking(false);
      });
  };

  return (
    <form className="notice" onSubmit={knock}>
      <p>
        Table <strong>{table}</strong> is gathering. Name yourself to join the company.
      </p>
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
        <button type="submit" disabled={knocking || name.trim() === "" || codeIn(offered) === null}>
          {knocking ? "Arriving" : "Arrive at the table"}
        </button>
        <button type="button" onClick={leave}>
          Name another table
        </button>
      </div>
    </form>
  );
}
