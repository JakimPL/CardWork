import type { ReactElement } from "react";
import { useEffect, useState } from "react";

import { readOut } from "../play/codes";
import { copied } from "../play/copying";
import { invitationTo } from "../play/joining";

/** What the code stands under, since it is the one thing a guest passes on by saying it aloud. */
const CODE = "Join code";

/** What the press reads: the offer, the word that the line was taken, and what stands where it was not. */
const COPY = "Copy invitation";
const TAKEN = "Copied ✓";
const BY_HAND = "Copy this line";

/** How long the press keeps its word before it offers the line again. */
const HELD = 2000;

interface InvitationProps {
  table: string;
  code: string;
}

/**
 * The code this table gathers on, and the line that carries somebody else to it.
 *
 * The code is read out rank by rank, since a guest at the table passes it on by saying it, and the press beside
 * it takes the whole address instead, which is what one person sends another. Where the clipboard is closed to
 * the page the line appears in a field of its own, selected and ready to be taken by hand.
 */
export function Invitation({ table, code }: InvitationProps): ReactElement {
  const [reading, setReading] = useState(COPY);
  const [line, setLine] = useState<string | null>(null);

  useEffect(() => {
    if (reading !== TAKEN) {
      return undefined;
    }

    const held = setTimeout(() => {
      setReading(COPY);
    }, HELD);
    return () => {
      clearTimeout(held);
    };
  }, [reading]);

  async function hand(): Promise<void> {
    const address = invitationTo(table, code, window.location);
    const taken = await copied(address);
    setReading(taken ? TAKEN : BY_HAND);
    setLine(taken ? null : address);
  }

  return (
    <div className="code">
      <span>
        {CODE} <strong>{readOut(code)}</strong>
      </span>
      <button
        type="button"
        className="invite"
        onClick={() => {
          void hand();
        }}
      >
        {reading}
      </button>
      {line !== null && (
        <input
          className="line"
          type="text"
          readOnly
          value={line}
          ref={(field) => {
            field?.select();
          }}
        />
      )}
    </div>
  );
}
