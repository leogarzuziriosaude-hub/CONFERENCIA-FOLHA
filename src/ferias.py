"""
Gerenciamento do histórico de férias.
Salvo em historico/ferias.json — persistido entre execuções.
"""

import json
import os
from pathlib import Path

HISTORICO_PATH = Path("historico/ferias.json")


def _carregar() -> dict:
    """Carrega o histórico de férias do arquivo JSON."""
    if HISTORICO_PATH.exists():
        with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _salvar(historico: dict):
    """Salva o histórico de férias no arquivo JSON."""
    HISTORICO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


def registrar_ferias(mes: str, matriculas: list[str]):
    """
    Registra as matrículas em férias para um determinado mês.
    
    Args:
        mes: string no formato 'MM/AAAA' (ex: '04/2026')
        matriculas: lista de matrículas (strings de 8 dígitos)
    """
    historico = _carregar()
    historico[mes] = list(set(matriculas))  # remove duplicatas
    _salvar(historico)


def esta_de_ferias(matricula: str, mes: str) -> bool:
    """
    Verifica se uma matrícula estava de férias em determinado mês.
    
    Args:
        matricula: string de 8 dígitos
        mes: string no formato 'MM/AAAA'
    
    Returns:
        True se estava de férias, False caso contrário
    """
    historico = _carregar()
    return matricula in historico.get(mes, [])


def listar_ferias(mes: str) -> list[str]:
    """Retorna a lista de matrículas em férias no mês informado."""
    historico = _carregar()
    return historico.get(mes, [])


def listar_meses_registrados() -> list[str]:
    """Retorna todos os meses que têm férias registradas."""
    historico = _carregar()
    return sorted(historico.keys())


def remover_mes(mes: str):
    """Remove o registro de férias de um mês (útil para corrigir erros)."""
    historico = _carregar()
    if mes in historico:
        del historico[mes]
        _salvar(historico)
