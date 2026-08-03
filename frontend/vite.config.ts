import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";
import { parse } from "yaml";

const CONFIGURATION = fileURLToPath(new URL("../config.yaml", import.meta.url));
const ENDPOINTS = "/tables";

interface Service {
  host: string;
  port: number;
}

interface Configuration {
  service: Service;
}

/**
 * Where the table answers, read from the one file a run is configured by.
 *
 * A development server holds the page and the table apart, so the two are made one origin by passing the
 * endpoints through. Reading the address here leaves `config.yaml` the single place it is stated, which is
 * what lets a table opened on another port be reached by a page already running.
 */
function served(): string {
  const configuration: Configuration = parse(readFileSync(CONFIGURATION, "utf-8"));
  return `http://${configuration.service.host}:${configuration.service.port}`;
}

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      [ENDPOINTS]: { target: served(), changeOrigin: true },
    },
  },
  test: {
    include: ["tests/**/*.test.ts?(x)"],
    environment: "node",
  },
});
