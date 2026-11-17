import csv
import json
import os
import re
import time

from groq import Groq, APIError, RateLimitError

PASTA_RELATORIOS = "relatorios_csv"
ARQUIVO_ANALISE_GERAL = os.path.join(PASTA_RELATORIOS, "analise_geral_questoes.csv")
ARQUIVO_ANALISE_LLM = os.path.join(PASTA_RELATORIOS, "analise_geral_questoes_llm.csv")
ARQUIVO_CACHE = os.path.join(PASTA_RELATORIOS, "analise_llm_cache_v3.jsonl")  # prompt mudou: cache novo
ARQUIVO_OBJETIVOS = os.path.join(
    PASTA_RELATORIOS, "Enade_Objetivo_Conhecimento - Enade_Objetivo_Conhecimento.csv"
)
if not os.path.exists(ARQUIVO_OBJETIVOS):
    ARQUIVO_OBJETIVOS = "Enade_Objetivo_Conhecimento - Enade_Objetivo_Conhecimento.csv"

ANOS = {"2014", "2017", "2021"}
LIMITE_CHARS_ENUNCIADO = 5000

MODELO = "openai/gpt-oss-120b"
client = Groq()  # usa a variável de ambiente GROQ_API_KEY

SYSTEM_PROMPT = SYSTEM_PROMPT = """Você é especialista em avaliação educacional e em Ciência da Computação.
Analisa questões do Enade respondidas por alunos de Ciência da Computação da UFCG.

ENTRADA
Para cada questão você recebe: o enunciado com as alternativas, o gabarito, o desempenho
(taxa de acerto e % de cada alternativa), o objetivo de conhecimento atribuído e a disciplina
da UFCG correspondente.

TAREFA
1. Identifique o tipo de item (múltipla escolha, asserção-razão, afirmativas I/II/III, código, figura),
   o tema real e o nível cognitivo (lembrar, compreender, aplicar ou analisar).
2. Confira se o tema real combina com o objetivo de conhecimento atribuído.
3. Explique o desempenho a partir da distribuição das respostas, citando as alternativas pela letra.
4. Avalie a qualidade do item e recomende uma ação pedagógica.

REGRAS
- Use somente o que está na entrada. Não invente o conteúdo de alternativas, figuras ou trechos
  ausentes. Se o enunciado estiver truncado ou tiver "[FIGURA...]", diga que essa parte não pôde
  ser avaliada e reduza a confiança.
- O gabarito informado é a referência de resposta correta; não o contradiga.
- Marque causas prováveis como hipótese ("possivelmente...").
- Se o acerto é alto e os distratores pouco atrativos, diga isso em uma frase, sem inventar problemas.
- Turmas pequenas: com 56 alunos, 1 aluno vale cerca de 1,8 ponto percentual. Evite concluir
  algo de distratores com poucos pontos percentuais.
- A "classificação automática" é só uma heurística; você pode discordar dela.
- Seja direto: cada campo de texto deve ter no máximo 2 frases curtas, sem listas e sem quebras de linha.

SAÍDA
Responda somente com um objeto JSON válido, com estas chaves:
{
  "caracteristicas_da_questao": "tipo de item, tema real, nível cognitivo",
  "coerencia_objetivo_texto": "coerente" | "parcial" | "incoerente" | "indeterminada",
  "justificativa_coerencia": "se não for coerente, diga qual seria o tema real; senão, uma frase",
  "leitura_dos_distratores": "o que a distribuição A-E indica, citando letras",
  "hipotese_de_desempenho": "por que os alunos acertaram ou erraram",
  "qualidade_do_item": "boa" | "atencao" | "problematica",
  "justificativa_qualidade": "motivo da classificação acima",
  "recomendacao_pedagogica": "uma ação concreta para o curso",
  "confianca": "alta" | "media" | "baixa"
}
"""

def carregar_tabela_geral(caminho=ARQUIVO_ANALISE_GERAL):
    with open(caminho, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


def carregar_textos_questoes(caminho=ARQUIVO_OBJETIVOS):
    """Lê o CSV de objetivos e devolve {(ano, questao): texto_questao}."""
    textos = {}
    if not os.path.exists(caminho):
        print(f"[AVISO] Arquivo de textos não encontrado: {caminho}")
        return textos

    with open(caminho, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):  # separador vírgula, como no seu código original
            limpo = {(k or "").strip(): (v or "").strip()
                     for k, v in row.items() if isinstance(v, str)}
            ano, q = limpo.get("Ano", ""), limpo.get("Questao", "")
            texto = re.sub(r"\s+", " ", limpo.get("texto_questao", ""))
            if ano and q and texto:
                textos[(ano, q)] = texto
    return textos


def carregar_cache():
    cache = {}
    if os.path.exists(ARQUIVO_CACHE):
        with open(ARQUIVO_CACHE, "r", encoding="utf-8") as f:
            for linha in f:
                if linha.strip():
                    item = json.loads(linha)
                    cache[(item["Ano"], item["Questao"])] = item
    return cache

def montar_prompt(linha, texto_questao):
    distribuicao = {k: linha[f"Pct_{k}"] for k in "ABCDE"}
    if texto_questao:
        if len(texto_questao) > LIMITE_CHARS_ENUNCIADO:
            enunciado = "[...início do texto omitido] " + texto_questao[-LIMITE_CHARS_ENUNCIADO:]
        else:
            enunciado = texto_questao
    else:
        enunciado = "(não disponível)"

    return f"""QUESTÃO: {linha['Questao']} ({linha['Ano']}) - {linha['Componente']}
Objetivo de conhecimento atribuído: {linha['Objetivo_de_Conhecimento']}
Presença na ementa UFCG: {linha['Presenca_na_Ementa_UFCG']}
Disciplina(s) correspondente(s): {linha['Disciplina_Correspondente_UFCG']}

Gabarito: {linha['Gabarito']}
Total de alunos: {linha['Total_Alunos']}
Taxa de acerto: {linha['Taxa_Acerto_%']}% (nível: {linha['Nivel_Dificuldade']})

Distribuição das respostas (%): {json.dumps(distribuicao)}
Em branco/rasura: {linha['Pct_Branco_Rasura']}%
Opção mais marcada: {linha['Opcao_Mais_Marcada']} ({linha['Pct_Opcao_Mais_Marcada']}%)
A maioria marcou o gabarito? {linha['A_Maioria_Marcou_Gabarito']}
Principal distrator: {linha['Principal_Distrator']} ({linha['Pct_Principal_Distrator']}%)
Classificação automática (heurística): {linha['Efeito_Distrator']}

ENUNCIADO DA QUESTÃO:
{enunciado}
"""

def analisar_questao_com_llm(linha, texto_questao, tentativas=5):
    prompt = montar_prompt(linha, texto_questao)
    for tentativa in range(tentativas):
        try:
            resp = client.chat.completions.create(
                model=MODELO,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_completion_tokens=3500,
                reasoning_effort="low",
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content)
        except RateLimitError:
            espera = 10 * (tentativa + 1)
            print(f"  limite de requisições atingido, aguardando {espera}s...")
            time.sleep(espera)
        except (json.JSONDecodeError, APIError) as e:
            print(f"  tentativa {tentativa + 1} falhou: {e}")
            time.sleep(2 ** tentativa)
    return None


def analisar_tabela_com_llm(textos, filtro=None, limite=None, pausa=2.0):
    linhas = carregar_tabela_geral()
    if filtro:
        linhas = [r for r in linhas if filtro(r)]

    sem_texto = [f"{r['Ano']} {r['Questao']}" for r in linhas if (r["Ano"], r["Questao"]) not in textos]
    if sem_texto:
        print(f"[AVISO] {len(sem_texto)} questões sem enunciado no CSV de textos: {', '.join(sem_texto[:10])}"
              + (" ..." if len(sem_texto) > 10 else ""))

    cache = carregar_cache()
    processadas = 0

    with open(ARQUIVO_CACHE, "a", encoding="utf-8") as f_cache:
        for linha in linhas:
            chave = (linha["Ano"], linha["Questao"])
            if chave in cache:
                continue
            if limite is not None and processadas >= limite:
                break

            print(f"Analisando {chave[0]} {chave[1]}...")
            resultado = analisar_questao_com_llm(linha, textos.get(chave))
            if resultado is None:
                continue

            registro = {"Ano": chave[0], "Questao": chave[1], **resultado}
            cache[chave] = registro
            f_cache.write(json.dumps(registro, ensure_ascii=False) + "\n")
            f_cache.flush()
            processadas += 1
            time.sleep(pausa)

    saida = []
    for linha in linhas:
        a = cache.get((linha["Ano"], linha["Questao"]))
        if not a:
            continue
        saida.append({
            **linha,
            "Enunciado_Disponivel": "Sim" if (linha["Ano"], linha["Questao"]) in textos else "Não",
            "LLM_Caracteristicas": a.get("caracteristicas_da_questao", ""),
            "LLM_Coerencia_Objetivo": a.get("coerencia_objetivo_texto", ""),
            "LLM_Justificativa_Coerencia": a.get("justificativa_coerencia", ""),
            "LLM_Leitura_Distratores": a.get("leitura_dos_distratores", ""),
            "LLM_Hipotese_Desempenho": a.get("hipotese_de_desempenho", ""),
            "LLM_Qualidade_Item": a.get("qualidade_do_item", ""),
            "LLM_Justificativa_Qualidade": a.get("justificativa_qualidade", ""),
            "LLM_Recomendacao": a.get("recomendacao_pedagogica", ""),
            "LLM_Confianca": a.get("confianca", ""),
        })
    return saida

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

if __name__ == "__main__":
    textos = carregar_textos_questoes()
    print(f"{len(textos)} enunciados carregados.")

    resultado = analisar_tabela_com_llm(
        textos,
        filtro=lambda r: r["Ano"] in ANOS,
        limite=None,
    )
    salvar_csv(resultado, ARQUIVO_ANALISE_LLM)