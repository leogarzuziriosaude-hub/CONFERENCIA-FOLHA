"""
Módulo de comparação e validação.
Cada função recebe os dados padronizados + a prévia e retorna um DataFrame
com o resultado da conferência (OK, AUSENTE, INDEVIDO, FERIAS).
"""

import pandas as pd
from src.padronizacao import get_rubrica, extrair_carga_horaria
from src.ferias import esta_de_ferias


STATUS_OK = "✅ OK"
STATUS_AUSENTE = "🚨 NÃO LANÇADO"
STATUS_INDEVIDO = "🚨 LANÇAMENTO INDEVIDO"
STATUS_FERIAS = "🟡 DE FÉRIAS"
STATUS_POSTERGADO = "🟡 POSTERGADO (FÉRIAS)"


def _competencia_str(dt) -> str:
    """Converte datetime para string 'MM/AAAA'."""
    if pd.isna(dt):
        return ""
    return pd.Timestamp(dt).strftime("%m/%Y")


def _proximo_mes(competencia: str) -> str:
    """Retorna o mês seguinte no formato 'MM/AAAA'."""
    mes, ano = int(competencia[:2]), int(competencia[3:])
    mes += 1
    if mes > 12:
        mes = 1
        ano += 1
    return f"{mes:02d}/{ano}"


def _mes_da_data(data) -> str:
    """Extrai 'MM/AAAA' de uma data."""
    try:
        return pd.Timestamp(data).strftime("%m/%Y")
    except Exception:
        return ""


def _competencia_envio(mes_referencia: str) -> str:
    """
    Calcula a competência de pagamento dado o mês de referência.
    Regra: competência = mês de referência + 1
    Ex: março (03/2026) → competência 04/2026
    """
    return _proximo_mes(mes_referencia)


# ─────────────────────────────────────────────
# ADICIONAL NOTURNO
# ─────────────────────────────────────────────

def conferir_adn(df_adn: pd.DataFrame, df_previa: pd.DataFrame, mes_referencia: str) -> pd.DataFrame:
    """
    Confere o Adicional Noturno.
    - Competência na prévia = mes_referencia + 1
    - Se não pago e está de férias → FERIAS
    - Se não pago e não está de férias → AUSENTE
    - Se está na prévia mas não enviamos → INDEVIDO
    """
    competencia = _competencia_envio(mes_referencia)
    resultados = []

    # Matrículas que enviamos
    enviadas = set(df_adn["MATRICULA"].unique())

    # Filtrar prévia pela rubrica correta e competência
    previa_adn = df_previa[
        df_previa["COMPETENCIA"].apply(_competencia_str) == competencia
    ].copy()

    for _, row in df_adn.iterrows():
        mat = row["MATRICULA"]
        pref = row["PREF"]
        rubrica = get_rubrica("ADN", pref)

        na_previa = not previa_adn[
            (previa_adn["MATRICULA"] == mat) & (previa_adn["RUBRICA"] == rubrica)
        ].empty

        if na_previa:
            status = STATUS_OK
        elif esta_de_ferias(mat, competencia):
            status = STATUS_FERIAS
        else:
            status = STATUS_AUSENTE

        resultados.append({
            "PREFIXO": pref,
            "MATRICULA": mat,
            "COMPETENCIA": competencia,
            "RUBRICA_ESPERADA": rubrica,
            "STATUS": status,
        })

    # INDEVIDOS: na prévia com rubrica ADN mas não enviamos
    rubricas_adn = [get_rubrica("ADN", p) for p in df_previa["PREF"].unique()]
    indevidos = previa_adn[
        previa_adn["RUBRICA"].isin([3037, 703]) &
        ~previa_adn["MATRICULA"].isin(enviadas)
    ]
    for _, row in indevidos.iterrows():
        resultados.append({
            "PREFIXO": row["PREF"],
            "MATRICULA": row["MATRICULA"],
            "COMPETENCIA": competencia,
            "RUBRICA_ESPERADA": row["RUBRICA"],
            "STATUS": STATUS_INDEVIDO,
        })

    return pd.DataFrame(resultados)


# ─────────────────────────────────────────────
# GRATIFICAÇÃO FIM DE SEMANA
# ─────────────────────────────────────────────

def conferir_grat_fds(df_fds: pd.DataFrame, df_previa: pd.DataFrame, mes_referencia: str) -> pd.DataFrame:
    """
    Confere a Gratificação de Fim de Semana.
    Mesma lógica do ADN — uma matrícula pode ter múltiplos dias,
    mas basta verificar se a rubrica aparece na prévia.
    """
    competencia = _competencia_envio(mes_referencia)
    resultados = []

    enviadas = set(df_fds["MATRICULA"].unique())

    previa_fds = df_previa[
        df_previa["COMPETENCIA"].apply(_competencia_str) == competencia
    ].copy()

    for mat in enviadas:
        pref = df_fds[df_fds["MATRICULA"] == mat]["PREF"].iloc[0]
        rubrica = get_rubrica("GRAT_FDS", pref)

        na_previa = not previa_fds[
            (previa_fds["MATRICULA"] == mat) & (previa_fds["RUBRICA"] == rubrica)
        ].empty

        if na_previa:
            status = STATUS_OK
        elif esta_de_ferias(mat, competencia):
            status = STATUS_FERIAS
        else:
            status = STATUS_AUSENTE

        resultados.append({
            "PREFIXO": pref,
            "MATRICULA": mat,
            "COMPETENCIA": competencia,
            "RUBRICA_ESPERADA": rubrica,
            "STATUS": status,
        })

    # INDEVIDOS
    indevidos = previa_fds[
        previa_fds["RUBRICA"].isin([3120, 710]) &
        ~previa_fds["MATRICULA"].isin(enviadas)
    ]
    for _, row in indevidos.iterrows():
        resultados.append({
            "PREFIXO": row["PREF"],
            "MATRICULA": row["MATRICULA"],
            "COMPETENCIA": competencia,
            "RUBRICA_ESPERADA": row["RUBRICA"],
            "STATUS": STATUS_INDEVIDO,
        })

    return pd.DataFrame(resultados)


# ─────────────────────────────────────────────
# ATRASOS (IMPONTUALIDADES)
# ─────────────────────────────────────────────

def conferir_atrasos(df_atrasos: pd.DataFrame, df_previa: pd.DataFrame, mes_referencia: str) -> pd.DataFrame:
    """
    Confere descontos de impontualidade.
    Comportamento da sede quando em férias: posterga para mês seguinte.
    """
    competencia = _competencia_envio(mes_referencia)
    competencia_seguinte = _proximo_mes(competencia)
    resultados = []

    enviadas = set(df_atrasos["MATRICULA"].unique())

    previa_comp = df_previa[df_previa["COMPETENCIA"].apply(_competencia_str) == competencia].copy()
    previa_comp2 = df_previa[df_previa["COMPETENCIA"].apply(_competencia_str) == competencia_seguinte].copy()

    for mat in enviadas:
        pref = df_atrasos[df_atrasos["MATRICULA"] == mat]["PREF"].iloc[0]
        rubrica = get_rubrica("ATRASOS", pref)

        na_previa = not previa_comp[
            (previa_comp["MATRICULA"] == mat) & (previa_comp["RUBRICA"] == rubrica)
        ].empty

        if na_previa:
            status = STATUS_OK
        elif esta_de_ferias(mat, competencia):
            # Verificar se aparece no mês seguinte
            na_previa2 = not previa_comp2[
                (previa_comp2["MATRICULA"] == mat) & (previa_comp2["RUBRICA"] == rubrica)
            ].empty
            status = STATUS_POSTERGADO if na_previa2 else STATUS_FERIAS
        else:
            status = STATUS_AUSENTE

        resultados.append({
            "PREFIXO": pref,
            "MATRICULA": mat,
            "COMPETENCIA": competencia,
            "RUBRICA_ESPERADA": rubrica,
            "STATUS": status,
        })

    # INDEVIDOS
    indevidos = previa_comp[
        previa_comp["RUBRICA"].isin([3507, 1054]) &
        ~previa_comp["MATRICULA"].isin(enviadas)
    ]
    for _, row in indevidos.iterrows():
        resultados.append({
            "PREFIXO": row["PREF"],
            "MATRICULA": row["MATRICULA"],
            "COMPETENCIA": competencia,
            "RUBRICA_ESPERADA": row["RUBRICA"],
            "STATUS": STATUS_INDEVIDO,
        })

    return pd.DataFrame(resultados)


# ─────────────────────────────────────────────
# FALTAS
# ─────────────────────────────────────────────

def conferir_faltas(df_falta: pd.DataFrame, df_previa: pd.DataFrame, mes_referencia: str) -> pd.DataFrame:
    """
    Confere descontos de falta.
    Comportamento da sede quando em férias: posterga para mês seguinte.
    """
    competencia = _competencia_envio(mes_referencia)
    competencia_seguinte = _proximo_mes(competencia)
    resultados = []

    enviadas = set(df_falta["MATRICULA"].unique())

    previa_comp = df_previa[df_previa["COMPETENCIA"].apply(_competencia_str) == competencia].copy()
    previa_comp2 = df_previa[df_previa["COMPETENCIA"].apply(_competencia_str) == competencia_seguinte].copy()

    for mat in enviadas:
        pref = df_falta[df_falta["MATRICULA"] == mat]["PREF"].iloc[0]
        rubrica = get_rubrica("FALTA", pref)

        na_previa = not previa_comp[
            (previa_comp["MATRICULA"] == mat) & (previa_comp["RUBRICA"] == rubrica)
        ].empty

        if na_previa:
            status = STATUS_OK
        elif esta_de_ferias(mat, competencia):
            na_previa2 = not previa_comp2[
                (previa_comp2["MATRICULA"] == mat) & (previa_comp2["RUBRICA"] == rubrica)
            ].empty
            status = STATUS_POSTERGADO if na_previa2 else STATUS_FERIAS
        else:
            status = STATUS_AUSENTE

        resultados.append({
            "PREFIXO": pref,
            "MATRICULA": mat,
            "COMPETENCIA": competencia,
            "RUBRICA_ESPERADA": rubrica,
            "STATUS": status,
        })

    # INDEVIDOS
    indevidos = previa_comp[
        previa_comp["RUBRICA"].isin([3506, 1065]) &
        ~previa_comp["MATRICULA"].isin(enviadas)
    ]
    for _, row in indevidos.iterrows():
        resultados.append({
            "PREFIXO": row["PREF"],
            "MATRICULA": row["MATRICULA"],
            "COMPETENCIA": competencia,
            "RUBRICA_ESPERADA": row["RUBRICA"],
            "STATUS": STATUS_INDEVIDO,
        })

    return pd.DataFrame(resultados)


# ─────────────────────────────────────────────
# DIFÍCIL PROVIMENTO
# ─────────────────────────────────────────────

def conferir_dificil_provimento(df_dp: pd.DataFrame, df_previa: pd.DataFrame, mes_referencia: str) -> pd.DataFrame:
    """
    Confere a Gratificação de Difícil Provimento.
    """
    competencia = _competencia_envio(mes_referencia)
    resultados = []

    enviadas = set(df_dp["MATRICULA"].unique())

    previa_comp = df_previa[df_previa["COMPETENCIA"].apply(_competencia_str) == competencia].copy()

    for mat in enviadas:
        pref = df_dp[df_dp["MATRICULA"] == mat]["PREF"].iloc[0]
        rubrica = get_rubrica("DIF_PROV", pref)

        na_previa = not previa_comp[
            (previa_comp["MATRICULA"] == mat) & (previa_comp["RUBRICA"] == rubrica)
        ].empty

        if na_previa:
            status = STATUS_OK
        elif esta_de_ferias(mat, competencia):
            status = STATUS_FERIAS
        else:
            status = STATUS_AUSENTE

        resultados.append({
            "PREFIXO": pref,
            "MATRICULA": mat,
            "COMPETENCIA": competencia,
            "RUBRICA_ESPERADA": rubrica,
            "STATUS": status,
        })

    # INDEVIDOS
    indevidos = previa_comp[
        previa_comp["RUBRICA"].isin([3195, 1053]) &
        ~previa_comp["MATRICULA"].isin(enviadas)
    ]
    for _, row in indevidos.iterrows():
        resultados.append({
            "PREFIXO": row["PREF"],
            "MATRICULA": row["MATRICULA"],
            "COMPETENCIA": competencia,
            "RUBRICA_ESPERADA": row["RUBRICA"],
            "STATUS": STATUS_INDEVIDO,
        })

    return pd.DataFrame(resultados)


# ─────────────────────────────────────────────
# GRATIFICAÇÃO DE PLANTÃO / ROTINA
# ─────────────────────────────────────────────

def conferir_plantao_rotina(df_previa: pd.DataFrame, mes_referencia: str) -> pd.DataFrame:
    """
    Confere se médicos plantonistas e de rotina estão recebendo as gratificações corretas.
    Baseado inteiramente na prévia (cargo + carga horária).

    Plantonista: qualquer médico com CH 12h, 24h ou 36h → rubrica 3147/716
    Rotina: Médico Intensivista ou Clínico com CH 30h → rubrica 3154/719
    Ambulatório: resto → não confere
    """
    competencia = _competencia_envio(mes_referencia)
    resultados = []

    previa_comp = df_previa[
        df_previa["COMPETENCIA"].apply(_competencia_str) == competencia
    ].copy()

    # Pegar colaboradores únicos com cargo/CH
    colaboradores = previa_comp[["PREF", "MATRICULA", "NOME", "CARGO", "CARGA_HORARIA"]].drop_duplicates(
        subset=["MATRICULA"]
    )

    for _, col in colaboradores.iterrows():
        mat = col["MATRICULA"]
        pref = col["PREF"]
        cargo = str(col["CARGO"]).upper() if pd.notna(col["CARGO"]) else ""
        ch = extrair_carga_horaria(col["CARGA_HORARIA"])

        # Só analisa médicos
        if "MEDICO" not in cargo and "MÉDICO" not in cargo:
            continue

        # Classificar
        if ch in [12, 24, 36]:
            classe = "PLANTONISTA"
            rubrica = get_rubrica("PLANTAO", pref)
        elif ch == 30 and ("INTENSIVISTA" in cargo or "CLINICO" in cargo or "CLÍNICO" in cargo):
            classe = "ROTINA"
            rubrica = get_rubrica("ROTINA", pref)
        else:
            continue  # Ambulatório — não confere

        # Verificar na prévia
        na_previa = not previa_comp[
            (previa_comp["MATRICULA"] == mat) & (previa_comp["RUBRICA"] == rubrica)
        ].empty

        if na_previa:
            status = STATUS_OK
        elif esta_de_ferias(mat, competencia):
            status = STATUS_FERIAS
        else:
            status = STATUS_AUSENTE

        resultados.append({
            "PREFIXO": pref,
            "MATRICULA": mat,
            "NOME": col["NOME"],
            "CARGO": col["CARGO"],
            "CARGA_HORARIA": col["CARGA_HORARIA"],
            "CLASSE": classe,
            "COMPETENCIA": competencia,
            "RUBRICA_ESPERADA": rubrica,
            "STATUS": status,
        })

    return pd.DataFrame(resultados)
