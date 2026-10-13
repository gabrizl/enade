import csv
import glob
import os
import re

# Dicionários de Tradução para Códigos do Enade
MAPA_PRESENCA = {
    '555': 'Presente com resultado válido',
    '556': 'Presente com resultado desconsiderado',
    '222': 'Ausente',
    '333': 'Ausente / Eliminado',
    '444': 'Ausente no local de aplicação',
    '888': 'Presente sem resposta válida'
}

MAPA_ACERTO = {
    '1': 'Acertou',
    '0': 'Errou',
    '8': 'Item desconsiderado',
    '9': 'Item anulado',
    'X': 'Item anulado',
    '.': 'Em branco',
    '*': 'Rasura / Dupla marcação',
    'Z': 'Não aplicável'
}

MAPA_RESPOSTA = {
    '*': 'Rasura / Dupla marcação',
    '.': 'Em branco'
}

def traduzir_presenca(cod):
    if not cod:
        return ''
    cod_str = str(cod).strip()
    return MAPA_PRESENCA.get(cod_str, cod_str)

def traduzir_acerto(cod):
    if not cod:
        return ''
    cod_str = str(cod).strip()
    return MAPA_ACERTO.get(cod_str, cod_str)

def traduzir_resposta(char):
    if not char:
        return ''
    return MAPA_RESPOSTA.get(char, char)


def extrair_respostas_ano(caminho_arquivo, co_curso="13446"):
    """
    Extrai os dados de um arquivo de microdados para o curso especificado,
    tratando adequadamente as peculiaridades de cada ano do Enade (2005 a 2021).
    """
    if not os.path.exists(caminho_arquivo):
        print(f"[AVISO] Arquivo não encontrado: {caminho_arquivo}")
        return []

    # Identificar o ano pelo nome do arquivo
    match_ano = re.search(r'(\d{4})', os.path.basename(caminho_arquivo))
    ano_arquivo = match_ano.group(1) if match_ano else "desconhecido"

    # Detectar delimitador
    with open(caminho_arquivo, 'r', encoding='latin1') as f:
        first_line = f.readline()
        delimiter = ';' if ';' in first_line else ','

    rows_out = []
    with open(caminho_arquivo, 'r', encoding='latin1') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            if str(row.get('CO_CURSO', '')).strip() != str(co_curso).strip():
                continue

            ano = row.get('NU_ANO', ano_arquivo)
            
            # Vetores de respostas, gabarito e acerto
            esc_fg = row.get('DS_VT_ESC_OFG', '').strip('"')
            ace_fg = row.get('DS_VT_ACE_OFG', '').strip('"')
            gab_fg = row.get('DS_VT_GAB_OFG_FIN', '').strip('"')

            esc_ce = row.get('DS_VT_ESC_OCE', '').strip('"')
            ace_ce = row.get('DS_VT_ACE_OCE', '').strip('"')
            gab_ce = row.get('DS_VT_GAB_OCE_FIN', '').strip('"')

            # Tratamento de Formação Geral (FG): 7 questões em 2005, 8 nos demais anos
            total_fg = max(len(esc_fg), len(ace_fg), len(gab_fg), 7 if str(ano) == '2005' else 8)

            # Tratamento do Componente Específico (CE)
            # Em 2005, a prova de Ciência da Computação era as questões 29 a 56 do caderno geral de 70 itens
            if str(ano) == '2005' and len(esc_ce) >= 56:
                # Índices 28 a 55 (questões 29 a 56)
                idx_inicio, idx_fim = 28, 56
                esc_ce_aluno = esc_ce[idx_inicio:idx_fim]
                ace_ce_aluno = ace_ce[idx_inicio:idx_fim]
                gab_ce_aluno = gab_ce[idx_inicio:idx_fim] if len(gab_ce) >= idx_fim else gab_ce
            elif str(ano) == '2011':
                # Em 2011 há 42 itens com faixas específicas
                esc_ce_aluno = esc_ce
                ace_ce_aluno = ace_ce
                gab_ce_aluno = gab_ce
            else:
                # 2008, 2014, 2017, 2021: tipicamente 27 itens
                esc_ce_aluno = esc_ce[:27] if len(esc_ce) >= 27 else esc_ce
                ace_ce_aluno = ace_ce[:27] if len(ace_ce) >= 27 else ace_ce
                gab_ce_aluno = gab_ce[:27] if len(gab_ce) >= 27 else gab_ce

            rec = {
                'Ano': ano,
                'Codigo_Curso': row.get('CO_CURSO', co_curso),
                'Curso': 'Ciência da Computação (Bacharelado)',
                'Instituicao': 'UFCG',
                'Presenca': traduzir_presenca(row.get('TP_PRES')),

                # Notas Consolidadas
                'Nota_Geral': row.get('NT_GER', ''),
                'Nota_Formacao_Geral': row.get('NT_FG', ''),
                'Nota_Especifica_Computacao': row.get('NT_CE', ''),

                # Divisão Objetiva / Discursiva
                'Nota_Objetiva_FG': row.get('NT_OBJ_FG', ''),
                'Nota_Discursiva_FG': row.get('NT_DIS_FG', ''),
                'Nota_Objetiva_CE': row.get('NT_OBJ_CE', ''),
                'Nota_Discursiva_CE': row.get('NT_DIS_CE', ''),

                # Questões Discursivas Isoladas
                'Nota_FG_Discursiva_1': row.get('NT_FG_D1', ''),
                'Nota_FG_Discursiva_2': row.get('NT_FG_D2', ''),
                'Nota_CE_Discursiva_1': row.get('NT_CE_D1', ''),
                'Nota_CE_Discursiva_2': row.get('NT_CE_D2', ''),
                'Nota_CE_Discursiva_3': row.get('NT_CE_D3', ''),

                # Gabaritos Oficiais
                'Gabarito_Formacao_Geral': gab_fg,
                'Gabarito_Especifico_Computacao': gab_ce_aluno,
            }

            # 1. Respostas e Acertos de Formação Geral (FG)
            for i in range(total_fg):
                char_resp = esc_fg[i] if i < len(esc_fg) else ''
                char_acerto = ace_fg[i] if i < len(ace_fg) else ''
                rec[f'Resposta_FG_{i+1:02d}'] = traduzir_resposta(char_resp)
                rec[f'Acerto_FG_{i+1:02d}'] = traduzir_acerto(char_acerto)

            # 2. Respostas e Acertos do Componente Específico (CE)
            total_ce = len(esc_ce_aluno)
            for i in range(total_ce):
                char_resp = esc_ce_aluno[i] if i < len(esc_ce_aluno) else ''
                char_acerto = ace_ce_aluno[i] if i < len(ace_ce_aluno) else ''
                rec[f'Resposta_CE_{i+1:02d}'] = traduzir_resposta(char_resp)
                rec[f'Acerto_CE_{i+1:02d}'] = traduzir_acerto(char_acerto)

            # 3. Questionário de Percepção da Prova (itens 1 a 9)
            for i in range(1, 10):
                rec[f'Percepcao_Prova_Q{i}'] = row.get(f'CO_RS_I{i}', '')

            rows_out.append(rec)

    return rows_out


def processar_todos_os_anos(
    pasta_microdados="microdados",
    pasta_saida="microdados_tratados",
    co_curso="13446"
):
    os.makedirs(pasta_saida, exist_ok=True)
    arquivos = sorted(glob.glob(os.path.join(pasta_microdados, "microdados*.txt")))

    if not arquivos:
        print(f"Nenhum arquivo encontrado em: {pasta_microdados}")
        return

    print(f"=== Iniciando extração Enade (UFCG - Curso {co_curso}) ===")
    print(f"Arquivos encontrados: {len(arquivos)}\n")

    todos_registros = []

    for arq in arquivos:
        match_ano = re.search(r'(\d{4})', os.path.basename(arq))
        ano = match_ano.group(1) if match_ano else "desconhecido"
        
        print(f"-> Processando Enade {ano} ({os.path.basename(arq)})...")
        registros_ano = extrair_respostas_ano(arq, co_curso=co_curso)

        if not registros_ano:
            print(f"   [INFO] Nenhum registro de Ciência da Computação (curso {co_curso}) no ano {ano} (ano não avaliado ou ausente).")
            continue

        print(f"   [OK] {len(registros_ano)} alunos encontrados para {ano}.")
        todos_registros.extend(registros_ano)

        # Salvar arquivo individual do ano
        saida_ano = os.path.join(pasta_saida, f"ufcg_cc_respostas_questoes_{ano}.csv")
        with open(saida_ano, 'w', newline='', encoding='utf-8-sig') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=list(registros_ano[0].keys()), delimiter=';')
            writer.writeheader()
            writer.writerows(registros_ano)
        print(f"   Arquivo individual salvo: {saida_ano}")

    # Salvar arquivo consolidado de todos os anos
    if todos_registros:
        # Obter a união de todas as colunas mantendo ordem consistente
        todas_colunas = []
        for reg in todos_registros:
            for k in reg.keys():
                if k not in todas_colunas:
                    todas_colunas.append(k)

        saida_consolidada = os.path.join(pasta_saida, "ufcg_cc_respostas_questoes_todos_anos.csv")
        with open(saida_consolidada, 'w', newline='', encoding='utf-8-sig') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=todas_colunas, delimiter=';')
            writer.writeheader()
            writer.writerows(todos_registros)
        print(f"\n[SUCESSO] Arquivo consolidado com {len(todos_registros)} alunos salvo em:\n  -> {saida_consolidada}")


if __name__ == "__main__":
    processar_todos_os_anos()
