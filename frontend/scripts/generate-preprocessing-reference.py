"""Referências T10.2 sem TensorFlow. Executar da raiz com Pillow 12.2 / NumPy 2.4.4."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import sys

import numpy as np
from PIL import Image, ImageCms, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.preprocessamento import CONTRATO_PREPROCESSAMENTO, decodificar_imagem, preparar_pixels, preparar_imagem

OUT = ROOT / "frontend/tests/fixtures/preprocessing"


def gerar():
    # Originais intactos do acervo, identificados nos registros de revisão T8.1.
    origens = {
        "display-p3.jpg": "IMG_01540; dataset/image/4bb174ff-imag24.jpg",
        "srgb.jpg": "IMG_01812; dataset/image/test504.jpg",
        "no-profile.jpg": "assets/revisão_imagens/IMG_0125.jpg",
    }
    fronteiras = json.loads((OUT / "boundary-provenance.json").read_text(encoding="utf-8")) if (OUT / "boundary-provenance.json").exists() else []
    fontes_derivadas = {caso["file"]: f"derivada de {caso['source']}; brilho {caso['brightness']}" for caso in fronteiras}
    with Image.open(OUT / "display-p3.jpg") as imagem:
        perfil = imagem.info["icc_profile"]
    with Image.open(OUT / "no-profile.jpg") as imagem:
        # Lossless variants retain real photographic texture. EXIF tags are
        # controlled test metadata; they are not claimed as original camera EXIF.
        base = imagem.convert("RGB")
        base.info.clear()
        base.save(OUT / "photo.png")
        base.save(OUT / "photo-icc.png", icc_profile=perfil)
        base.save(OUT / "photo.webp", lossless=True)
        for orientacao in range(1, 9):
            exif = Image.Exif()
            exif[274] = orientacao
            base.save(OUT / f"exif-{orientacao}.png", exif=exif, icc_profile=perfil)
        transparente = base.convert("RGBA")
        transparente.putpixel((0, 0), (1, 2, 3, 0))
        transparente.save(OUT / "transparent.png")
    casos = []
    for nome in [*origens, "photo.png", "photo-icc.png", "photo.webp",
                 *(f"exif-{i}.png" for i in range(1, 9)),
                 *(p.name for p in sorted(OUT.glob("boundary-*.png")))]:
        caminho = OUT / nome
        with Image.open(caminho) as imagem:
            icc = imagem.info.get("icc_profile")
            descricao = ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))).strip() if icc else None
            orientacao = imagem.getexif().get(274, 1)
            tamanho_original = list(imagem.size)
        decodificada = decodificar_imagem(caminho)
        pixels = preparar_pixels(caminho)
        # gzip mtime=0 keeps generated fixtures deterministic.
        for etapa, dados in [("decoded", decodificada.tobytes()), ("pixels", pixels.tobytes())]:
            (OUT / f"{nome}.{etapa}.gz").write_bytes(gzip.compress(dados, mtime=0))
        casos.append({
            "file": nome, "source": origens.get(nome, fontes_derivadas.get(nome, "derivada de no-profile.jpg; metadados controlados")),
            "sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(),
            "originalSize": tamanho_original, "width": decodificada.width, "height": decodificada.height,
            "icc": descricao, "orientation": orientacao,
            "decodedSha256": hashlib.sha256(decodificada.tobytes()).hexdigest(),
            "pixelsSha256": hashlib.sha256(pixels.tobytes()).hexdigest(),
            "normalizedSha256": hashlib.sha256(preparar_imagem(caminho).astype('<f4').tobytes()).hexdigest(),
            "tolerance": {"max": 3, "mae": 0.35} if caminho.suffix == ".jpg" else {"max": 0, "mae": 0},
        })
    referencia = {"contract": CONTRATO_PREPROCESSAMENTO,
                  "environment": {"pillow": pillow_version, "numpy": np.__version__}, "cases": casos}
    (OUT / "reference.json").write_text(json.dumps(referencia, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"OK: {len(casos)} referências fotográficas T10.2")


if __name__ == "__main__":
    gerar()
