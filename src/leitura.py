import pandas as pd


def ler_eventos_variaveis(caminho_arquivo):
    """
    Lê a planilha de eventos variáveis (eventos.MM.xlsx).
    Abas: ADC NOT, GRAT FDS, ATRASOS
    Dados começam na linha 4 (header=2 no pandas).
    """
    abas = {
        "ADN": pd.read_excel(caminho_arquivo, sheet_name="ADC NOT", header=2),
        "GRAT_FDS": pd.read_excel(caminho_arquivo, sheet_name="GRAT FDS", header=2),
        "ATRASOS": pd.read_excel(caminho_arquivo, sheet_name="ATRASOS", header=2),
    }
    return abas


def ler_absenteismo(caminho_arquivo):
    """
    Lê a planilha de absenteismo (absenteismo.MM.xlsx).
    Abas: ATESTADO, FALTA - INJUSTIFICADA
    Dados começam na linha 4 (header=2 no pandas).
    """
    abas = {
        "ATESTADO": pd.read_excel(caminho_arquivo, sheet_name="ATESTADO", header=2),
        "FALTA": pd.read_excel(caminho_arquivo, sheet_name="FALTA - INJUSTIFICADA", header=2),
    }
    return abas


def ler_dificil_provimento(caminho_arquivo):
    """
    Lê a planilha de difícil provimento (dificil_provimento.MM.xlsx).
    Dados começam na linha 2 (header=0 no pandas).
    Colunas: A=PREF, B=MATRICULA, C=NOME, D=CARGO, E=HORAS
    """
    df = pd.read_excel(caminho_arquivo, header=0)
    return df


def ler_previa(caminho_arquivo):
    """
    Lê a planilha da prévia da folha de pagamento (previa.MM.xlsx).
    Colunas relevantes:
        A=PREF, B=MATRICULA, C=NOME, E=CARGO, H=CARGA_HORARIA,
        K=RUBRICA, L=DESCRICAO, O=COMPETENCIA, P=VALOR
    """
    df = pd.read_excel(caminho_arquivo, header=0)
    return df
# teste commit
