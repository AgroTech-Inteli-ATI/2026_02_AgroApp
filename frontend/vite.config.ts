import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import { createHash } from "node:crypto";
import { readFile, readdir, writeFile } from "node:fs/promises";
import path from "node:path";

// T9.4: gera dist/sw.js com a lista de arquivos do build para pré-carregar offline.
function offlineCache(): Plugin {
  let outDir = "";
  return {
    name: "agroapp-offline-cache",
    apply: "build",
    configResolved: (config) => void (outDir = config.build.outDir),
    async closeBundle() {
      const manifest = JSON.parse(
        await readFile(path.join(outDir, "models/manifest.json"), "utf8"),
      ) as { models: { filename: string }[] };
      const used = new Set(manifest.models.map((m) => `models/${m.filename}`));
      const files = (await readdir(outDir, { recursive: true, withFileTypes: true }))
        .filter((entry) => entry.isFile())
        .map((entry) =>
          path.relative(outDir, path.join(entry.parentPath, entry.name)).replaceAll("\\", "/"),
        )
        // Fica de fora só o que o app nunca pede: o próprio sw.js, procedência e modelos fora do manifesto.
        .filter(
          (file) =>
            file !== "sw.js" &&
            !file.endsWith(".md") &&
            (!file.endsWith(".tflite") || used.has(file)),
        )
        .map((file) => (file === "index.html" ? "./" : file))
        .sort();
      const hash = createHash("sha256");
      for (const file of files)
        hash.update(file).update(await readFile(path.join(outDir, file === "./" ? "index.html" : file)));
      const template = await readFile(path.resolve("scripts/sw.js"), "utf8");
      await writeFile(
        path.join(outDir, "sw.js"),
        template
          .replace("__VERSION__", hash.digest("hex").slice(0, 16))
          .replace("__FILES__", JSON.stringify(files)),
      );
    },
  };
}

export default defineConfig({
  plugins: [react(), offlineCache()],
  base: process.env.VITE_BASE_PATH || "/",
  worker: { format: "es" },
  server: {
    watch: { ignored: ["**/public/runtime/**", "**/public/models/**"] },
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp",
    },
  },
  preview: {
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp",
    },
  },
});
