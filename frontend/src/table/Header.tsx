import type { ReactElement } from "react";

import type { Layout } from "../api/layout";
import type { PositionView } from "../api/views";
import { Plaque } from "./Plaque";

interface HeaderProps {
  layout: Layout;
  view: PositionView;
}

/** The standing of the whole table in one row across the top: the game, and every seat playing it. */
export function Header({ layout, view }: HeaderProps): ReactElement {
  return (
    <header className="standing">
      <h1 className="title">{layout.title}</h1>
      <div className="plaques">
        {layout.plaques.map((plaque) => (
          <Plaque key={plaque.seat} plaque={plaque} layout={layout} view={view} />
        ))}
      </div>
    </header>
  );
}
