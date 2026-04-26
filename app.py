"""
app.py — Interface Streamlit para o sistema de conferência de RH.
Execute com: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO

from src.leitura import ler_eventos_variaveis, ler_absenteismo, ler_dificil_provimento, ler_previa
from src.padronizacao import (
    padronizar_adn, padronizar_grat_fds, padronizar_atrasos,
    padronizar_falta, padronizar_dificil_provimento, padronizar_previa
)
from src.comparacao import (
    conferir_adn, conferir_grat_fds, conferir_atrasos,
    conferir_faltas, conferir_dificil_provimento, conferir_plantao_rotina
)
from src.exportacao import exportar_resultado
from src.ferias import registrar_ferias, listar_ferias, listar_meses_registrados, remover_mes
from src.padronizacao import padronizar_matricula

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Conferência RH",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 Sistema de Conferência de RH")
st.caption("Validação de eventos variáveis, faltas, difícil provimento e gratificações.")

# ── Sidebar: navegação ────────────────────────────────────────────────────────
pagina = st.sidebar.radio(
    "Navegação",
    ["📋 Conferência Mensal", "🏖️ Gestão de Férias"],
)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1: CONFERÊNCIA MENSAL
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "📋 Conferência Mensal":

    st.header("Conferência Mensal")
    st.info("Faça upload das 4 planilhas do mês e clique em **Executar Conferência**.")

    col1, col2 = st.columns(2)
    with col1:
        mes = st.selectbox("Mês de referência", [f"{m:02d}" for m in range(1, 13)], index=2)
        ano = st.number_input("Ano de referência", min_value=2024, max_value=2030, value=2026)
    with col2:
        st.markdown("**Mês de referência** = mês em que as ocorrências aconteceram (ex: março = 03).")
        st.markdown(f"A competência na prévia será buscada como **{(int(mes) % 12) + 1:02d}/{ano if int(mes) < 12 else ano + 1}**.")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        up_eventos     = st.file_uploader("📁 Eventos Variáveis (eventos.MM.xlsx)",     type="xlsx")
        up_absenteismo = st.file_uploader("📁 Absenteísmo (absenteismo.MM.xlsx)",       type="xlsx")
    with col_b:
        up_dif_prov    = st.file_uploader("📁 Difícil Provimento (dificil_provimento.MM.xlsx)", type="xlsx")
        up_previa      = st.file_uploader("📁 Prévia da Folha (previa.MM.xlsx)",        type="xlsx")

    st.divider()

    if st.button("🔍 Executar Conferência", type="primary", disabled=not all([up_eventos, up_absenteismo, up_dif_prov, up_previa])):

        mes_referencia = f"{mes}/{ano}"

        with st.spinner("Lendo e padronizando dados..."):
            abas_eventos     = ler_eventos_variaveis(up_eventos)
            abas_absenteismo = ler_absenteismo(up_absenteismo)
            df_dif_prov_raw  = ler_dificil_provimento(up_dif_prov)
            df_previa_raw    = ler_previa(up_previa)

            df_adn    = padronizar_adn(abas_eventos["ADN"])
            df_fds    = padronizar_grat_fds(abas_eventos["GRAT_FDS"])
            df_atr    = padronizar_atrasos(abas_eventos["ATRASOS"])
            df_falta  = padronizar_falta(abas_absenteismo["FALTA"])
            df_dp     = padronizar_dificil_provimento(df_dif_prov_raw)
            df_previa = padronizar_previa(df_previa_raw)

        with st.spinner("Executando conferências..."):
            resultados = {
                "ADC NOT":            conferir_adn(df_adn, df_previa, mes_referencia),
                "GRAT FDS":           conferir_grat_fds(df_fds, df_previa, mes_referencia),
                "ATRASOS":            conferir_atrasos(df_atr, df_previa, mes_referencia),
                "FALTAS":             conferir_faltas(df_falta, df_previa, mes_referencia),
                "DIFÍCIL PROVIMENTO": conferir_dificil_provimento(df_dp, df_previa, mes_referencia),
                "PLANTÃO-ROTINA":     conferir_plantao_rotina(df_previa, mes_referencia),
            }

        # ── Métricas resumo ───────────────────────────────────────────────
        st.subheader("📊 Resumo")
        cols = st.columns(len(resultados))
        for i, (nome, df) in enumerate(resultados.items()):
            with cols[i]:
                if df.empty:
                    st.metric(nome, "Sem dados")
                    continue
                criticos = (df["STATUS"].str.startswith("🚨")).sum()
                st.metric(
                    nome,
                    f"{criticos} crítico(s)",
                    delta=f"{len(df)} total",
                    delta_color="off"
                )

        st.divider()

        # ── Abas de resultado ─────────────────────────────────────────────
        abas_ui = st.tabs(["🔴 CRÍTICA"] + list(resultados.keys()))

        # Aba crítica
        with abas_ui[0]:
            criticos = []
            for nome, df in resultados.items():
                if df.empty:
                    continue
                df_c = df[~df["STATUS"].str.startswith("✅")].copy()
                if not df_c.empty:
                    df_c.insert(0, "CONFERÊNCIA", nome)
                    criticos.append(df_c)
            if criticos:
                df_critica = pd.concat(criticos, ignore_index=True)
                st.dataframe(df_critica, use_container_width=True, height=400)
            else:
                st.success("🎉 Nenhuma ocorrência crítica encontrada!")

        # Demais abas
        for i, (nome, df) in enumerate(resultados.items(), start=1):
            with abas_ui[i]:
                if df.empty:
                    st.info("Sem dados para esta conferência.")
                else:
                    st.dataframe(df, use_container_width=True, height=400)

        # ── Download ──────────────────────────────────────────────────────
        st.divider()
        buf = BytesIO()
        exportar_resultado(resultados, buf, mes_referencia)
        buf.seek(0)
        st.download_button(
            label="⬇️ Baixar Relatório Excel",
            data=buf,
            file_name=f"conferencia_{mes}_{ano}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2: GESTÃO DE FÉRIAS
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "🏖️ Gestão de Férias":

    st.header("Gestão de Férias")
    st.info("Registre mensalmente as matrículas que estão de férias. Esse histórico é usado automaticamente nas conferências.")

    col1, col2 = st.columns(2)
    with col1:
        mes_f = st.selectbox("Mês", [f"{m:02d}" for m in range(1, 13)], key="mes_ferias")
    with col2:
        ano_f = st.number_input("Ano", min_value=2024, max_value=2030, value=2026, key="ano_ferias")

    mes_chave = f"{mes_f}/{ano_f}"

    # Matrículas já registradas
    ferias_atuais = listar_ferias(mes_chave)
    st.markdown(f"**Matrículas em férias em {mes_chave}:** {len(ferias_atuais)} registradas")

    # Input de novas matrículas
    st.subheader("Adicionar matrículas")
    st.caption("Cole as matrículas abaixo — uma por linha. Aceita formato 0.000.000-0 ou 00000000.")
    texto = st.text_area("Matrículas", height=150, placeholder="01234567\n02345678\n0.123.456-7")

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("💾 Salvar", type="primary"):
            novas = [padronizar_matricula(m) for m in texto.strip().splitlines() if m.strip()]
            novas = [m for m in novas if m]
            todas = list(set(ferias_atuais + novas))
            registrar_ferias(mes_chave, todas)
            st.success(f"✅ {len(novas)} matrícula(s) adicionada(s). Total: {len(todas)}")
            st.rerun()

    # Visualizar histórico
    st.divider()
    st.subheader("Histórico de férias")
    meses = listar_meses_registrados()
    if meses:
        mes_sel = st.selectbox("Ver mês", meses)
        lista = listar_ferias(mes_sel)
        st.dataframe(pd.DataFrame({"MATRICULA": lista}), use_container_width=True)

        if st.button(f"🗑️ Limpar registros de {mes_sel}", type="secondary"):
            remover_mes(mes_sel)
            st.success(f"Registros de {mes_sel} removidos.")
            st.rerun()
    else:
        st.info("Nenhum mês registrado ainda.")
