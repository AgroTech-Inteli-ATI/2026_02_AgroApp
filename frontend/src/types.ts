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
  format: "INT8" | "FP32";
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
  id: string;
  architecture: string;
  selectionStatus: string;
  classesSource: {
    sourcePath: string;
    contractPath: string;
    sha256: string;
  };
  classes: ClassLabel[];
  models: ModelSpec[];
}
export interface ModelInfo {
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
