import js from "@eslint/js";
import globals from "globals";
import pluginReact from "eslint-plugin-react";

export default [
  { startsWithIgnored: true, ignores: ["dist", "node_modules"] },
  js.configs.recommended,
  { files: ["**/*.{js,mjs,cjs,jsx}"], languageOptions: { globals: globals.browser } },
  {
    ...pluginReact.configs.flat.recommended,
    rules: {
      "react/prop-types": "off",
      "react/react-in-jsx-scope": "off"
    }
  },
];
