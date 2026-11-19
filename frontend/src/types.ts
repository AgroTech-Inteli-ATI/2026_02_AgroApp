export interface ClassLabel {
  indice: number;
  nome: string;
}
export interface TensorSpec {
  shape: number[];
  dtype: "int8" | "float32";
  scale?: number;
  zeroPoint?: number;
}
export interface ModelSpec {
  format: "Float16" | "INT8";
  role: "principal" | "contingencia";
  filename: string;
  bytes: number;
  sha256: string;
  sourceSha256: string;
  sourcePath: string;
  contractPath: string;
  version: string;
  input: TensorSpec;
  output: TensorSpec;
}
export interface ModelManifest {
  runtime?: { name: string; version: string };
  id: string;
  version: string;
  architecture: string;
  selectionStatus: string;
  selection: { sourcePath: string; status: string };
  classesSource: {
    sourcePath: string;
    contractPath: string;
    sha256: string;
  };
  classes: ClassLabel[];
  models: ModelSpec[];
}
export interface ModelInfo {
  sha256?: string;
  sourceSha256?: string;
  runtime?: { name: string; version: string };
  requestedAccelerator?: string;
  fullyAccelerated?: boolean;
  cpuThreads?: number;
  id: string;
  format: string;
  bytes: number;
  accelerator: string;
  fallback: boolean;
}
export interface Prediction extends ClassLabel {
  score: number;
}
export interface AnalysisResult {
  predictions: Prediction[];
  preparationMs: number;
  inferenceMs: number;
  width: number;
  height: number;
  preview: Blob;
}
export type WorkerRequest =
  | { type: "init"; base: string }
  | { type: "analyze"; id: number; file: File };
export type WorkerResponse =
  | { type: "status"; message: string }
  | { type: "ready"; info: ModelInfo }
  | { type: "result"; id: number; result: AnalysisResult }
  | { type: "error"; id?: number; message: string };
