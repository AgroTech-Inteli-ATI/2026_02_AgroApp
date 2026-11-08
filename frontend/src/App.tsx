import { useEffect, useRef, useState, type ChangeEvent } from "react";
import {
  ArrowRight,
  BookOpen,
  Camera,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  Clock3,
  ImagePlus,
  Info,
  Leaf,
  LoaderCircle,
  Maximize,
  ScanLine,
  ShieldCheck,
  Sprout,
  Upload,
  X,
} from "lucide-react";
import { technicalContent } from "./data/content";
import type {
  AnalysisResult,
  ClassLabel,
  ModelInfo,
  WorkerRequest,
  WorkerResponse,
} from "./types";
import styles from "./App.module.css";

const base = import.meta.env.BASE_URL;
const percent = (value: number) =>
  new Intl.NumberFormat("pt-BR", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
const milliseconds = (value: number) =>
  `${Math.round(value).toLocaleString("pt-BR")} ms`;
const splitLabel = (name: string) => {
  const split = name.indexOf(" (");
  return split < 0
    ? { common: name, scientific: "" }
    : { common: name.slice(0, split), scientific: name.slice(split + 2, -1) };
};

export default function App() {
  const [tab, setTab] = useState<"analysis" | "classes">("analysis");
  const [labels, setLabels] = useState<ClassLabel[]>([]);
  const [model, setModel] = useState<ModelInfo>();
  const [status, setStatus] = useState("Carregando o modelo…");
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [file, setFile] = useState<File>();
  const [original, setOriginal] = useState("");
  const [preview, setPreview] = useState("");
  const [showPrepared, setShowPrepared] = useState(false);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [result, setResult] = useState<AnalysisResult>();
  const [selectedClass, setSelectedClass] = useState<number>();
  const [retryCount, setRetryCount] = useState(0);
  const worker = useRef<Worker | null>(null);
  const request = useRef(0);
  const urls = useRef({ original: "", preview: "" });
  const input = useRef<HTMLInputElement>(null);
  const cameraInput = useRef<HTMLInputElement>(null);
  const help = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${base}models/manifest.json`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Catálogo indisponível");
        return response.json();
      })
      .then((manifest) => setLabels(manifest.classes))
      .catch(() => {});
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (typeof Worker === "undefined") {
      setLoadError(
        "Este navegador não oferece o processamento necessário. Use Chrome ou Edge atualizado.",
      );
      return;
    }
    setLoadError("");
    setModel(undefined);
    setStatus("Carregando o modelo…");
    const instance = new Worker(`${base}runtime/inference.js`);
    worker.current = instance;
    instance.onmessage = (event: MessageEvent<WorkerResponse>) => {
      const message = event.data;
      if (message.type === "status") setStatus(message.message);
      if (message.type === "ready") {
        setModel(message.info);
        setStatus("Pronto para analisar");
      }
      if (message.type === "error") {
        if (message.id === undefined) {
          setLoadError(message.message);
          setBusy(false);
        } else if (message.id === request.current) {
          setError(message.message);
          setBusy(false);
        }
      }
      // Guarda as previsões recebidas do worker para exibi-las na interface.
      if (message.type === "result" && message.id === request.current) {
        if (urls.current.preview) URL.revokeObjectURL(urls.current.preview);
        urls.current.preview = URL.createObjectURL(message.result.preview);
        setPreview(urls.current.preview);
        setResult(message.result);
        setSelectedClass(message.result.predictions[0].indice);
        setBusy(false);
      }
    };
    instance.onerror = () => {
      setLoadError(
        "O processamento foi interrompido. Recarregue o modelo para tentar novamente.",
      );
      setBusy(false);
    };
    instance.postMessage({
      type: "init",
      base: new URL(base, window.location.href).href,
    } satisfies WorkerRequest);
    return () => {
      instance.terminate();
      worker.current = null;
    };
  }, [retryCount]);

  useEffect(
    () => () => {
      if (urls.current.original) URL.revokeObjectURL(urls.current.original);
      if (urls.current.preview) URL.revokeObjectURL(urls.current.preview);
    },
    [],
  );

  const analyze = (nextFile: File) => {
    if (!model || busy || !worker.current) return;
    setError("");
    if (!["image/jpeg", "image/png", "image/webp"].includes(nextFile.type)) {
      setError("Formato não aceito. Escolha uma foto JPEG, PNG ou WebP.");
      return;
    }
    if (nextFile.size > 10 * 1024 * 1024 || nextFile.size === 0) {
      setError("Escolha uma foto válida com até 10 MB.");
      return;
    }
    request.current += 1;
    if (urls.current.original) URL.revokeObjectURL(urls.current.original);
    if (urls.current.preview) URL.revokeObjectURL(urls.current.preview);
    urls.current = { original: URL.createObjectURL(nextFile), preview: "" };
    setOriginal(urls.current.original);
    setPreview("");
    setFile(nextFile);
    setShowPrepared(false);
    setResult(undefined);
    setSelectedClass(undefined);
    setBusy(true);
    worker.current.postMessage({
      type: "analyze",
      id: request.current,
      file: nextFile,
    } satisfies WorkerRequest);
  };

  const reset = () => {
    if (busy) return;
    request.current += 1;
    Object.values(urls.current).filter(Boolean).forEach(URL.revokeObjectURL);
    urls.current = { original: "", preview: "" };
    setFile(undefined);
    setOriginal("");
    setPreview("");
    setResult(undefined);
    setError("");
    setShowPrepared(false);
    setSelectedClass(undefined);
  };

  const selectPhoto = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.currentTarget.files?.[0];
    if (nextFile) analyze(nextFile);
    // Permite selecionar a mesma foto novamente. Cancelar mantém o resultado.
    event.currentTarget.value = "";
  };

  const chosen = result?.predictions.find(
    (prediction) => prediction.indice === selectedClass,
  );
  const content =
    selectedClass === undefined ? undefined : technicalContent[selectedClass];
  const stage = busy
    ? "Analisando sua foto…"
    : result
      ? "Análise concluída"
      : status;

  return (
    <div className={styles.app}>
      <a className={styles.skipLink} href="#main">
        Pular para o conteúdo
      </a>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <a className={styles.brand} href={base} aria-label="AgroApp, início">
            <img
              src={`${base}brand/agroapp.png`}
              alt=""
              width="38"
              height="38"
            />
            <span>
              Agro<span>APP</span>
            </span>
          </a>
          <nav className={styles.nav} aria-label="Principal">
            <button
              className={tab === "analysis" ? styles.activeNav : ""}
              onClick={() => setTab("analysis")}
              aria-current={tab === "analysis" ? "page" : undefined}
            >
              <ScanLine size={17} />
              Analisar foto
            </button>
            <button
              className={tab === "classes" ? styles.activeNav : ""}
              onClick={() => setTab("classes")}
              aria-current={tab === "classes" ? "page" : undefined}
            >
              <Leaf size={17} />
              Classes do modelo
            </button>
          </nav>
          <button
            className={styles.helpButton}
            onClick={() => help.current?.showModal()}
          >
            <CircleHelp size={18} />
            <span>Como funciona</span>
          </button>
        </div>
      </header>

      <main id="main" className={styles.main}>
        <div className={styles.pageHeading}>
          <div>
            <h1>
              {tab === "analysis" ? (
                <>
                  Um novo olhar para
                  <br />
                  <span>sua lavoura.</span>
                </>
              ) : (
                <>
                  Conheça as classes
                  <br />
                  <span>do nosso modelo.</span>
                </>
              )}
            </h1>
            <p>
              {tab === "analysis"
                ? "Adicione uma foto e explore as possíveis identificações de pragas."
                : "As 13 classes que o modelo foi treinado para reconhecer."}
            </p>
          </div>
          <div className={styles.modelStatus} role="status">
            <span
              className={`${styles.statusDot} ${!model && !loadError ? styles.pulsing : ""} ${loadError ? styles.errorDot : ""}`}
            />
            <div>
              <strong>
                {loadError
                  ? "Modelo indisponível"
                  : model
                    ? "Modelo pronto"
                    : "Preparando o modelo"}
              </strong>
              <span>
                {loadError
                  ? "Tente carregar novamente"
                  : model
                    ? "EfficientNet-Lite0 · 13 classes"
                    : status}
              </span>
            </div>
          </div>
        </div>

        {loadError && (
          <div className={styles.errorBanner} role="alert">
            <Info size={20} />
            <span>{loadError}</span>
            <button onClick={() => setRetryCount((count) => count + 1)}>
              Recarregar modelo <ArrowRight size={16} />
            </button>
          </div>
        )}
        {model?.fallback && (
          <div className={styles.notice} role="status">
            <Info size={18} />
            Este navegador está usando a versão {model.format} de contingência. Confira os
            detalhes da execução abaixo.
          </div>
        )}

        {tab === "analysis" ? (
          <>
            <section
              className={styles.workspace}
              aria-label="Bancada de análise"
            >
              <div className={styles.photoPanel}>
                <div className={styles.panelHeading}>
                  <h2>Sua fotografia</h2>
                  <span>
                    {file
                      ? `${(file.size / 1024 / 1024).toFixed(1).replace(".", ",")} MB`
                      : "Uma foto, muitas pistas"}
                  </span>
                </div>
                <input
                  ref={input}
                  type="file"
                  className={styles.fileInput}
                  accept="image/jpeg,image/png,image/webp"
                  aria-label="Selecionar foto da galeria"
                  tabIndex={-1}
                  disabled={!model || busy}
                  onChange={selectPhoto}
                />
                <input
                  ref={cameraInput}
                  type="file"
                  className={styles.fileInput}
                  accept="image/jpeg,image/png,image/webp"
                  capture="environment"
                  aria-label="Capturar foto com a câmera"
                  tabIndex={-1}
                  disabled={!model || busy}
                  onChange={selectPhoto}
                />
                <div
                  className={`${styles.dropzone} ${dragging ? styles.dragging : ""} ${file ? styles.withPhoto : ""}`}
                  onDragOver={(event) => {
                    event.preventDefault();
                    if (model && !busy) setDragging(true);
                  }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={(event) => {
                    event.preventDefault();
                    setDragging(false);
                    const nextFile = event.dataTransfer.files[0];
                    if (nextFile) analyze(nextFile);
                  }}
                >
                  {original ? (
                    <>
                      <img
                        className={styles.photo}
                        src={showPrepared && preview ? preview : original}
                        alt={
                          showPrepared
                            ? "Foto preparada para o modelo, com preenchimento cinza"
                            : "Foto selecionada para análise"
                        }
                      />
                      {busy && (
                        <div className={styles.scanOverlay}>
                          <div className={styles.scanLine} />
                          <span>
                            <LoaderCircle className={styles.spin} size={17} />{" "}
                            Analisando sua foto
                          </span>
                        </div>
                      )}
                      {!busy && (
                        <button
                          className={styles.removePhoto}
                          onClick={reset}
                          aria-label="Remover foto"
                        >
                          <X size={18} />
                        </button>
                      )}
                    </>
                  ) : (
                    <div className={styles.uploadContent}>
                      <div className={styles.scanGraphic}>
                        <span />
                        <span />
                        <span />
                        <span />
                        <Sprout size={51} strokeWidth={1.3} />
                        <div className={styles.graphicPlus}>
                          <ImagePlus size={19} />
                        </div>
                      </div>
                      <h3>
                        A próxima descoberta
                        <br />
                        começa com uma foto.
                      </h3>
                      <p>
                        Tire uma foto ou escolha da galeria.
                        <br />
                        Você também pode arrastar uma imagem até aqui.
                      </p>
                      <div className={styles.captureActions}>
                        <button
                          className={styles.primaryButton}
                          disabled={!model || busy}
                          onClick={() => cameraInput.current?.click()}
                        >
                          {!model && !loadError ? (
                            <LoaderCircle className={styles.spin} size={18} />
                          ) : (
                            <Camera size={18} />
                          )}
                          Tirar foto
                        </button>
                        <button
                          className={styles.secondaryButton}
                          disabled={!model || busy}
                          onClick={() => input.current?.click()}
                        >
                          <ImagePlus size={18} />
                          Escolher da galeria
                        </button>
                      </div>
                      <span className={styles.fileHint}>
                        JPG, PNG ou WebP · até 10 MB
                      </span>
                    </div>
                  )}
                </div>
                {error && (
                  <div className={styles.inlineError} role="alert">
                    <Info size={17} />
                    <span>{error}</span>
                  </div>
                )}
                <div className={`${styles.photoFooter} ${file ? styles.photoFooterWithPhoto : ""}`}>
                  {file ? (
                    <>
                      <div className={styles.fileName}>
                        <ImagePlus size={17} />
                        <span title={file.name}>{file.name}</span>
                      </div>
                      <div className={styles.photoActions}>
                        <button
                          className={styles.textButton}
                          disabled={busy || !model}
                          onClick={() => cameraInput.current?.click()}
                        >
                          <Camera size={16} /> Tirar outra foto
                        </button>
                        <button
                          className={styles.textButton}
                          disabled={busy || !model}
                          onClick={() => input.current?.click()}
                        >
                          <ImagePlus size={16} /> Trocar foto
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <ShieldCheck size={16} />
                      <span>Sua foto fica no seu dispositivo.</span>
                    </>
                  )}
                </div>
                {result && (
                  <div className={styles.previewToggle}>
                    <div role="group" aria-label="Visualização da imagem">
                      <button
                        aria-pressed={!showPrepared}
                        onClick={() => setShowPrepared(false)}
                      >
                        Original
                      </button>
                      <button
                        aria-pressed={showPrepared}
                        onClick={() => setShowPrepared(true)}
                      >
                        Entrada do modelo
                      </button>
                    </div>
                    <span>
                      <Maximize size={14} />
                      224 × 224 px
                    </span>
                  </div>
                )}
              </div>

              <div className={styles.resultPanel} aria-busy={busy} role="region" aria-labelledby="analysis-result-title">
                <div className={styles.panelHeading}>
                  <h2 id="analysis-result-title">Resultado da análise</h2>
                  <span className={styles.smallBadge}>
                    {result ? "Top 3 hipóteses" : "Reconhecimento visual"}
                  </span>
                </div>
                {!result ? (
                  <div className={styles.emptyResult}>
                    <div
                      className={`${styles.resultSymbol} ${busy ? styles.symbolBusy : ""}`}
                    >
                      <ScanLine size={33} strokeWidth={1.35} />
                    </div>
                    <h3>
                      {busy
                        ? "Observando os detalhes…"
                        : "O que a sua foto revela?"}
                    </h3>
                    <p>
                      {busy
                        ? "Estamos preparando a imagem e comparando seus padrões com as classes do modelo."
                        : "As possíveis identificações aparecem aqui assim que você adicionar uma imagem."}
                    </p>
                    <div className={styles.flow} aria-hidden="true">
                      <span className={styles.flowStep}>
                        <Upload size={17} />
                        <span>Adicionar</span>
                      </span>
                      <span className={styles.flowConnector} />
                      <span className={styles.flowStep}>
                        <ScanLine size={17} />
                        <span>Analisar</span>
                      </span>
                      <span className={styles.flowConnector} />
                      <span className={styles.flowStep}>
                        <Check size={17} />
                        <span>Explorar</span>
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className={styles.results}>
                    <div className={styles.completed}>
                      <CheckCircle2 size={16} />
                      Análise concluída
                      <span>
                        <Clock3 size={13} />
                        {milliseconds(
                          result.preparationMs + result.inferenceMs,
                        )}
                      </span>
                    </div>
                    <p className={styles.resultIntro}>
                      Possíveis identificações
                    </p>
                    {/* Mostra as três classes com maiores scores retornados pelo modelo. */}
                    <div className={styles.predictions}>
                      {result.predictions
                        .slice(0, 3)
                        .map((prediction, index) => {
                          const label = splitLabel(prediction.nome);
                          return (
                            <button
                              key={prediction.indice}
                              className={`${styles.prediction} ${selectedClass === prediction.indice ? styles.selectedPrediction : ""}`}
                              onClick={() =>
                                setSelectedClass(prediction.indice)
                              }
                              aria-pressed={selectedClass === prediction.indice}
                            >
                              <span className={styles.predictionRank}>
                                {String(index + 1).padStart(2, "0")}
                              </span>
                              <span className={styles.predictionLabel}>
                                <strong>{label.common}</strong>
                                {label.scientific && (
                                  <em>{label.scientific}</em>
                                )}
                                <span className={styles.scoreTrack}>
                                  <span
                                    style={{
                                      width: `${prediction.score * 100}%`,
                                    }}
                                  />
                                </span>
                              </span>
                              <span className={styles.score}>
                                {percent(prediction.score)}
                              </span>
                            </button>
                          );
                        })}
                    </div>
                    <p className={styles.scoreDisclaimer}>
                      <Info size={14} />
                      <span>
                        O score expressa a resposta do modelo e não confirma um
                        diagnóstico.
                      </span>
                    </p>
                    <div className={styles.technicalContent}>
                      <BookOpen size={19} />
                      <div>
                        <h3>Orientações técnicas</h3>
                        {content?.validated ? (
                          <>
                            <strong>{content.title}</strong>
                            <p>{content.text}</p>
                            <small>
                              Fonte: {content.source} · Revisado em{" "}
                              {content.reviewedAt}
                            </small>
                          </>
                        ) : (
                          <>
                            <p>
                              Conteúdo técnico ainda indisponível para{" "}
                              {chosen
                                ? splitLabel(chosen.nome).common
                                : "esta classe"}
                              .
                            </p>
                            <small>
                              As orientações serão exibidas após validação
                              técnica.
                            </small>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                <div className={styles.resultFooter}>
                  <span className={styles.miniDot} />
                  <span role="status" aria-live="polite">
                    {loadError ? "Aguardando o modelo" : stage}
                  </span>
                  {model && (
                    <span className={styles.modelFormat}>{model.format}</span>
                  )}
                </div>
              </div>
            </section>

            <section className={styles.tips} aria-label="Dicas para fotografar">
              <div className={styles.tipIcon}>
                <Leaf size={24} strokeWidth={1.5} />
              </div>
              <div className={styles.tipsTitle}>
                <h2>
                  Uma boa foto faz
                  <br /> a diferença.
                </h2>
                <p>Mais detalhes, uma análise melhor.</p>
              </div>
              <ul>
                <li>
                  <Check size={16} />
                  Aproxime-se da praga
                </li>
                <li>
                  <Check size={16} />
                  Use boa iluminação
                </li>
                <li>
                  <Check size={16} />
                  Mantenha a imagem nítida
                </li>
              </ul>
              <img
                src={`${base}brand/leaves.png`}
                alt=""
                className={styles.leaves}
              />
            </section>

            {model && (
              <details className={styles.details}>
                <summary>
                  Detalhes do modelo e da execução
                  <ChevronDown size={16} />
                </summary>
                <dl>
                  <div>
                    <dt>Modelo</dt>
                    <dd>EfficientNet-Lite0</dd>
                  </div>
                  <div>
                    <dt>Versão</dt>
                    <dd>{model.id}</dd>
                  </div>
                  <div>
                    <dt>Formato</dt>
                    <dd>
                      {model.format} ·{" "}
                      {(model.bytes / 1_000_000).toFixed(2).replace(".", ",")}{" "}
                      MB
                    </dd>
                  </div>
                  <div>
                    <dt>Execução</dt>
                    <dd>{model.accelerator}</dd>
                  </div>
                  {result && (
                    <>
                      <div>
                        <dt>Preparação</dt>
                        <dd>{milliseconds(result.preparationMs)}</dd>
                      </div>
                      <div>
                        <dt>Inferência</dt>
                        <dd>{milliseconds(result.inferenceMs)}</dd>
                      </div>
                    </>
                  )}
                </dl>
              </details>
            )}
          </>
        ) : (
          <section
            className={styles.classesSection}
            aria-label="Classes reconhecidas"
          >
            <div className={styles.classTableHeading}>
              <h2>Catálogo de reconhecimento</h2>
              <span>Índices do modelo versionado</span>
            </div>
            <div className={styles.classList}>
              {labels.map((label) => {
                const name = splitLabel(label.nome);
                return (
                  <div className={styles.classRow} key={label.indice}>
                    <span className={styles.classIndex}>
                      {String(label.indice).padStart(2, "0")}
                    </span>
                    <Leaf size={19} />
                    <div>
                      <h3>{name.common}</h3>
                      {name.scientific && <p>{name.scientific}</p>}
                    </div>
                    <span className={styles.classTag}>Praga</span>
                  </div>
                );
              })}
            </div>
            <p className={styles.catalogNote}>
              <Info size={17} />O modelo compara a foto somente com estas
              classes. Fotos de outros assuntos também podem receber um score
              alto.
            </p>
            <button
              className={styles.primaryButton}
              onClick={() => setTab("analysis")}
            >
              Analisar uma foto <ArrowRight size={18} />
            </button>
          </section>
        )}

        <footer className={styles.footer}>
          <span>
            AgroTech <span className={styles.footerDivider} /> Inteli
          </span>
          <span>
            Ciência de dados, a serviço do campo.
            <Leaf size={15} />
          </span>
        </footer>
      </main>

      <dialog
        ref={help}
        className={styles.dialog}
        onClick={(event) => {
          if (event.target === event.currentTarget) help.current?.close();
        }}
        aria-labelledby="help-title"
      >
        <div className={styles.dialogTop}>
          <span className={styles.dialogIcon}>
            <ScanLine size={24} />
          </span>
          <button
            className={styles.iconButton}
            onClick={() => help.current?.close()}
            aria-label="Fechar explicação"
          >
            <X size={21} />
          </button>
        </div>
        <h2 id="help-title">Da fotografia às hipóteses.</h2>
        <p>
          Você adiciona uma foto. O AgroApp prepara a imagem e executa o modelo
          diretamente no navegador, sem enviar sua fotografia a um servidor.
        </p>
        <ol>
          <li>
            <strong>Tire uma foto ou escolha da galeria</strong>
            <span>
              Use uma foto nítida em JPG, PNG ou WebP, sem transparência, com até
              10 MB. A abertura da câmera depende do navegador e do dispositivo.
            </span>
          </li>
          <li>
            <strong>A imagem é preparada automaticamente</strong>
            <span>
              Preservamos a foto inteira e ajustamos para 224 × 224 pixels, com
              bordas cinzas quando necessário.
            </span>
          </li>
          <li>
            <strong>Explore as três hipóteses</strong>
            <span>
              O modelo compara a imagem com 13 classes de pragas. Os scores não
              substituem uma avaliação técnica.
            </span>
          </li>
        </ol>
        <p className={styles.dialogNote}>
          <ShieldCheck size={18} />A conexão é usada para carregar o site e o
          modelo. Sua foto permanece no dispositivo.
        </p>
        <button
          className={styles.primaryButton}
          onClick={() => help.current?.close()}
        >
          Entendi, vamos analisar <ArrowRight size={18} />
        </button>
      </dialog>
    </div>
  );
}
