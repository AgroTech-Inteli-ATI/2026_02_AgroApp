"""Gera o kit de imagens da T12.3 para copiar ao celular (galeria).

python frontend/scripts/device-kit.py            # na raiz do repositório
Saída: frontend/.work/kit-dispositivo/ (ignorada pelo Git) com kit.json (hashes e resultado esperado).

As oito fotos exif-N.jpg guardam os pixels girados/espelhados com a tag Orientation N,
de modo que, aplicado o EXIF, todas mostram a mesma foto em pé. Os scores esperados vêm
do Float16 do build (TFLite + XNNPACK, configuração equivalente ao navegador na T10.2).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.benchmark_t5_6 import interpretador, prever  # noqa: E402
from src.preprocessamento import preparar_imagem  # noqa: E402

BASE = ROOT / "assets/revisão_imagens/IMG_0021.jpg"
SAIDA = ROOT / "frontend/.work/kit-dispositivo"
BUILD = ROOT / "frontend/dist/models"
T = Image.Transpose
# Transformação a gravar nos pixels para que exif_transpose(tag N) devolva a foto em pé.
INVERSA = {1: None, 2: T.FLIP_LEFT_RIGHT, 3: T.ROTATE_180, 4: T.FLIP_TOP_BOTTOM,
           5: T.TRANSPOSE, 6: T.ROTATE_90, 7: T.TRANSVERSE, 8: T.ROTATE_270}
LIMIAR = json.loads((ROOT / "assets/data/politica_T6_5/parametros.json").read_text(encoding="utf-8"))["limiar_confianca"]
ERROS = {
    "transparente.png": "A imagem tem transparência. Escolha um JPEG ou uma imagem sem transparência.",
    "acima-40mp.jpg": "A foto é grande demais. Reduza para até 40 megapixels e tente novamente.",
    "acima-10mb.png": "Escolha uma foto válida com até 10 MB.",
    "vazia.jpg": "Escolha uma foto válida com até 10 MB.",
    "corrompida.jpg": "Não foi possível abrir a foto. Escolha um JPEG, PNG ou WebP válido.",
    "animacao.gif": "Formato não aceito. Escolha uma foto JPEG, PNG ou WebP. (ou o seletor não oferece o arquivo)",
}


def gerar(saida: Path = SAIDA) -> dict:
    saida.mkdir(parents=True, exist_ok=True)
    em_pe = Image.open(BASE).convert("RGB")
    (saida / "referencia.jpg").write_bytes(BASE.read_bytes())
    for tag, inversa in INVERSA.items():
        pixels = em_pe if inversa is None else em_pe.transpose(inversa)
        exif = Image.Exif()
        exif[0x0112] = tag
        pixels.save(saida / f"exif-{tag}.jpg", quality=100, subsampling=0, exif=exif)
        corrigida = ImageOps.exif_transpose(Image.open(saida / f"exif-{tag}.jpg")).convert("RGB")
        diferenca = np.abs(np.asarray(corrigida, np.int16) - np.asarray(em_pe, np.int16)).mean()
        assert corrigida.size == em_pe.size and diferenca < 2, f"exif-{tag}.jpg não volta à foto em pé"

    transparente = em_pe.convert("RGBA")
    transparente.putalpha(Image.new("L", em_pe.size, 128))
    transparente.save(saida / "transparente.png")
    Image.new("RGB", (8000, 5001), (90, 120, 60)).save(saida / "acima-40mp.jpg", quality=85)
    ruido = np.random.default_rng(42).integers(0, 256, (1900, 1900, 3), dtype=np.uint8)
    Image.fromarray(ruido).save(saida / "acima-10mb.png", compress_level=1)
    assert (saida / "acima-10mb.png").stat().st_size > 10 * 1024 * 1024
    (saida / "vazia.jpg").write_bytes(b"")
    (saida / "corrompida.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"nao e uma foto" * 20)
    quadros = [em_pe.convert("P"), ImageOps.invert(em_pe).convert("P")]
    quadros[0].save(saida / "animacao.gif", save_all=True, append_images=quadros[1:], duration=300, loop=0)

    manifesto = json.loads((BUILD / "manifest.json").read_text(encoding="utf-8"))
    spec = next(m for m in manifesto["models"] if m["role"] == "principal")
    modelo = interpretador(BUILD / spec["filename"], 1, "padrao")
    nomes = [c["nome"] for c in manifesto["classes"]]
    arquivos = {}
    for caminho in sorted(saida.iterdir()):
        if caminho.name == "kit.json":
            continue
        item = {"sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(), "bytes": caminho.stat().st_size}
        if caminho.name in ERROS:
            item["esperado"] = {"erro": ERROS[caminho.name]}
        else:
            scores = prever(modelo, preparar_imagem(caminho))
            top = int(scores.argmax())
            item["esperado"] = {"classe": nomes[top], "indice": top, "score_top1": round(float(scores[top]), 4),
                                "decisao": "aceito" if scores[top] >= LIMIAR else "inconclusivo"}
        arquivos[caminho.name] = item
    kit = {"esquema": "kit_dispositivo_T12_3_v1", "origem": BASE.relative_to(ROOT).as_posix(),
           "modelo": {"formato": spec["format"], "sha256": spec["sha256"]}, "limiar": LIMIAR, "arquivos": arquivos}
    (saida / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return kit


if __name__ == "__main__":
    for nome, item in gerar()["arquivos"].items():
        print(f"{nome:18} {item['esperado']}")
