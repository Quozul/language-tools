import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: [
      {
        find: "@qzl/ui",
        replacement: path.resolve(import.meta.dirname, "../../packages/ui/src"),
      },
      { find: "@", replacement: path.resolve(import.meta.dirname) },
      {
        find: "server-only",
        replacement: path.resolve(
          import.meta.dirname,
          "tests/stubs/server-only.ts",
        ),
      },
    ],
  },
  test: {
    environment: "node",
    include: ["lib/**/*.test.ts", "components/**/*.test.ts"],
    exclude: ["node_modules/**", ".next/**"],
  },
});
