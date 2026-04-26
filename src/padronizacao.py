import pandas as pd
import re


# ─────────────────────────────────────────────
# RUBRICAS POR TIPO E PREFIXO
# ─────────────────────────────────────────────

RUBRICAS = {
    "ADN":        {"normal": 3037, "contrato": 703},
    "GRAT_FDS":   {"normal": 3120, "contrato": 710},
    "ATRASOS":    {"normal": 3507, "contrato": 1054},
    "FALTA":      {"normal": 3506, "contrato": 1065},
    "DIF_PROV":   {"normal": 3195, "contrato": 1053},
    "PLANTAO":    {"normal": 3147, "contrato": 716},
    "ROTINA":     {"normal": 3154, "contrato": 719},
}

PREFIXO_CONTRATO = 95  # prefixo que usa rubricas de contrato administrativo


def get_rubrica(tipo: str, prefixo) -> int:
    """Retorna a rubrica correta com base no tipo e prefixo."""
    try:
        pref = int(str(prefixo).strip())
    except Exception:
        pref = 0
    chave = "contrato" if pref == PREFIXO_CONTRATO else "normal"
    return RUBRICAS[tipo][chave]


# ─────────────────────────────────────────────
# PADRONIZAÇÃO DE MATRÍCULA
# ─────────────────────────────────────────────

def padronizar_matricula(valor) -> str:
    """
    Normaliza matrícula para string de 8 dígitos sem formatação.
    Aceita: '0.123.456-7' ou '01234567' ou variações.
    Retorna: '01234567'
    """
    if pd.isna(valor):
        return ""
    s = str(valor).strip()
    apenas_digitos = re.sub(r"[^\d]", "", s)
    return apenas_digitos.zfill(8) if apenas_digitos else ""


# ─────────────────────────────────────────────
# LIMPEZA GERAL
# ─────────────────────────────────────────────

def limpar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Remove colunas 'Unnamed' geradas pelo pandas."""
    df = df.copy()
    df.columns = df.columns.astype(str)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    return df


def remover_linhas_vazias(df: pd.DataFrame, col_matricula: str = "MATRICULA") -> pd.DataFrame:
    """Remove linhas onde a matrícula está vazia."""
    return df[df[col_matricula].notna() & (df[col_matricula].astype(str).str.strip() != "")].copy()


# ─────────────────────────────────────────────
# PADRONIZAÇÃO POR ABA
# ─────────────────────────────────────────────

def padronizar_adn(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza aba ADC NOT.
    Colunas originais (posição): B=PREF, C=MATRICULA, F=DATA_INICIAL, G=DATA_FINAL, J=HORAS
    Índices (base 0 após limpar Unnamed): 1, 2, 5, 6, 9
    """
    df = limpar_colunas(df)
    df_pad = df.iloc[:, [1, 2, 5, 6, 9]].copy()
    df_pad.columns = ["PREF", "MATRICULA", "DATA_INICIAL", "DATA_FINAL", "HORAS"]
    df_pad["MATRICULA"] = df_pad["MATRICULA"].apply(padronizar_matricula)
    df_pad["EVENTO"] = "ADN"
    df_pad = remover_linhas_vazias(df_pad)
    return df_pad.reset_index(drop=True)


def padronizar_grat_fds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza aba GRAT FDS.
    Colunas: B=PREF, C=MATRICULA, F=DATA_INICIAL, I=HORAS
    Índices: 1, 2, 5, 8
    Horas válidas: 4, 6, 8, 10, 12, 24
    """
    df = limpar_colunas(df)
    df_pad = df.iloc[:, [1, 2, 5, 8]].copy()
    df_pad.columns = ["PREF", "MATRICULA", "DATA_INICIAL", "HORAS"]
    df_pad["MATRICULA"] = df_pad["MATRICULA"].apply(padronizar_matricula)
    df_pad["EVENTO"] = "GRAT_FDS"
    df_pad = remover_linhas_vazias(df_pad)
    return df_pad.reset_index(drop=True)


def padronizar_atrasos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza aba ATRASOS.
    Colunas: B=PREF, C=MATRICULA, G=DATA_INICIAL, I=HORAS (formato HH:MM)
    Índices: 1, 2, 6, 8
    """
    df = limpar_colunas(df)
    df_pad = df.iloc[:, [1, 2, 6, 8]].copy()
    df_pad.columns = ["PREF", "MATRICULA", "DATA_INICIAL", "HORAS"]
    df_pad["MATRICULA"] = df_pad["MATRICULA"].apply(padronizar_matricula)
    df_pad["HORAS"] = df_pad["HORAS"].apply(normalizar_hhmm)
    df_pad["EVENTO"] = "ATRASOS"
    df_pad = remover_linhas_vazias(df_pad)
    return df_pad.reset_index(drop=True)


def padronizar_falta(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza aba FALTA - INJUSTIFICADA.
    Colunas: B=PREF, C=MATRICULA, G=DATA_INICIAL, H=DATA_FINAL
    Índices: 1, 2, 6, 7
    """
    df = limpar_colunas(df)
    df_pad = df.iloc[:, [1, 2, 6, 7]].copy()
    df_pad.columns = ["PREF", "MATRICULA", "DATA_INICIAL", "DATA_FINAL"]
    df_pad["MATRICULA"] = df_pad["MATRICULA"].apply(padronizar_matricula)
    df_pad["EVENTO"] = "FALTA"
    df_pad = remover_linhas_vazias(df_pad)
    return df_pad.reset_index(drop=True)


def padronizar_dificil_provimento(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza planilha de difícil provimento.
    Colunas: A=PREF, B=MATRICULA, C=NOME, D=CARGO, E=HORAS
    Índices: 0, 1, 2, 3, 4
    """
    df = limpar_colunas(df)
    df_pad = df.iloc[:, [0, 1, 2, 3, 4]].copy()
    df_pad.columns = ["PREF", "MATRICULA", "NOME", "CARGO", "HORAS"]
    df_pad["MATRICULA"] = df_pad["MATRICULA"].apply(padronizar_matricula)
    df_pad["EVENTO"] = "DIF_PROV"
    df_pad = remover_linhas_vazias(df_pad)
    return df_pad.reset_index(drop=True)


def padronizar_previa(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza a planilha de prévia da folha.
    Colunas relevantes:
        A=PREF, B=MATRICULA, C=NOME, E=CARGO, H=CARGA_HORARIA,
        K=RUBRICA, L=DESCRICAO, O=COMPETENCIA, P=VALOR
    Índices: 0, 1, 2, 4, 7, 10, 11, 14, 15
    """
    df = limpar_colunas(df)
    df_pad = df.iloc[:, [0, 1, 2, 4, 7, 10, 11, 14, 15]].copy()
    df_pad.columns = [
        "PREF", "MATRICULA", "NOME", "CARGO",
        "CARGA_HORARIA", "RUBRICA", "DESCRICAO",
        "COMPETENCIA", "VALOR"
    ]
    df_pad["MATRICULA"] = df_pad["MATRICULA"].apply(padronizar_matricula)
    df_pad["RUBRICA"] = pd.to_numeric(df_pad["RUBRICA"], errors="coerce")
    df_pad["COMPETENCIA"] = pd.to_datetime(df_pad["COMPETENCIA"], dayfirst=True, errors="coerce")
    df_pad = remover_linhas_vazias(df_pad)
    return df_pad.reset_index(drop=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def normalizar_hhmm(valor) -> str:
    """
    Converte valor de atraso para string HH:MM.
    Aceita: datetime.time, string '01:30', float (fração do dia).
    """
    if pd.isna(valor):
        return "00:00"
    if hasattr(valor, "hour"):  # datetime.time
        return f"{valor.hour:02d}:{valor.minute:02d}"
    s = str(valor).strip()
    if re.match(r"^\d{1,2}:\d{2}$", s):
        return s
    # float vindo do Excel (fração do dia)
    try:
        f = float(s)
        total_min = round(f * 24 * 60)
        h, m = divmod(total_min, 60)
        return f"{h:02d}:{m:02d}"
    except Exception:
        return s


def extrair_carga_horaria(valor) -> int:
    """
    Extrai número inteiro de carga horária.
    Ex: '12 HORAS' → 12, '30 HORAS' → 30
    """
    if pd.isna(valor):
        return 0
    m = re.search(r"(\d+)", str(valor))
    return int(m.group(1)) if m else 0
