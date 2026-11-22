import { useEffect, useRef, useState } from "react";
import styles from "./BenchmarkPanel.module.css";
import { sha256, summarize, type BenchmarkSample, type InitializationMeasurement } from "../lib/benchmark";

interface Props {
  initialization?: InitializationMeasurement;
  offlineReady: boolean;
  run: (file: File, signal: AbortSignal) => Promise<BenchmarkSample>;
  onRunning: (running: boolean) => void;
}
interface Row extends BenchmarkSample { image: number; phase: "warmup" | "measured" }
interface ImageRecord { name: string; bytes: number; type: string; sha256: string }

export function BenchmarkPanel({ initialization, offlineReady, run, onRunning }: Props) {
  const [device, setDevice] = useState("iPhone 13");
  const [os, setOs] = useState("iOS 26.6.2");
  const [browser, setBrowser] = useState("Chrome 158.0.8127.35");
  const [conditions, setConditions] = useState("");
  const [airplane, setAirplane] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [rows, setRows] = useState<Row[]>([]);
  const [report, setReport] = useState<Record<string, unknown>>();
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState("");
  const controller = useRef<AbortController | null>(null);
  const evidence = useRef<Promise<Record<string, unknown>> | null>(null);

  useEffect(() => {
    // Captura a identidade enquanto há rede; sw.js não é armazenado no próprio pré-cache.
    evidence.current = Promise.all([
      fetch(`${import.meta.env.BASE_URL}sw.js`, { signal: AbortSignal.timeout(15_000) }).then(async (response) => {
        if (!response.ok) throw new Error("Service worker indisponível");
        return sha256(await response.arrayBuffer());
      }),
      fetch(`${import.meta.env.BASE_URL}models/manifest.json`, { signal: AbortSignal.timeout(15_000) }).then((response) => {
        if (!response.ok) throw new Error("Manifesto indisponível");
        return response.json();
      }),
    ]).then(([serviceWorkerSha256, manifest]) => ({
      serviceWorkerSha256, manifest,
      scripts: [...document.scripts].map((script) => script.src).filter(Boolean),
    })).catch((error: unknown) => ({ error: String(error) }));
    const hidden = () => {
      if (document.visibilityState !== "visible") controller.current?.abort();
    };
    document.addEventListener("visibilitychange", hidden);
    return () => {
      controller.current?.abort();
      document.removeEventListener("visibilitychange", hidden);
    };
  }, []);
  useEffect(() => {
    if (!initialization) controller.current?.abort();
  }, [initialization]);

  async function start() {
    if (!initialization || running || !files.length) return;
    const abort = new AbortController();
    controller.current = abort;
    setRunning(true); onRunning(true); setRows([]); setReport(undefined);
    const collected: Row[] = [];
    let images: ImageRecord[] = [];
    const startedAt = new Date().toISOString();
    const networkAtStart = navigator.onLine;
    let failure: string | null = null;
    const build = await evidence.current;
    try {
      if (build?.error) throw new Error(`Identidade do build indisponível. Abra o link com rede antes de ativar modo avião: ${build.error}`);
      if (!initialization.model.sha256 || !initialization.model.runtime)
        throw new Error("Recarregue a versão atual: faltam identificação do modelo ou runtime.");
      if (files.some((file) => !["image/jpeg", "image/png", "image/webp"].includes(file.type)
        || !file.size || file.size > 10 * 1024 * 1024))
        throw new Error("Use somente JPEG, PNG ou WebP com até 10 MB por imagem.");
      setMessage("Identificando imagens antes da medição…");
      images = await Promise.all(files.map(async (file) => ({
        name: file.name, bytes: file.size, type: file.type,
        sha256: await sha256(await file.arrayBuffer()),
      })));
      for (let i = 0; i < 53; i++) {
        if (abort.signal.aborted || document.visibilityState !== "visible")
          throw new Error("Coleta interrompida: mantenha a página visível e a tela ligada.");
        const image = i % files.length;
        setMessage(i < 3 ? `Aquecimento ${i + 1}/3` : `Medição ${i - 2}/50`);
        const sample = await run(files[image], abort.signal);
        if (abort.signal.aborted) throw new Error("Coleta interrompida.");
        collected.push({ ...sample, image, phase: i < 3 ? "warmup" : "measured" });
        setRows([...collected]);
      }
    } catch (error) {
      failure = error instanceof Error ? error.message : String(error);
    } finally {
      const measured = collected.filter((row) => row.phase === "measured");
      setReport({
        schema: "agroapp-benchmark-browser-v1", startedAt, finishedAt: new Date().toISOString(),
        complete: !failure && measured.length === 50, failure,
        device, os, browser, conditions, airplaneModeDeclared: airplane,
        navigatorOnlineStart: networkAtStart, navigatorOnlineEnd: navigator.onLine,
        offlineCacheReady: offlineReady, userAgent: navigator.userAgent,
        hardwareConcurrency: navigator.hardwareConcurrency, crossOriginIsolated,
        delegate: "LiteRT.js default; internal CPU delegate not exposed by application API",
        deviceMetadataSource: "User-declared; userAgent recorded separately",
        location: location.origin + location.pathname,
        initialization, build, productionBuild: import.meta.env.PROD, images, samples: collected,
        percentiles: "linear interpolation, index=(n-1)*p; milliseconds; excludes 3 warmups",
        summary: summarize(measured),
        boundaries: {
          workerToReadyMs: "Worker creation to ready; downloads/cache, compile and synthetic warmup included",
          navigationToReadyMs: "Navigation time origin to ready; not OS process cold start",
          inferenceMs: "LiteRT.js run + await output.data; excludes postprocessing and UI",
          fileToPaintMs: "File available in app to double requestAnimationFrame after React commit; paint approximation, excludes native camera/shutter/file picker and image preview decoding",
        },
        proposedLimits: { inferenceP95Ms: 300, fileToPaintP95Ms: 3000,
          status: "Not partner-ratified; browser is not native Benchmark Tool; file-to-paint is not shutter-to-result" },
      });
      controller.current = null; setRunning(false); onRunning(false);
      setMessage(failure ? `Coleta parcial: ${failure}` : "50 medições concluídas. Exporte o JSON.");
    }
  }
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2) + "\n"], { type: "application/json" }));
    const anchor = document.createElement("a"); anchor.href = url;
    anchor.download = `benchmark-${new Date().toISOString().replace(/[:.]/g, "-")}.json`;
    anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 10_000);
  }
  return <section aria-label="Benchmark no dispositivo" className={styles.panel}>
    <h2>Benchmark no dispositivo</h2>
    <p>3 aquecimentos + 50 análises pelo fluxo real. Fotos permanecem neste aparelho. Mantenha a tela ligada e esta aba visível.</p>
    <fieldset disabled={running} className={styles.fields}>
      <label>Aparelho <input value={device} onChange={(e) => setDevice(e.target.value)} /></label>
      <label>Sistema <input value={os} onChange={(e) => setOs(e.target.value)} /></label>
      <label>Navegador <input value={browser} onChange={(e) => setBrowser(e.target.value)} /></label>
      <label>Condições (bateria, economia de energia, temperatura, cache e rede) <textarea value={conditions} onChange={(e) => setConditions(e.target.value)} /></label>
      <label className={styles.check}><input type="checkbox" checked={airplane} onChange={(e) => setAirplane(e.target.checked)} /> Modo avião ativo e Wi-Fi desligado (confirmação manual)</label>
      <label>Imagens para benchmark <input type="file" multiple accept="image/jpeg,image/png,image/webp" onChange={(e) => setFiles(Array.from(e.target.files ?? []))} /></label>
      <button type="button" disabled={!initialization || !files.length || !device.trim() || !os.trim() || !browser.trim() || !conditions.trim()} onClick={() => void start()}>Iniciar 50 medições</button>
    </fieldset>
    <p>Cache offline: {offlineReady ? "pronto" : "aguardando"}. {initialization ? `Modelo: ${initialization.model.format}; ${initialization.model.accelerator}. Inicialização: ${Math.round(initialization.workerToReadyMs)} ms.` : "Aguardando modelo."}</p>
    {running && <button type="button" onClick={() => controller.current?.abort()}>Interromper coleta</button>}
    <p role="status">{message}</p>
    <p>{rows.filter((row) => row.phase === "measured").length}/50 medições registradas.</p>
    {report && <><button type="button" onClick={download}>Exportar JSON do benchmark</button><pre className={styles.summary}>{JSON.stringify(report.summary, null, 2)}</pre></>}
    <p>O tempo total começa quando o arquivo chega à aplicação, excluindo a captura nativa. Limites propostos: inferência p95 ≤ 300 ms e fluxo p95 ≤ 3 s; comparação parcial, sem aprovação automática.</p>
  </section>;
}
