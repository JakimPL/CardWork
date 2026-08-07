import { type ReactElement, type SyntheticEvent, useState } from "react";

import type { Creation, LobbySetting, LobbyView, Posting, TableCard } from "../api/admin";
import type { Offering } from "../api/gathering";
import { offeringOf } from "../play/choosing";
import { foundingChoiceFor } from "../play/founding";
import { useOverseeing } from "../play/useOverseeing";
import { leave } from "../play/useStanding";

/** What the capacity reads as where the lobby holds as many tables as ask, which mirrors the server's `NO_LIMIT`. */
const NO_LIMIT = 0;

/** The ways a lobby may be held open, each the word the overseer settles it under. */
const CREATIONS: Creation[] = ["self-serve", "admin-only", "hybrid"];

interface OverseeingProps {
  admin: string;
}

/**
 * The overseer's panel: every table the lobby holds, the terms it holds them under, and the levers over both.
 *
 * The panel answers behind the admin token alone, which no guest holds, so what stands here is the whole lobby
 * rather than one table: the tables gathering and in play alike, the count against the cap, and who may open one.
 * The overseer settles those terms, opens a table on the company's behalf, breaks one up, and clears away the
 * stale, and the lobby is read afresh after each so the panel reads as the lobby stands.
 */
export function Overseeing({ admin }: OverseeingProps): ReactElement {
  const { lobby, offerings, trouble, settle, close, reap, open } = useOverseeing(admin);

  return (
    <div className="notice overseeing">
      <p className="gathered">Overseeing the lobby</p>
      {lobby === null ? (
        <p>Reading the lobby.</p>
      ) : (
        <>
          <Terms lobby={lobby} settle={settle} />
          <Tables tables={lobby.tables} close={close} />
          <Opening offerings={offerings} open={open} />
          <div className="choices">
            <button type="button" onClick={reap}>
              Reap the stale tables
            </button>
            <button type="button" onClick={leave}>
              Leave the panel
            </button>
          </div>
        </>
      )}
      {trouble !== null && <p className="trouble">{trouble}</p>}
    </div>
  );
}

interface TermsProps {
  lobby: LobbyView;
  settle: (setting: LobbySetting) => void;
}

/** The terms the lobby is held under, each the overseer's to settle: who may open a table, and how many stand. */
function Terms({ lobby, settle }: TermsProps): ReactElement {
  return (
    <div className="terms">
      <label>
        Who may open a table
        <select
          value={lobby.creation}
          onChange={(event) => {
            const chosen = CREATIONS.find((creation) => creation === event.target.value);
            if (chosen !== undefined) {
              settle({ creation: chosen });
            }
          }}
        >
          {CREATIONS.map((creation) => (
            <option key={creation} value={creation}>
              {creation}
            </option>
          ))}
        </select>
      </label>
      <label>
        Tables at once
        <input
          type="number"
          min={NO_LIMIT}
          value={lobby.capacity}
          onChange={(event) => settle({ capacity: Number(event.target.value) })}
        />
      </label>
      <p className="census">
        {lobby.census} standing of {lobby.capacity === NO_LIMIT ? "no limit" : lobby.capacity}
      </p>
    </div>
  );
}

interface TablesProps {
  tables: TableCard[];
  close: (table: string, reason: string | null) => void;
}

/** Every table the lobby holds, gathering and in play alike, each with the press that breaks it up. */
function Tables({ tables, close }: TablesProps): ReactElement {
  if (tables.length === 0) {
    return <p className="empty">No table stands at the lobby.</p>;
  }

  return (
    <ul className="tables">
      {tables.map((card) => (
        <li key={card.table} className="table-card">
          <span className="name">{card.table}</span>
          <span className="phase">{card.phase}</span>
          <span className="seats">
            {presentAt(card)}/{card.seats}
          </span>
          <span className="idle">idle {Math.round(card.idle)}s</span>
          {card.host !== null && card.host !== undefined && <span className="host">{card.host}</span>}
          <button type="button" onClick={() => close(card.table, null)}>
            Close
          </button>
        </li>
      ))}
    </ul>
  );
}

interface OpeningProps {
  offerings: Offering[] | null;
  open: (posting: Posting) => void;
}

/** The overseer opening a table on the company's behalf: the name it answers under, and the game it starts on. */
function Opening({ offerings, open }: OpeningProps): ReactElement {
  const [table, setTable] = useState("");
  const [game, setGame] = useState("");
  const chosen = offerings ?? [];
  const playing = game === "" ? (chosen[0]?.game ?? "") : game;
  const offering = offeringOf(chosen, playing);
  const named = table.trim();

  const post = (event: SyntheticEvent): void => {
    event.preventDefault();
    if (offering === null || named === "") {
      return;
    }

    open({ table: named, choice: foundingChoiceFor(offering) });
    setTable("");
  };

  return (
    <form className="opening" onSubmit={post}>
      <label>
        Table
        <input value={table} onChange={(event) => setTable(event.target.value)} placeholder="green-baize" />
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
      <button type="submit" disabled={offering === null || named === ""}>
        Open the table
      </button>
    </form>
  );
}

/** How many of a gathering's company are present, and a dash for a table in play whose seats stand apart from this. */
function presentAt(card: TableCard): string {
  return card.present === null || card.present === undefined ? "—" : String(card.present);
}
