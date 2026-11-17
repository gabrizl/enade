import csv
import os
import statistics
import subprocess
from collections import Counter, defaultdict

ARQUIVO_PPC_PDF = os.path.join("documentos", "computacaoPPC2023atualizado-final.pdf")
ARQUIVO_RANKING = "relatorios_csv/ranking_questoes_por_ano.csv"
ARQUIVO_SAIDA_QUESTOES = "relatorios_csv/aderencia_ementa_ppc2023_questoes.csv"
ARQUIVO_SAIDA_RESUMO = "relatorios_csv/resumo_aderencia_ppc2023.csv"

# Mapeamento oficial entre Objetivos de Conhecimento (ENADE) e Disciplinas do PPC 2023 (UFCG)
MAPA_PPC_2023 = {
    # --- COMPONENTE ESPECÍFICO ---
    "Algoritmos e Estruturas de Dados": ("Obrigatória", ["Estruturas de Dados e Algoritmos", "Análise e Técnicas de Algoritmos"]),
    "Banco de Dados": ("Obrigatória", ["Banco de Dados I"]),
    "Bancos de Dados": ("Obrigatória", ["Banco de Dados I"]),
    "Compiladores": ("Obrigatória", ["Compiladores"]),
    "Engenharia de Software": ("Obrigatória", ["Engenharia de Software", "Análise de Sistemas", "Projeto de Software"]),
    "Engenharia de Software e Interação Homem-Computador": ("Obrigatória", ["Engenharia de Software"]),
    "Fundamentos e Técnicas de Programação": ("Obrigatória", ["Programação I", "Programação II", "Introdução à Computação"]),
    "Inteligência Artificial": ("Obrigatória", ["Inteligência Artificial"]),
    "Inteligência Artificial e Computacional": ("Obrigatória", ["Inteligência Artificial"]),
    "Linguagens Formais, Autômatos e Compiladores": ("Obrigatória", ["Teoria da Computação", "Compiladores"]),
    "Lógica e Matemática Discreta": ("Obrigatória", ["Lógica para Computação", "Fundamentos de Matemática para Ciência da Computação I", "Fundamentos de Matemática para Ciência da Computação II"]),
    "Organização e Arquitetura de Computadores": ("Obrigatória", ["Organização e Arquitetura de Computadores"]),
    "Arquitetura de Computadores e Sistemas Operacionais": ("Obrigatória", ["Organização e Arquitetura de Computadores", "Sistemas Operacionais"]),
    "Paradigmas de Linguagens de Programação": ("Obrigatória", ["Paradigmas de Linguagens de Programação"]),
    "Probabilidade e Estatística": ("Obrigatória", ["Introdução à Probabilidade", "Estatística Aplicada"]),
    "Redes de Computadores": ("Obrigatória", ["Redes de Computadores"]),
    "Redes de Computadores e Sistemas Distribuídos": ("Obrigatória", ["Redes de Computadores"]),
    "Sistemas Operacionais": ("Obrigatória", ["Sistemas Operacionais", "Programação Concorrente"]),
    "Sistemas Operacionais e Arquitetura de Computadores": ("Obrigatória", ["Sistemas Operacionais", "Organização e Arquitetura de Computadores"]),
    "Teoria da Computabilidade e Complexidade": ("Obrigatória", ["Teoria da Computação", "Análise e Técnicas de Algoritmos"]),
    "Teoria da Computação": ("Obrigatória", ["Teoria da Computação"]),
    "Teoria dos Grafos": ("Obrigatória", ["Teoria dos Grafos"]),
    "Ética, Computador e Sociedade": ("Obrigatória", ["Direito e Cidadania"]),

    # --- OPTATIVAS NO PPC 2023 ---
    "Computação Gráfica e Processamento de Imagem": ("Optativa", ["Computação Gráfica", "Percepção Computacional"]),
    "Interação Homem-Computador": ("Optativa", ["Interface Humano-Computador"]),
    "Sistemas Digitais": ("Optativa", ["Projeto de Sistemas Digitais"]),
    "Sistemas Distribuídos": ("Optativa", ["Sistemas Distribuídos"]),

    # --- FORMAÇÃO GERAL (TRANSVERSAIS / SOCIEDADE) ---
    "Ciência, tecnologia e inovação": ("Formação Geral (Parcial em Obrigatória)", ["Direito e Cidadania", "Metodologia Científica"]),
    "Tecnologias de informação e comunicação": ("Formação Geral (Parcial em Optativa)", ["Informática e Sociedade"]),
    "Tecnologias de Informação e Comunicação": ("Formação Geral (Parcial em Optativa)", ["Informática e Sociedade"]),
    "Inovação tecnológica": ("Formação Geral (Parcial em Obrigatória)", ["Direito e Cidadania"]),
    "Avanços tecnológicos": ("Formação Geral (Parcial em Optativa)", ["Informática e Sociedade"]),
    "Ética, democracia e cidadania": ("Formação Geral (Parcial em Obrigatória)", ["Direito e Cidadania"]),
    "Sociodiversidade e multiculturalismo (violência, tolerância/intolerância, inclusão/exclusão e relações de gênero);": ("Formação Geral (Parcial em Obrigatória)", ["Direito e Cidadania"]),
}


def extrair_ementas_ppc2023():
    """Extrai o texto do PPC 2023 via pdftotext e devolve dicionário {nome_disciplina: (tipo, ementa)}."""
    if not os.path.exists(ARQUIVO_PPC_PDF):
        raise FileNotFoundError(f"Arquivo PPC não encontrado: {ARQUIVO_PPC_PDF}")

    res = subprocess.run(["pdftotext", ARQUIVO_PPC_PDF, "-"], capture_output=True, text=True, check=True)
    lines = [l.strip() for l in res.stdout.splitlines()]

    opt_start = next(i for i, l in enumerate(lines) if i > 3942 and "Componentes Curriculares Optativos" in l)
    ementas = {}
    i = 3942
    while i < len(lines):
        if lines[i].startswith("COMPONENTE CURRICULAR:"):
            nome = lines[i].replace("COMPONENTE CURRICULAR:", "").strip()
            if not nome and i + 1 < len(lines):
                nome = lines[i + 1].strip()
            tipo = "Optativa" if i > opt_start else "Obrigatória"
            j = i + 1
            while j < len(lines) and lines[j] != "EMENTA:":
                j += 1
            em = []
            if j < len(lines) and lines[j] == "EMENTA:":
                k = j + 1
                while k < len(lines) and not lines[k].startswith("BIBLIOGRAFIA"):
                    if lines[k]:
                        em.append(lines[k])
                    k += 1
            ementas[nome] = (tipo, " ".join(em))
        i += 1
    return ementas


def analisar_aderencia():
    ementas_ppc = extrair_ementas_ppc2023()
    print(f"[OK] Extraídas {len(ementas_ppc)} ementas oficiais do {ARQUIVO_PPC_PDF}.")

    with open(ARQUIVO_RANKING, "r", encoding="utf-8-sig") as f:
        ranking = list(csv.DictReader(f, delimiter=";"))

    # Analisar questões dos anos com Objetivo_de_Conhecimento mapeado (2014, 2017, 2021)
    questoes_mapeadas = [r for r in ranking if r["Ano"] in ("2014", "2017", "2021")]

    linhas_questoes = []
    for r in questoes_mapeadas:
        obj = r["Objetivo_de_Conhecimento"]
        comp = r["Componente"]

        if obj in MAPA_PPC_2023:
            cat_ppc, discs = MAPA_PPC_2023[obj]
        elif "Geral" in comp:
            cat_ppc, discs = ("Formação Geral (Fora da Ementa de CC)", [])
        else:
            cat_ppc, discs = ("Não Mapeada no PPC", [])

        if cat_ppc == "Obrigatória":
            aderencia = "Sim - Núcleo Obrigatório (PPC 2023)"
        elif cat_ppc == "Optativa":
            aderencia = "Parcial - Apenas em Optativa (PPC 2023)"
        elif "Parcial em Obrigatória" in cat_ppc:
            aderencia = "Sim - Transversal em Obrigatória (Direito/Metodologia)"
        elif "Parcial em Optativa" in cat_ppc:
            aderencia = "Parcial - Transversal em Optativa (Inf. e Sociedade)"
        else:
            aderencia = "Não - Tema Geral Externo ao Currículo de CC"

        trechos = []
        for d in discs:
            if d in ementas_ppc:
                _, em = ementas_ppc[d]
                trechos.append(f"[{d}]: {em[:180]}...")
        trecho_str = " | ".join(trechos) if trechos else "Conteúdo de Formação Geral (MEC/INEP)"

        linhas_questoes.append({
            "Ano": r["Ano"],
            "Questao": r["Questao"],
            "Componente": comp,
            "Objetivo_de_Conhecimento": obj,
            "Status_Questao": r["Status"],
            "Taxa_Acerto_%": r["Taxa_Acerto_%"],
            "Dificuldade": r["Dificuldade"],
            "Categoria_PPC_2023": cat_ppc,
            "Aderencia_Ementa": aderencia,
            "Disciplinas_PPC_2023": ", ".join(discs) if discs else "-",
            "Trecho_Ementa_PPC_2023": trecho_str,
        })

    # Salvar tabela por questão
    os.makedirs(os.path.dirname(ARQUIVO_SAIDA_QUESTOES), exist_ok=True)
    with open(ARQUIVO_SAIDA_QUESTOES, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(linhas_questoes[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(linhas_questoes)
    print(f"[OK] Aderência por questão salva em: {ARQUIVO_SAIDA_QUESTOES}")

    # Gerar resumo quantitativo por Categoria PPC e por Ano
    validas = [q for q in linhas_questoes if q["Status_Questao"] == "Válida"]
    grupos = defaultdict(list)
    for q in validas:
        if q["Categoria_PPC_2023"] == "Obrigatória":
            g = "CE - Obrigatória no PPC 2023"
        elif q["Categoria_PPC_2023"] == "Optativa":
            g = "CE - Optativa no PPC 2023"
        else:
            g = "Formação Geral (FG)"
        grupos[("Consolidado (2014–2021)", g)].append(q)
        grupos[(q["Ano"], g)].append(q)

    resumo_rows = []
    for (periodo, grupo), qs in sorted(grupos.items()):
        taxas = [float(x["Taxa_Acerto_%"]) for x in qs]
        dificeis = sum(1 for x in qs if x["Dificuldade"] in ("Muito difícil", "Difícil"))
        faceis = sum(1 for x in qs if x["Dificuldade"] in ("Fácil", "Muito fácil"))
        resumo_rows.append({
            "Periodo": periodo,
            "Categoria_Curricular": grupo,
            "Qtd_Questoes_Validas": len(qs),
            "Media_Acerto_%": round(statistics.mean(taxas), 2),
            "Mediana_Acerto_%": round(statistics.median(taxas), 2),
            "Qtd_Dificil_MuitoDificil": dificeis,
            "Pct_Dificil_MuitoDificil": round(dificeis / len(qs) * 100, 1),
            "Qtd_Facil_MuitoFacil": faceis,
            "Pct_Facil_MuitoFacil": round(faceis / len(qs) * 100, 1),
        })

    with open(ARQUIVO_SAIDA_RESUMO, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(resumo_rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(resumo_rows)
    print(f"[OK] Resumo de aderência salvo em: {ARQUIVO_SAIDA_RESUMO}")

    print("\n=== RESUMO QUANTITATIVO: ADERÊNCIA À EMENTA PPC 2023 ===")
    for r in resumo_rows:
        print(f"{r['Periodo']:<24} | {r['Categoria_Curricular']:<30} | Qtd: {r['Qtd_Questoes_Validas']:2d} | Média: {r['Media_Acerto_%']:5.2f}% | Difíceis: {r['Pct_Dificil_MuitoDificil']:4.1f}% | Fáceis: {r['Pct_Facil_MuitoFacil']:4.1f}%")


if __name__ == "__main__":
    analisar_aderencia()
