// T12.3: confere um HAR exportado do DevTools (celular via chrome://inspect ou Playwright).
//   node scripts/verify-har.mjs carga.har --fase carga
//   node scripts/verify-har.mjs diagnostico.har --fase diagnostico
// Carga: nenhuma requisição envia dados e todas vão à origem do app; resume os bytes baixados.
// Diagnóstico: além disso, nenhuma requisição de rede pode acontecer.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const LOCAL = /^(blob|data|chrome-extension):/;

export function verificarHar(har, fase) {
  if (!["carga", "diagnostico"].includes(fase)) throw new Error(`fase inválida: ${fase}`);
  const entradas = (har?.log?.entries ?? []).filter((e) => !LOCAL.test(e.request.url));
  const documento = entradas.find((e) => e.response?.content?.mimeType?.includes("text/html"));
  const origem = documento ? new URL(documento.request.url).origin : undefined;
  const problemas = [];
  for (const { request } of entradas) {
    const url = new URL(request.url);
    if (!["GET", "HEAD"].includes(request.method))
      problemas.push(`${request.method} ${request.url}: método que envia dados`);
    if (request.postData?.text || request.postData?.params?.length || (request.bodySize ?? 0) > 0)
      problemas.push(`${request.url}: requisição com corpo`);
    if (url.search.length > 256) problemas.push(`${request.url}: query string longa`);
    if (origem && url.origin !== origem) problemas.push(`${request.url}: origem externa ao app`);
  }
  if (fase === "diagnostico")
    for (const { request } of entradas) problemas.push(`${request.method} ${request.url}: rede usada durante o diagnóstico`);
  // _transferSize (Chrome/Playwright) é o tráfego real; bodySize é o fallback do HAR 1.2.
  const bytes = (e) => Math.max(0, e.response?._transferSize ?? e.response?.bodySize ?? 0);
  const porArquivo = entradas.map((e) => ({ url: new URL(e.request.url).pathname, status: e.response?.status, bytes: bytes(e) }));
  return {
    fase,
    origem: origem ?? null,
    requisicoes: entradas.length,
    bytesTransferidos: porArquivo.reduce((soma, a) => soma + a.bytes, 0),
    maiores: [...porArquivo].sort((a, b) => b.bytes - a.bytes).slice(0, 10),
    problemas,
    aprovado: problemas.length === 0,
  };
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [arquivo, flag, fase] = process.argv.slice(2);
  if (!arquivo || flag !== "--fase") {
    console.error("Uso: node scripts/verify-har.mjs <arquivo.har> --fase carga|diagnostico");
    process.exit(2);
  }
  const resultado = verificarHar(JSON.parse(readFileSync(arquivo, "utf8")), fase);
  console.log(JSON.stringify(resultado, null, 2));
  process.exit(resultado.aprovado ? 0 : 1);
}
