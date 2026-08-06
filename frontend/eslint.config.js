import js from "@eslint/js";
import a11y from "eslint-plugin-jsx-a11y";
import react from "eslint-plugin-react";
import hooks from "eslint-plugin-react-hooks";
import sorting from "eslint-plugin-simple-import-sort";
import globals from "globals";
import typescript from "typescript-eslint";

/*
 * What the page is held to, which is the standard the Python beside it answers.
 *
 * The type-aware rules are the point of it: reading a whole program is what lets a linter say the kind of
 * thing pylint says. Three of the rules below carry over from the guidelines the Python follows — an import
 * block in a settled order, a signature stating its types, and a figure given a name where it means something
 * — and the rest widen a default, since a number read into a sentence and a handler answering with nothing
 * are both ordinary here.
 *
 * Generated code is read rather than written, so the schema the endpoints publish is left as it arrives.
 */
const SOURCES = ["**/*.{js,ts,tsx}"];
const HARNESS = ["tests/**/*.{ts,tsx}", "vite.config.ts"];
const CONFIGURATION = ["**/*.js"];

/** The figures that carry their meaning in themselves, which are the counts a step is taken in. */
const PLAIN_FIGURES = [-1, 0, 1];

export default typescript.config(
  { ignores: ["dist/**", "src/api/schema.ts"] },
  js.configs.recommended,
  ...typescript.configs.strictTypeChecked,
  ...typescript.configs.stylisticTypeChecked,
  react.configs.flat.recommended,
  react.configs.flat["jsx-runtime"],
  hooks.configs.flat["recommended-latest"],
  a11y.flatConfigs.recommended,
  {
    files: SOURCES,
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
      globals: globals.browser,
    },
    settings: { react: { version: "detect" } },
    plugins: { "simple-import-sort": sorting },
    rules: {
      "simple-import-sort/imports": "error",
      "simple-import-sort/exports": "error",
      "@typescript-eslint/explicit-function-return-type": ["error", { allowExpressions: true }],
      "@typescript-eslint/consistent-type-imports": ["error", { fixStyle: "separate-type-imports" }],
      "@typescript-eslint/no-magic-numbers": [
        "error",
        { ignore: PLAIN_FIGURES, ignoreArrayIndexes: true, ignoreEnums: true, ignoreReadonlyClassProperties: true },
      ],
      "@typescript-eslint/no-confusing-void-expression": ["error", { ignoreArrowShorthand: true }],
      "@typescript-eslint/restrict-template-expressions": ["error", { allowNumber: true }],
      curly: "error",
      eqeqeq: ["error", "always"],
      "no-console": "error",
    },
  },
  {
    // These answer with whatever they read and send whatever they are handed, and naming the shape once is the
    // whole of what they do with it: the schema either side is held to is the caller's to state.
    files: ["src/api/parsing.ts", "src/api/requests.ts"],
    rules: { "@typescript-eslint/no-unnecessary-type-parameters": "off" },
  },
  {
    files: HARNESS,
    languageOptions: { globals: globals.node },
    rules: { "@typescript-eslint/no-magic-numbers": "off" },
  },
  {
    files: CONFIGURATION,
    extends: [typescript.configs.disableTypeChecked],
    languageOptions: { globals: globals.node },
    rules: { "@typescript-eslint/no-magic-numbers": "off" },
  },
);
