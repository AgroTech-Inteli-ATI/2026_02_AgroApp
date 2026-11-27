import { describe, expect, it } from "vitest";
import { verificarHar } from "./verify-har.mjs";

const entrada = (url, extra = {}) => ({
  request: { method: "GET", url, bodySize: 0, ...extra },
  response: { status: 200, _transferSize: 100, content: { mimeType: url.endsWith("/") ? "text/html" : "application/octet-stream" } },
});
const har = (...entries) => ({ log: { entries } });
const app = "https://agro.exemplo/";

describe("verificarHar", () => {
  it("aprova carga só com GET na origem do app e soma os bytes", () => {
    const r = verificarHar(har(entrada(app), entrada(`${app}models/m.tflite`), entrada("blob:https://agro.exemplo/1")), "carga");
    expect(r).toMatchObject({ aprovado: true, requisicoes: 2, bytesTransferidos: 200 });
  });

  it("reprova envio de dados, origem externa e query longa", () => {
    const r = verificarHar(har(
      entrada(app),
      entrada(`${app}upload`, { method: "POST", postData: { text: "foto" } }),
      entrada("https://outro.exemplo/pixel.gif"),
      entrada(`${app}x?d=${"a".repeat(300)}`),
    ), "carga");
    expect(r.aprovado).toBe(false);
    expect(r.problemas.join("\n")).toMatch(/POST.*método que envia dados[\s\S]*com corpo[\s\S]*origem externa[\s\S]*query string longa/);
  });

  it("no diagnóstico, qualquer requisição de rede reprova; blob: não conta", () => {
    expect(verificarHar(har(entrada("blob:https://agro.exemplo/1")), "diagnostico").aprovado).toBe(true);
    expect(verificarHar(har(entrada(`${app}models/m.tflite`)), "diagnostico").aprovado).toBe(false);
  });
});
