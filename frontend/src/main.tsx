import "./styles.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";

const MOUNT = "table";

const mount = document.getElementById(MOUNT);
if (mount === null) {
  throw new Error(`The page holds no element named ${MOUNT} for the table to be drawn in`);
}

createRoot(mount).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
