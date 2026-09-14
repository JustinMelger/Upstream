import js from "@eslint/js";
import ts from "typescript-eslint";
import hooks from "eslint-plugin-react-hooks";
import globals from "globals";
import stylistic from "@stylistic/eslint-plugin";
import simpleImportSort from "eslint-plugin-simple-import-sort";

export default ts.config(
  {
    ignores: [
      "dist",
      "src/lib/api/generated.ts",
      "playwright-report",
      "test-results",
    ],
  },
  js.configs.recommended,
  ...ts.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
    plugins: {
      "react-hooks": hooks,
      "@stylistic": stylistic,
      "simple-import-sort": simpleImportSort,
    },
    rules: {
      ...hooks.configs.recommended.rules,
      "simple-import-sort/imports": "error",
      "one-var": ["error", "never"],
      "@typescript-eslint/consistent-type-imports": [
        "error",
        {
          prefer: "type-imports",
          fixStyle: "inline-type-imports",
          disallowTypeAnnotations: false,
        },
      ],
      "@stylistic/padding-line-between-statements": [
        "error",
        { blankLine: "always", prev: "import", next: "*" },
        { blankLine: "any", prev: "import", next: "import" },
        { blankLine: "always", prev: "*", next: "return" },
        {
          blankLine: "always",
          prev: "*",
          next: ["function", "export", "interface", "type"],
        },
        {
          blankLine: "always",
          prev: ["function", "interface", "type"],
          next: "*",
        },
        { blankLine: "always", prev: "block-like", next: "*" },
        { blankLine: "always", prev: "*", next: "block-like" },
      ],
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_" },
      ],
    },
  },
  { files: ["*.js"], languageOptions: { globals: globals.node } },
);
