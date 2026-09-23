"""Listas usadas para gerar cadastros fictícios (sem dados de pessoas reais)."""

from __future__ import annotations

import random
from decimal import Decimal

from .regras import FILIAL_COMPARTILHADA, cnpj_ficticio, proximo_codigo

PREFIXOS = ["Alfa", "Beta", "Delta", "Horizonte", "Litoral", "Serra", "Vale", "Planalto", "Nova Era", "Atlântica",
            "Central", "Pioneira", "Progresso", "União", "Real", "Continental", "Estrela", "Aurora", "Imperial", "Sol"]
RAMOS = ["Materiais de Construção", "Hidráulica", "Construtora", "Distribuidora", "Comércio de Tubos",
         "Home Center", "Engenharia", "Instalações", "Saneamento", "Irrigação"]
SUFIXOS = ["Ltda", "S.A.", "EIRELI", "ME"]
LOCALIDADES = [("SC", "Joinville"), ("SC", "Blumenau"), ("PR", "Curitiba"), ("SP", "Campinas"), ("RS", "Caxias do Sul"),
               ("BA", "Salvador"), ("PE", "Recife"), ("CE", "Fortaleza"), ("GO", "Goiânia"), ("MT", "Cuiabá"),
               ("DF", "Brasília"), ("MS", "Campo Grande"), ("MG", "Uberlândia")]
NOMES_VENDEDOR = ["Vendedor", "Representante", "Consultor"]
PRODUTOS = [
    ("TB", "Tubo PVC soldável", ["20mm", "25mm", "32mm", "40mm", "50mm"], "BR", Decimal("18.90"), "0001"),
    ("TE", "Tubo esgoto", ["40mm", "50mm", "75mm", "100mm"], "BR", Decimal("32.50"), "0001"),
    ("JO", "Joelho 90 soldável", ["20mm", "25mm", "32mm", "40mm"], "UN", Decimal("1.80"), "0002"),
    ("TE", "Tê soldável", ["20mm", "25mm", "32mm"], "UN", Decimal("2.40"), "0002"),
    ("LU", "Luva soldável", ["20mm", "25mm", "32mm", "50mm"], "UN", Decimal("1.20"), "0002"),
    ("RG", "Registro esfera", ["20mm", "25mm", "32mm"], "UN", Decimal("24.90"), "0003"),
    ("CX", "Caixa sifonada", ["100mm", "150mm"], "UN", Decimal("19.70"), "0003"),
    ("CO", "Cola para PVC", ["75g", "175g", "850g"], "UN", Decimal("12.30"), "0004"),
]


def gerar_vendedores(rng: random.Random, quantidade: int) -> list[tuple]:
    linhas, codigo = [], None
    for i in range(1, quantidade + 1):
        codigo = proximo_codigo(codigo)
        linhas.append((FILIAL_COMPARTILHADA, codigo, f"{rng.choice(NOMES_VENDEDOR)} {i:03d}"))
    return linhas


def gerar_produtos(rng: random.Random, quantidade: int) -> list[tuple]:
    catalogo = [(pref, desc, med, um, preco, grupo) for pref, desc, medidas, um, preco, grupo in PRODUTOS
                for med in medidas]
    linhas = []
    for i, (pref, desc, med, um, preco, grupo) in enumerate(catalogo[:quantidade], start=1):
        fator = Decimal(str(round(rng.uniform(0.9, 1.1), 2)))
        linhas.append((FILIAL_COMPARTILHADA, f"{pref}{i:05d}", f"{desc} {med}"[:30], "PA", um, grupo,
                       (preco * fator).quantize(Decimal("0.01"))))
    return linhas


def gerar_cliente(rng: random.Random, codigo: str, vendedores: list[str]) -> tuple:
    prefixo, ramo = rng.choice(PREFIXOS), rng.choice(RAMOS)
    uf, municipio = rng.choice(LOCALIDADES)
    nome = f"{prefixo} {ramo} {rng.choice(SUFIXOS)}"[:40]
    return (FILIAL_COMPARTILHADA, codigo, "01", nome, f"{prefixo} {ramo}"[:20], uf, municipio,
            cnpj_ficticio(rng), rng.choice(vendedores), "2")
