import { createHash } from "node:crypto";
import { describe, expect, it } from "vitest";
import reference from "../../tests/fixtures/reference.json";
import { letterbox, quantize, roundEven } from "./preprocess";

describe("Contrato do processamento Python", () => {
  for (const { width, height, sha256 } of reference.preprocessing) {
    it(`reproduz Pillow para ${width} × ${height}`, () => {
      const rgb = Uint8Array.from(
        { length: width * height * 3 },
        (_, i) => (i * 37 + Math.floor(i / 7) * 19) % 256,
      );
      const pixels = letterbox(rgb, width, height);
      expect(pixels.length).toBe(224 * 224 * 3);
      expect(createHash("sha256").update(pixels).digest("hex")).toBe(sha256);
    });
  }

  it("respeita empates pares do Python, incluindo negativos", () => {
    expect([-2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5].map(roundEven)).toEqual([
      -2, -2, 0, 0, 2, 2, 4,
    ]);
  });

  it("quantiza os 256 níveis RGB no contrato INT8 do candidato", () => {
    const pixels = Uint8Array.from({ length: 256 }, (_, i) => i);
    const [scale, zero] = reference.quantization.input;
    expect(Array.from(quantize(pixels, scale, zero))).toEqual(
      Array.from({ length: 256 }, (_, i) => i - 128),
    );
  });

  it("preserva conteúdo e bordas cinzas sem cortar uma imagem estreita", () => {
    const pixels = letterbox(new Uint8Array([255, 0, 0, 0, 0, 255]), 1, 2);
    expect([...pixels.slice(0, 3)]).toEqual([128, 128, 128]);
    expect([...pixels.slice(56 * 3, 56 * 3 + 3)]).toEqual([255, 0, 0]);
    const bottomCenter = (223 * 224 + 112) * 3;
    expect([...pixels.slice(bottomCenter, bottomCenter + 3)]).toEqual([
      0, 0, 255,
    ]);
  });
});
