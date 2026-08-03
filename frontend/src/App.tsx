import type { ReactElement } from "react";

import { useSeat } from "./play/useSeat";
import { Joining } from "./table/Joining";
import { Table } from "./table/Table";

/** The page: the table the address names, or the way to name one. */
export function App(): ReactElement {
  const seat = useSeat();
  return seat === null ? <Joining /> : <Table seat={seat} />;
}
