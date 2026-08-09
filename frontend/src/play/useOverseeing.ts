import { useCallback, useEffect, useState } from "react";

import type { LobbySetting, LobbyView, Posting } from "../api/admin";
import { closeTable, postTable, readLobby, reapTables, settleLobby } from "../api/admin";
import type { Offering } from "../api/gathering";
import { readOfferings } from "../api/lobby";
import { reasonOf } from "../api/refusal";

/** The lobby as the overseer's panel holds it: how it stands, what may be opened at it, and where a lever failed. */
export interface Overseen {
  lobby: LobbyView | null;
  offerings: Offering[] | null;
  trouble: string | null;
  settle: (setting: LobbySetting) => void;
  close: (table: string, reason: string | null) => void;
  reap: () => void;
  open: (posting: Posting) => void;
}

/**
 * Read and run the lobby as the overseer, behind the token the host was started under.
 *
 * The panel holds no stream: the lobby is read once as it opens and again after every lever the overseer pulls,
 * since a table gathered, broken up or reaped changes what stands and the answer to each of those carries the
 * lobby back. The games the host offers are read alongside, so the overseer opens a table on the same choices a
 * guest plays under.
 *
 * @param admin - the token the panel answers behind, which rides the fragment and reaches every route in a header.
 */
export function useOverseeing(admin: string): Overseen {
  const [lobby, setLobby] = useState<LobbyView | null>(null);
  const [offerings, setOfferings] = useState<Offering[] | null>(null);
  const [trouble, setTrouble] = useState<string | null>(null);

  const stumbled = useCallback((refusal: unknown) => {
    setTrouble(reasonOf(refusal));
  }, []);

  const held = useCallback((view: LobbyView) => {
    setLobby(view);
    setTrouble(null);
  }, []);

  const load = useCallback(() => {
    readLobby(admin).then(held).catch(stumbled);
  }, [admin, held, stumbled]);

  useEffect(() => {
    load();
    readOfferings().then(setOfferings).catch(stumbled);
  }, [load, stumbled]);

  const settle = useCallback(
    (setting: LobbySetting) => {
      setTrouble(null);
      settleLobby(admin, setting).then(held).catch(stumbled);
    },
    [admin, held, stumbled],
  );

  const close = useCallback(
    (table: string, reason: string | null) => {
      setTrouble(null);
      closeTable(admin, table, { reason }).then(held).catch(stumbled);
    },
    [admin, held, stumbled],
  );

  const reap = useCallback(() => {
    setTrouble(null);
    reapTables(admin).then(load).catch(stumbled);
  }, [admin, load, stumbled]);

  const open = useCallback(
    (posting: Posting) => {
      setTrouble(null);
      postTable(admin, posting)
        .then(() => load())
        .catch(stumbled);
    },
    [admin, load, stumbled],
  );

  return { lobby, offerings, trouble, settle, close, reap, open };
}
