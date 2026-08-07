import { type ReactElement, type SyntheticEvent, useEffect, useState } from "react";

import type { Offering } from "../api/gathering";
import { found, readOfferings } from "../api/lobby";
import { reasonOf } from "../api/refusal";
import { offeringOf } from "../play/choosing";
import { foundingIn } from "../play/founding";
import { arrivedAt } from "../play/useStanding";

/** The longest a name reads at a table, which mirrors `cardserver.schemas.NAME_LONGEST`. */
const NAME_LONGEST = 24;

interface FoundingProps {
  back: () => void;
}

/**
 * How a person opens a table of their own: the name it answers under, their own name, and the game it starts on.
 *
 * Founding a table is arriving at it, so what is stated here is the founder's the moment it goes up: the code is
 * drawn for them, the token minted seats them as the host, and the tab carries over to the gathering the way an
 * arrival does. The company settles the table, the decks and the rest once it gathers, so the founder names the
 * game and leaves the plainest choice it admits standing.
 *
 * The games the host holds the rules of are read out as the arrival reads them, without a credential, so a person
 * opening a table chooses from the same offerings a person joining one plays under.
 */
export function Founding({ back }: FoundingProps): ReactElement {
  const [offerings, setOfferings] = useState<Offering[] | null>(null);
  const [table, setTable] = useState("");
  const [name, setName] = useState("");
  const [game, setGame] = useState("");
  const [trouble, setTrouble] = useState<string | null>(null);
  const [opening, setOpening] = useState(false);

  useEffect(() => {
    let held = true;
    readOfferings()
      .then((offered) => {
        if (held) {
          setOfferings(offered);
          setGame(offered[0]?.game ?? "");
        }
      })
      .catch((refusal: unknown) => {
        if (held) {
          setTrouble(reasonOf(refusal));
        }
      });

    return () => {
      held = false;
    };
  }, []);

  const chosen = offerings ?? [];
  const playing = game === "" ? (chosen[0]?.game ?? "") : game;
  const founding = foundingIn({ table, name, game: playing }, offeringOf(chosen, playing));

  const open = (event: SyntheticEvent): void => {
    event.preventDefault();
    if (founding === null) {
      return;
    }

    setOpening(true);
    setTrouble(null);
    found(founding)
      .then((admitted) => {
        arrivedAt({ table: founding.table, token: admitted.token });
      })
      .catch((refusal: unknown) => {
        setTrouble(reasonOf(refusal));
        setOpening(false);
      });
  };

  return (
    <form className="notice" onSubmit={open}>
      <p>Open a table of your own: name it, name yourself, and choose what it starts on.</p>
      <label>
        Table
        <input value={table} onChange={(event) => setTable(event.target.value)} placeholder="green-baize" />
      </label>
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
        Game
        <select value={playing} disabled={chosen.length === 0} onChange={(event) => setGame(event.target.value)}>
          {chosen.map((offering) => (
            <option key={offering.game} value={offering.game}>
              {offering.title}
            </option>
          ))}
        </select>
      </label>
      {trouble !== null && <p className="trouble">{trouble}</p>}
      <div className="choices">
        <button type="submit" disabled={opening || founding === null}>
          {opening ? "Opening" : "Open the table"}
        </button>
        <button type="button" onClick={back}>
          Join a table instead
        </button>
      </div>
    </form>
  );
}
