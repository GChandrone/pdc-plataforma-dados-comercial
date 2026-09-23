"""Destinos dos arquivos extraídos: volume do Unity Catalog (produção) ou pasta local (testes)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Protocol


class Destino(Protocol):
    def gravar(self, caminho_relativo: str, conteudo: bytes) -> None: ...


class DestinoLocal:
    def __init__(self, base: str | Path) -> None:
        self.base = Path(base)

    def gravar(self, caminho_relativo: str, conteudo: bytes) -> None:
        arquivo = self.base / caminho_relativo
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_bytes(conteudo)


class DestinoVolume:
    """Envia arquivos a um volume do Unity Catalog pela Files API (autenticação por DATABRICKS_HOST/TOKEN)."""

    def __init__(self, base: str) -> None:
        if not base.startswith("/Volumes/"):
            raise ValueError("LANDING_PATH deve apontar para um volume do Unity Catalog (/Volumes/...)")
        from databricks.sdk import WorkspaceClient

        self.base = base.rstrip("/")
        self._cliente = WorkspaceClient()

    def gravar(self, caminho_relativo: str, conteudo: bytes) -> None:
        self._cliente.files.upload(f"{self.base}/{caminho_relativo}", io.BytesIO(conteudo), overwrite=True)
