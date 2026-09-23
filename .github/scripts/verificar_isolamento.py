"""Verificação de isolamento entre ambientes (quality gate do CI).

Falha se:
1. algum arquivo do pipeline citar um catálogo bronze/silver/gold (com ou sem prefixo dev_) de forma fixa,
   em vez de recebê-lo por parâmetro;
2. algum código do pipeline gravar na landing, que é escrita apenas pelo extrator.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTAS = [RAIZ / "src", RAIZ / "setup", RAIZ / "resources"]
EXTENSOES = {".py", ".sql", ".ipynb", ".json", ".yml", ".yaml"}

CATALOGO_FIXO = re.compile(r"(?<![\w{$])(?:dev_)?(?:bronze|silver|gold)\.(?:protheus|comercial|information_schema)\b")
ESCRITA_LANDING = re.compile(
    r"\.write[^\n]*\.(?:save|saveAsTable|parquet|json|csv)\([^)\n]*landing"
    r"|(?:INSERT\s+INTO|MERGE\s+INTO|COPY\s+INTO)\s+[`\"']?(?:/Volumes/)?landing",
    re.IGNORECASE,
)


def conteudo(arquivo: Path) -> str:
    texto = arquivo.read_text(encoding="utf-8")
    if arquivo.suffix == ".ipynb":
        notebook = json.loads(texto)
        return "\n".join("".join(celula.get("source", [])) for celula in notebook.get("cells", []))
    return texto


def main() -> int:
    problemas: list[str] = []
    for pasta in PASTAS:
        for arquivo in sorted(pasta.rglob("*")):
            if not arquivo.is_file() or arquivo.suffix not in EXTENSOES:
                continue
            for numero, linha in enumerate(conteudo(arquivo).splitlines(), start=1):
                relativo = arquivo.relative_to(RAIZ)
                if CATALOGO_FIXO.search(linha):
                    problemas.append(f"{relativo}:{numero}: catálogo citado de forma fixa -> {linha.strip()}")
                if ESCRITA_LANDING.search(linha):
                    problemas.append(f"{relativo}:{numero}: escrita na landing pelo pipeline -> {linha.strip()}")
    if problemas:
        print("Falha na verificação de isolamento:")
        print("\n".join(problemas))
        return 1
    print("Verificação de isolamento concluída sem problemas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
