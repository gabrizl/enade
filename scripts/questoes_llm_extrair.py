import csv
import json
import os
import re

PASTA = "relatorios_csv"
ARQUIVO_GERAL = os.path.join(PASTA, "analise_geral_questoes.csv")
ARQUIVO_CACHE = os.path.join(PASTA, "analise_llm_cache_v3.jsonl")

SAIDA_MD = os.path.join(PASTA, "relatorio_llm_questoes.md")
SAIDA_RESUMO = os.path.join(PASTA, "resumo_llm_questoes.csv")
SAIDA_REVISAR = os.path.join(PASTA, "revisar_llm_questoes.csv")
SAIDA_COERENCIA = os.path.join(PASTA, "auditoria_objetivo_conhecimento.csv")

ANOS = {"2014", "2017", "2021"}

def carregar_jsonl(caminho):
    itens = {}
    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                item = json.loads(linha)
                itens[(item["Ano"], item["Questao"])] = item
    return itens


def carregar_tabela_geral(caminho):
    with open(caminho, "r", encoding="utf-8-sig") as f:
        return {(r["Ano"], r["Questao"]): r for r in csv.DictReader(f, delimiter=";")}


def chave_ordenacao(chave):
    """Ordena por ano, componente (FG antes de CE) e número da questão."""
    ano, q = chave
    prefixo, _, num = q.partition("_")
    return (ano, 0 if prefixo == "FG" else 1, int(re.sub(r"\D", "", num) or 0))


def montar_registros(analises, geral):
    """Une a tabela geral com a análise do LLM, só para as questões presentes nos dois."""
    registros = []
    for chave in sorted((k for k in analises if k[0] in ANOS), key=chave_ordenacao):
        base = geral.get(chave)
        if base is None:
            print(f"[AVISO] {chave[0]} {chave[1]} está no cache mas não na tabela geral; ignorada.")
            continue
        registros.append((chave, base, analises[chave]))
    return registros


def precisa_revisao(a):
    return (
        a.get("qualidade_do_item") != "boa"
        or a.get("confianca") != "alta"
        or a.get("coerencia_objetivo_texto") in ("parcial", "incoerente")
    )

def gerar_markdown(registros):
    linhas = ["# Análise por LLM das questões do Enade (UFCG - Ciência da Computação)\n"]

    total = len(registros)
    incoerentes = sum(1 for _, _, a in registros if a.get("coerencia_objetivo_texto") == "incoerente")
    parciais = sum(1 for _, _, a in registros if a.get("coerencia_objetivo_texto") == "parcial")
    problematicas = sum(1 for _, _, a in registros if a.get("qualidade_do_item") == "problematica")
    linhas.append(
        f"**{total} questões analisadas** · {incoerentes} com objetivo incoerente · "
        f"{parciais} parcialmente coerente · {problematicas} item(ns) problemático(s)\n"
    )

    ano_atual = comp_atual = None
    for (ano, q), b, a in registros:
        comp = b.get("Componente", "")

        if ano != ano_atual:
            linhas.append(f"\n---\n\n# {ano}\n")
            ano_atual, comp_atual = ano, None
        if comp != comp_atual:
            linhas.append(f"\n## {comp}\n")
            comp_atual = comp

        linhas.append(f"### {q} — {b.get('Objetivo_de_Conhecimento', '')}\n")
        linhas.append("| Gabarito | Acerto | Nível | A | B | C | D | E | Branco | Alunos |")
        linhas.append("|---|---|---|---|---|---|---|---|---|---|")
        linhas.append(
            f"| {b.get('Gabarito', '-')} | {b.get('Taxa_Acerto_%', '-')}% | {b.get('Nivel_Dificuldade', '-')} | "
            + " | ".join(f"{b.get(f'Pct_{k}', '-')}%" for k in "ABCDE")
            + f" | {b.get('Pct_Branco_Rasura', '-')}% | {b.get('Total_Alunos', '-')} |\n"
        )
        linhas.append(f"**Ementa UFCG:** {b.get('Presenca_na_Ementa_UFCG', '-')} — {b.get('Disciplina_Correspondente_UFCG', '-')}  ")
        linhas.append(f"**Classificação automática:** {b.get('Efeito_Distrator', '-')}  ")
        linhas.append(
            f"**Qualidade (LLM):** {a.get('qualidade_do_item', '-')} · "
            f"**Confiança:** {a.get('confianca', '-')} · "
            f"**Objetivo x enunciado:** {a.get('coerencia_objetivo_texto', '-')}\n"
        )
        if a.get("coerencia_objetivo_texto") in ("parcial", "incoerente"):
            linhas.append(f"> **Coerência do objetivo:** {a.get('justificativa_coerencia', '')}\n")

        linhas.append(f"**Características**\n\n{a.get('caracteristicas_da_questao', '')}\n")
        linhas.append(f"**Leitura dos distratores**\n\n{a.get('leitura_dos_distratores', '')}\n")
        linhas.append(f"**Hipótese de desempenho**\n\n{a.get('hipotese_de_desempenho', '')}\n")
        linhas.append(f"**Justificativa da qualidade**\n\n{a.get('justificativa_qualidade', '')}\n")
        linhas.append(f"**Recomendação pedagógica**\n\n{a.get('recomendacao_pedagogica', '')}\n")

    with open(SAIDA_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(f"[OK] {SAIDA_MD}")

def _limpar_celula(valor):
    """Remove quebras de linha e espaços repetidos; evita que o texto quebre a linha da planilha."""
    if not isinstance(valor, str):
        return valor
    return " ".join(valor.replace("\r", " ").replace("\n", " ").split())


def salvar_csv(dados, caminho):
    if not dados:
        print("[--] Nada para salvar.")
        return
    dados_limpos = [{k: _limpar_celula(v) for k, v in linha.items()} for linha in dados]
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(
            f,
            fieldnames=list(dados_limpos[0].keys()),
            delimiter=";",
            quoting=csv.QUOTE_ALL,
        )
        w.writeheader()
        w.writerows(dados_limpos)
    print(f"[OK] Arquivo gerado em: {caminho}")


def gerar_csvs(registros):
    resumo, revisar, coerencia = [], [], []

    for (ano, q), b, a in registros:
        linha = {
            "Ano": ano,
            "Questao": q,
            "Componente": b.get("Componente", ""),
            "Objetivo_de_Conhecimento": b.get("Objetivo_de_Conhecimento", ""),
            "Gabarito": b.get("Gabarito", ""),
            "Acerto_%": b.get("Taxa_Acerto_%", ""),
            "Nivel_Dificuldade": b.get("Nivel_Dificuldade", ""),
            "Efeito_Distrator": b.get("Efeito_Distrator", ""),
            "Presenca_na_Ementa_UFCG": b.get("Presenca_na_Ementa_UFCG", ""),
            "Coerencia_Objetivo": a.get("coerencia_objetivo_texto", ""),
            "Qualidade_LLM": a.get("qualidade_do_item", ""),
            "Confianca_LLM": a.get("confianca", ""),
            "Recomendacao": a.get("recomendacao_pedagogica", ""),
        }
        resumo.append(linha)

        if precisa_revisao(a):
            revisar.append(linha)

        if a.get("coerencia_objetivo_texto") in ("parcial", "incoerente"):
            coerencia.append({
                "Ano": ano,
                "Questao": q,
                "Objetivo_Atribuido": b.get("Objetivo_de_Conhecimento", ""),
                "Disciplina_Mapeada_UFCG": b.get("Disciplina_Correspondente_UFCG", ""),
                "Coerencia": a.get("coerencia_objetivo_texto", ""),
                "Justificativa": a.get("justificativa_coerencia", ""),
                "Caracteristicas_LLM": a.get("caracteristicas_da_questao", ""),
            })

    salvar_csv(resumo, SAIDA_RESUMO)
    salvar_csv(revisar, SAIDA_REVISAR)
    salvar_csv(coerencia, SAIDA_COERENCIA)


if __name__ == "__main__":
    analises = carregar_jsonl(ARQUIVO_CACHE)
    geral = carregar_tabela_geral(ARQUIVO_GERAL)
    registros = montar_registros(analises, geral)
    gerar_markdown(registros)
    gerar_csvs(registros)