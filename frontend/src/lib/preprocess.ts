export const INPUT_SIZE = 224;
export const PREPROCESS_CONTRACT = "T10.2-rgb8-sem-conversao-icc-v1";
const PRECISION = 2 ** 22;

// Python round() / NumPy rint: ties to even, including negative values.
export function roundEven(value: number) {
  const floor = Math.floor(value),
    fraction = value - floor;
  return fraction < 0.5
    ? floor
    : fraction > 0.5
      ? floor + 1
      : floor % 2 === 0
        ? floor
        : floor + 1;
}

function cubic(x: number) {
  x = Math.abs(x);
  if (x < 1) return (1.5 * x - 2.5) * x * x + 1;
  if (x < 2) return ((-0.5 * x + 2.5) * x - 4) * x + 2;
  return 0;
}

function coefficients(source: number, target: number) {
  const scale = source / target,
    filterScale = Math.max(1, scale),
    support = 2 * filterScale;
  return Array.from({ length: target }, (_, i) => {
    const center = (i + 0.5) * scale;
    const start = Math.max(0, Math.trunc(center - support + 0.5));
    const end = Math.min(source, Math.trunc(center + support + 0.5));
    const weights = Array.from({ length: end - start }, (_, j) =>
      cubic((j + start - center + 0.5) / filterScale),
    );
    const sum = weights.reduce((a, b) => a + b, 0);
    return {
      start,
      weights: weights.map((w) =>
        Math.trunc((w / sum) * PRECISION + (w < 0 ? -0.5 : 0.5)),
      ),
    };
  });
}

/** Pillow-compatible separable bicubic resampling with antialiasing and RGB8 rounding. */
export function resizeBicubic(
  rgb: Uint8Array,
  width: number,
  height: number,
  newWidth: number,
  newHeight: number,
) {
  let horizontal = rgb;
  if (width !== newWidth) {
    horizontal = new Uint8Array(newWidth * height * 3);
    const filters = coefficients(width, newWidth);
    for (let y = 0; y < height; y++)
      for (let x = 0; x < newWidth; x++) {
        const { start, weights } = filters[x];
        for (let c = 0; c < 3; c++) {
          let sum = PRECISION / 2;
          for (let k = 0; k < weights.length; k++)
            sum += rgb[(y * width + start + k) * 3 + c] * weights[k];
          horizontal[(y * newWidth + x) * 3 + c] = Math.max(
            0,
            Math.min(255, Math.floor(sum / PRECISION)),
          );
        }
      }
  }
  if (height === newHeight) return horizontal;
  const result = new Uint8Array(newWidth * newHeight * 3),
    filters = coefficients(height, newHeight);
  for (let y = 0; y < newHeight; y++)
    for (let x = 0; x < newWidth; x++) {
      const { start, weights } = filters[y];
      for (let c = 0; c < 3; c++) {
        let sum = PRECISION / 2;
        for (let k = 0; k < weights.length; k++)
          sum += horizontal[((start + k) * newWidth + x) * 3 + c] * weights[k];
        result[(y * newWidth + x) * 3 + c] = Math.max(
          0,
          Math.min(255, Math.floor(sum / PRECISION)),
        );
      }
    }
  return result;
}

export function letterbox(rgb: Uint8Array, width: number, height: number) {
  const scale = INPUT_SIZE / Math.max(width, height);
  const newWidth = Math.max(1, roundEven(width * scale)),
    newHeight = Math.max(1, roundEven(height * scale));
  const resized = resizeBicubic(rgb, width, height, newWidth, newHeight);
  const output = new Uint8Array(INPUT_SIZE * INPUT_SIZE * 3).fill(128);
  const left = Math.floor((INPUT_SIZE - newWidth) / 2),
    top = Math.floor((INPUT_SIZE - newHeight) / 2);
  for (let y = 0; y < newHeight; y++) {
    output.set(
      resized.subarray(y * newWidth * 3, (y + 1) * newWidth * 3),
      ((top + y) * INPUT_SIZE + left) * 3,
    );
  }
  return output;
}

export function quantize(rgb: Uint8Array, scale: number, zero: number) {
  return Int8Array.from(rgb, (pixel) =>
    Math.max(
      -128,
      Math.min(127, roundEven(Math.fround(pixel / 255) / scale + zero)),
    ),
  );
}

/** Float32 HWC in [0,1]; backbone normalization already belongs to the model. */
export function normalize(rgb: Uint8Array) {
  return Float32Array.from(rgb, (pixel) => pixel / 255);
}

export async function decodeImage(file: File) {
  let bitmap: ImageBitmap;
  try {
    // Preserve the encoded RGB values, as Pillow convert('RGB') did at training.
    // The default allows browser-dependent ICC/gamma conversion, including P3.
    bitmap = await createImageBitmap(file, {
      imageOrientation: "from-image",
      colorSpaceConversion: "none",
      premultiplyAlpha: "none",
    });
  } catch {
    throw new Error(
      "Não foi possível abrir a foto. Escolha um JPEG, PNG ou WebP válido.",
    );
  }
  try {
    const { width, height } = bitmap;
    if (width * height > 40_000_000)
      throw new Error(
        "A foto é grande demais. Reduza para até 40 megapixels e tente novamente.",
      );
    const canvas = new OffscreenCanvas(width, height);
    const context = canvas.getContext("2d", {
      willReadFrequently: true,
      colorSpace: "srgb",
    });
    if (!context)
      throw new Error(
        "Seu navegador não oferece o processamento de imagem necessário. Use Chrome ou Edge atualizado.",
      );
    context.drawImage(bitmap, 0, 0);
    const rgba = context.getImageData(0, 0, width, height, { colorSpace: "srgb" }).data;
    const rgb = new Uint8Array(width * height * 3);
    for (let i = 0, j = 0; i < rgba.length; i += 4, j += 3) {
      if (rgba[i + 3] !== 255)
        throw new Error(
          "A imagem tem transparência. Escolha um JPEG ou uma imagem sem transparência.",
        );
      rgb[j] = rgba[i];
      rgb[j + 1] = rgba[i + 1];
      rgb[j + 2] = rgba[i + 2];
    }
    return { rgb, width, height };
  } finally {
    bitmap.close();
  }
}

export async function prepareImage(file: File) {
  const { rgb, width, height } = await decodeImage(file);
  const pixels = letterbox(rgb, width, height);
  const previewCanvas = new OffscreenCanvas(INPUT_SIZE, INPUT_SIZE);
  const previewContext = previewCanvas.getContext("2d", { colorSpace: "srgb" })!;
  const imageData = previewContext.createImageData(INPUT_SIZE, INPUT_SIZE);
  for (let i = 0, j = 0; i < pixels.length; i += 3, j += 4) {
    imageData.data[j] = pixels[i];
    imageData.data[j + 1] = pixels[i + 1];
    imageData.data[j + 2] = pixels[i + 2];
    imageData.data[j + 3] = 255;
  }
  previewContext.putImageData(imageData, 0, 0);
  return {
    pixels,
    width,
    height,
    preview: await previewCanvas.convertToBlob({ type: "image/png" }),
  };
}
