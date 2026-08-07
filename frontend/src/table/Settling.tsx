import type { ReactElement } from "react";

import type { Choice, GatheringView, Offering } from "../api/gathering";
import { endingRead, offeringOf, runningTo, seatingsOf, settledOn } from "../play/choosing";
import { hasSay, iAmHost } from "../play/company";

/** The most rounds a company sets a match to run for, which is where the counts a control lists stop. */
const ROUNDS_MOST = 10;

/** The round counts a match may be set to run for. */
const ROUND_COUNTS = [...Array(ROUNDS_MOST).keys()].map((step) => step + 1);

/** What a guest holding no seat is told, since the players of the game are the ones who settle it. */
const TOLD = "Take a seat to settle what is played";

/** How the host reads the say they are handing out or keeping, which is the whole of the governance toggle. */
const GOVERNANCE = "Everyone at the table may change the settings";

interface SettlingProps {
  gathering: GatheringView;
  offerings: Offering[];
  settle: (choice: Choice) => void;
  govern: (democratic: boolean) => void;
}

/**
 * What the table plays, settled out of what the host says it offers.
 *
 * Every control here is drawn from an `Offering`, so the page lists the games this host holds the rules of, the
 * tables each of them seats and the counts of decks each is dealt from while holding the name of none. A game
 * that admits one count of decks offers no choice of them at all.
 *
 * Settling is for the guests holding seats, which the server answers for itself: a guest standing by reads the
 * choice and is told as much. How the table is governed stands here too, as the host's own to settle: the toggle
 * hands the say to the whole table or keeps it to the host, and it shows for the host alone.
 */
export function Settling({ gathering, offerings, settle, govern }: SettlingProps): ReactElement {
  const { choice } = gathering;
  const offering = offeringOf(offerings, choice.game);
  const saying = hasSay(gathering);
  const hosting = iAmHost(gathering);

  return (
    <div className="settling">
      <label>
        Game
        <select
          value={choice.game}
          disabled={!saying}
          onChange={(event) => {
            settleOnto(offerings, choice, event.target.value, settle);
          }}
        >
          {offerings.map((offered) => (
            <option key={offered.game} value={offered.game}>
              {offered.title}
            </option>
          ))}
        </select>
      </label>
      <label>
        Players
        <select
          value={choice.players}
          disabled={!saying || offering === null}
          onChange={(event) => {
            settle({ ...choice, players: Number(event.target.value) });
          }}
        >
          {(offering === null ? [choice.players] : seatingsOf(offering)).map((players) => (
            <option key={players} value={players}>
              {players}
            </option>
          ))}
        </select>
      </label>
      {offering !== null && offering.decks.length > 1 && (
        <label>
          Decks
          <select
            value={choice.decks}
            disabled={!saying}
            onChange={(event) => {
              settle({ ...choice, decks: Number(event.target.value) });
            }}
          >
            {offering.decks.map((decks) => (
              <option key={decks} value={decks}>
                {decks}
              </option>
            ))}
          </select>
        </label>
      )}
      <label>
        Rounds
        <select
          value={choice.conclusion.rounds ?? ""}
          disabled={!saying}
          onChange={(event) => {
            settle(runningTo(choice, Number(event.target.value)));
          }}
        >
          <option value="" disabled>
            {endingRead(choice.conclusion)}
          </option>
          {ROUND_COUNTS.map((rounds) => (
            <option key={rounds} value={rounds}>
              {rounds}
            </option>
          ))}
        </select>
      </label>
      <p className="ending">Runs to {endingRead(choice.conclusion)}</p>
      {hosting && (
        <label className="governance">
          <input type="checkbox" checked={gathering.democratic} onChange={(event) => govern(event.target.checked)} />
          {GOVERNANCE}
        </label>
      )}
      {!saying && <p className="told">{TOLD}</p>}
    </div>
  );
}

/** The choice carried onto another game, at the table and the decks that game admits. */
function settleOnto(offerings: Offering[], choice: Choice, game: string, settle: (choice: Choice) => void): void {
  const offering = offeringOf(offerings, game);
  if (offering !== null) {
    settle(settledOn(choice, offering));
  }
}
