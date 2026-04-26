"""
main.py — Ponto de entrada para execução local (sem Streamlit).
Para uso via Streamlit, execute: streamlit run app.py
"""

import sys
from pathlib import Path
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


def rodar_conferencia(mes: str):
    """
    Executa a conferência completa para o mês informado.
    
    Args:
        mes: string no formato 'MM' (ex: '03' para março)
    """
    print(f"\n{'='*50}")
    print(f"  CONFERÊNCIA HR — MÊS DE REFERÊNCIA: {mes}/????")
    print(f"{'='*50}\n")

    # ── Caminhos dos arquivos ──────────────────────────
    arq_eventos      = f"data/eventos.{mes}.xlsx"
    arq_absenteismo  = f"data/absenteismo.{mes}.xlsx"
    arq_dif_prov     = f"data/dificil_provimento.{mes}.xlsx"
    arq_previa       = f"data/previa.{mes}.xlsx"

    for arq in [arq_eventos, arq_absenteismo, arq_dif_prov, arq_previa]:
        if not Path(arq).exists():
            print(f"❌ Arquivo não encontrado: {arq}")
            sys.exit(1)

    # ── Leitura ───────────────────────────────────────
    print("📂 Lendo arquivos...")
    abas_eventos     = ler_eventos_variaveis(arq_eventos)
    abas_absenteismo = ler_absenteismo(arq_absenteismo)
    df_dif_prov_raw  = ler_dificil_provimento(arq_dif_prov)
    df_previa_raw    = ler_previa(arq_previa)

    # ── Padronização ──────────────────────────────────
    print("🔧 Padronizando dados...")
    df_adn    = padronizar_adn(abas_eventos["ADN"])
    df_fds    = padronizar_grat_fds(abas_eventos["GRAT_FDS"])
    df_atr    = padronizar_atrasos(abas_eventos["ATRASOS"])
    df_falta  = padronizar_falta(abas_absenteismo["FALTA"])
    df_dp     = padronizar_dificil_provimento(df_dif_prov_raw)
    df_previa = padronizar_previa(df_previa_raw)

    mes_ref = mes  # ex: '03'
    # Descobrir o ano pela prévia
    anos = df_previa["COMPETENCIA"].dropna().apply(lambda x: x.year).unique()
    ano_ref = int(anos[0]) if len(anos) > 0 else 2026
    mes_referencia = f"{mes_ref}/{ano_ref}"

    # ── Comparação ────────────────────────────────────
    print("🔍 Executando conferências...")
    resultados = {
        "ADC NOT":           conferir_adn(df_adn, df_previa, mes_referencia),
        "GRAT FDS":          conferir_grat_fds(df_fds, df_previa, mes_referencia),
        "ATRASOS":           conferir_atrasos(df_atr, df_previa, mes_referencia),
        "FALTAS":            conferir_faltas(df_falta, df_previa, mes_referencia),
        "DIFÍCIL PROVIMENTO":conferir_dificil_provimento(df_dp, df_previa, mes_referencia),
        "PLANTÃO-ROTINA":    conferir_plantao_rotina(df_previa, mes_referencia),
    }

    # ── Exportação ────────────────────────────────────
    caminho_saida = f"output/conferencia_{mes}_{ano_ref}.xlsx"
    Path("output").mkdir(exist_ok=True)
    exportar_resultado(resultados, caminho_saida, mes_referencia)

    # ── Resumo ────────────────────────────────────────
    print("\n📊 RESUMO:")
    for nome, df in resultados.items():
        if df.empty:
            print(f"  {nome}: sem dados")
            continue
        total   = len(df)
        ok      = (df["STATUS"].str.startswith("✅")).sum()
        critico = (df["STATUS"].str.startswith("🚨")).sum()
        alerta  = (df["STATUS"].str.startswith("🟡")).sum()
        print(f"  {nome}: {ok} OK | {critico} 🚨 críticos | {alerta} 🟡 alertas | {total} total")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python main.py MM")
        print("Exemplo: python main.py 03")
        sys.exit(1)
    rodar_conferencia(sys.argv[1])
