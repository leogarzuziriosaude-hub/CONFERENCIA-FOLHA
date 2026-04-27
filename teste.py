from src.leitura import ler_eventos_variaveis, ler_previa
from src.padronizacao import padronizar_adn, padronizar_previa
from src.comparacao import conferir_adn

abas = ler_eventos_variaveis("data/eventos.03.xlsx")
df_previa_raw = ler_previa("data/previa.03.xlsx")

df_adn = padronizar_adn(abas["ADN"])
df_previa = padronizar_previa(df_previa_raw)

resultado = conferir_adn(df_adn, df_previa, "03/2026")

ok = resultado[resultado["STATUS"] == "✅ OK"].head(2)
nao_lancado = resultado[resultado["STATUS"] == "🚨 NÃO LANÇADO"].head(2)
indevido = resultado[resultado["STATUS"] == "🚨 LANÇAMENTO INDEVIDO"].head(2)

print("✅ OK:")
print(ok[["MATRICULA", "PREFIXO", "RUBRICA_ESPERADA"]].to_string())
print("\n🚨 NÃO LANÇADO:")
print(nao_lancado[["MATRICULA", "PREFIXO", "RUBRICA_ESPERADA"]].to_string())
print("\n🚨 INDEVIDO:")
print(indevido[["MATRICULA", "PREFIXO", "RUBRICA_ESPERADA"]].to_string())