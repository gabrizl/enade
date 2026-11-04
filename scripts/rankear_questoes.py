import argparse
import csv
import os
import statistics
from collections import defaultdict

PASTA_RELATORIOS = "relatorios_csv"
PASTA_POR_ANO = os.path.join(PASTA_RELATORIOS, "por_ano")

ARQUIVO_ENTRADA = os.path.join(PASTA_RELATORIOS, "tabela_resumo_desempenho_questoes.csv")
ARQUIVO_RANKING = os.path.join(PASTA_RELATORIOS, "ranking_questoes_por_ano.csv")
ARQUIVO_ESTATISTICAS = os.path.join(PASTA_RELATORIOS, "estatisticas_anuais_desempenho.csv")

# Gabaritos Oficiais por Ano
GABARITOS = {
    '2005': {'FG': 'DECAECB', 'CE': 'ZCEBCDEBACDCAABZBBBCABDEDBDC'},
    '2008': {'FG': 'CEDADBDC', 'CE': 'CCAEBBDCA DAEEEBDADDBCCABAC'},
    '2011': {'FG': 'DAEACBBE', 'CE': 'DECBZEDAXBEDACXXEDEBACNNNNNDDXDXNNNNNNNNNN'},
    '2014': {'FG': 'ACEBDCED', 'CE': 'BAXDBBCCAXAEXEDCDCBACAXAXXE'},
    '2017': {'FG': 'CCBBCEAD', 'CE': 'ACECBCDEADEDXCAEXXBDEBEBDAE'},
    '2021': {'FG': 'ECBBAACD', 'CE': 'EBDXXCCBXEDAXACEXADBZEEXZCD'},
}

def carregar_dados():
    caminho = ARQUIVO_ENTRADA
    # Fallback se arquivo ainda estiver no local antigo
    if not os.path.exists(caminho):
        caminho_legado = "graficos_analise/tabela_resumo_desempenho_questoes.csv"
        if os.path.exists(caminho_legado):
            caminho = caminho_legado
        else:
            raise FileNotFoundError(f"Arquivo de dados não encontrado: {ARQUIVO_ENTRADA}")
    with open(caminho, 'r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter=';'))

def processar_ranking(linhas):
    dados_por_ano = defaultdict(list)
    for row in linhas:
        ano = row['Ano']
        q = row['Questao']
        tipo_curto = 'FG' if 'FG' in row['Tipo'] else 'CE'
        idx = int(q.split('_')[1]) - 1
        
        gab_str = GABARITOS.get(ano, {}).get(tipo_curto, '')
        char_gab = gab_str[idx] if idx < len(gab_str) else ''
        
        taxa_str = row.get('Taxa_Acerto_%', '').strip()
        taxa_acerto = float(taxa_str) if taxa_str else None
        
        taxa_erro_str = row.get('Taxa_Erro_%', '').strip()
        taxa_erro = float(taxa_erro_str) if taxa_erro_str else None
        
        total_alunos = int(row['Total_Alunos'])
        acertos = int(row['Acertos'])
        erros = int(row['Erros'])
        em_branco = int(row['Em_Branco'])
        anulados = int(row['Anulados'])
        
        # Identificar status da questão
        if char_gab == 'N':
            status = 'Não aplicável ao curso'
            taxa_acerto = None
            taxa_erro = None
        elif anulados == total_alunos or taxa_acerto is None:
            status = 'Anulada / Desconsiderada'
            taxa_acerto = None
            taxa_erro = None
        else:
            status = 'Válida'
            
        dados_por_ano[ano].append({
            'Ano': int(ano),
            'Questao': q,
            'Tipo_Curto': tipo_curto,
            'Componente': 'Formação Geral' if tipo_curto == 'FG' else 'Componente Específico',
            'Gabarito_Oficial': char_gab,
            'Taxa_Acerto_%': taxa_acerto,
            'Taxa_Erro_%': taxa_erro,
            'Acertos': acertos,
            'Erros': erros,
            'Em_Branco': em_branco,
            'Anulados': anulados,
            'Total_Alunos': total_alunos,
            'Status': status
        })
        
    resultado_final = []
    
    for ano in sorted(dados_por_ano.keys()):
        itens = dados_por_ano[ano]
        
        validas = [it for it in itens if it['Status'] == 'Válida']
        invalidas = [it for it in itens if it['Status'] != 'Válida']
        
        validas.sort(key=lambda x: (-x['Taxa_Acerto_%'], x['Questao']))
        
        # Rank Geral
        for i, it in enumerate(validas):
            if i > 0 and it['Taxa_Acerto_%'] == validas[i - 1]['Taxa_Acerto_%']:
                it['Rank_Geral'] = validas[i - 1]['Rank_Geral']
            else:
                it['Rank_Geral'] = i + 1
                
        for it in invalidas:
            it['Rank_Geral'] = '-'
            
        # Rank Componente
        for comp in ['FG', 'CE']:
            validas_comp = [it for it in validas if it['Tipo_Curto'] == comp]
            validas_comp.sort(key=lambda x: (-x['Taxa_Acerto_%'], x['Questao']))
            for i, it in enumerate(validas_comp):
                if i > 0 and it['Taxa_Acerto_%'] == validas_comp[i - 1]['Taxa_Acerto_%']:
                    it['Rank_Componente'] = validas_comp[i - 1]['Rank_Componente']
                else:
                    it['Rank_Componente'] = i + 1
                    
            for it in invalidas:
                if it['Tipo_Curto'] == comp:
                    it['Rank_Componente'] = '-'
                    
        invalidas.sort(key=lambda x: (x['Status'], x['Questao']))
        ano_completo = validas + invalidas
        resultado_final.extend(ano_completo)
        
    return resultado_final

def gerar_estatisticas_anuais(dados_ranqueados):
    anos = sorted(set(r['Ano'] for r in dados_ranqueados))
    estatisticas = []
    
    for ano in anos:
        itens_ano = [r for r in dados_ranqueados if r['Ano'] == ano]
        total_alunos = itens_ano[0]['Total_Alunos']
        validas = [r for r in itens_ano if r['Status'] == 'Válida']
        anuladas = [r for r in itens_ano if r['Status'] == 'Anulada / Desconsiderada']
        nao_aplicaveis = [r for r in itens_ano if r['Status'] == 'Não aplicável ao curso']
        
        fg_val = [r for r in validas if r['Tipo_Curto'] == 'FG']
        ce_val = [r for r in validas if r['Tipo_Curto'] == 'CE']
        
        taxas_acerto_geral = [r['Taxa_Acerto_%'] for r in validas]
        taxas_erro_geral = [r['Taxa_Erro_%'] for r in validas]
        
        taxas_fg = [r['Taxa_Acerto_%'] for r in fg_val]
        taxas_ce = [r['Taxa_Acerto_%'] for r in ce_val]
        
        media_geral_acerto = statistics.mean(taxas_acerto_geral) if taxas_acerto_geral else 0
        media_geral_erro = statistics.mean(taxas_erro_geral) if taxas_erro_geral else 0
        media_fg_acerto = statistics.mean(taxas_fg) if taxas_fg else 0
        media_ce_acerto = statistics.mean(taxas_ce) if taxas_ce else 0
        
        top_geral = validas[0] if validas else None
        bot_geral = validas[-1] if validas else None
        
        fg_sorted = sorted(fg_val, key=lambda x: x['Taxa_Acerto_%'], reverse=True)
        ce_sorted = sorted(ce_val, key=lambda x: x['Taxa_Acerto_%'], reverse=True)
        
        estatisticas.append({
            'Ano': ano,
            'Total_Alunos': total_alunos,
            'Questoes_Validas': len(validas),
            'Questoes_Anuladas': len(anuladas),
            'Questoes_Nao_Aplicaveis': len(nao_aplicaveis),
            'Media_Geral_Acerto_%': round(media_geral_acerto, 2),
            'Media_Geral_Erro_%': round(media_geral_erro, 2),
            'Media_FG_Acerto_%': round(media_fg_acerto, 2),
            'Media_CE_Acerto_%': round(media_ce_acerto, 2),
            'Mais_Acertada_Geral': f"{top_geral['Questao']} ({top_geral['Taxa_Acerto_%']:.2f}%)" if top_geral else '-',
            'Menos_Acertada_Geral': f"{bot_geral['Questao']} ({bot_geral['Taxa_Acerto_%']:.2f}%)" if bot_geral else '-',
            'Mais_Acertada_FG': f"{fg_sorted[0]['Questao']} ({fg_sorted[0]['Taxa_Acerto_%']:.2f}%)" if fg_sorted else '-',
            'Menos_Acertada_FG': f"{fg_sorted[-1]['Questao']} ({fg_sorted[-1]['Taxa_Acerto_%']:.2f}%)" if fg_sorted else '-',
            'Mais_Acertada_CE': f"{ce_sorted[0]['Questao']} ({ce_sorted[0]['Taxa_Acerto_%']:.2f}%)" if ce_sorted else '-',
            'Menos_Acertada_CE': f"{ce_sorted[-1]['Questao']} ({ce_sorted[-1]['Taxa_Acerto_%']:.2f}%)" if ce_sorted else '-'
        })
        
    return estatisticas

def salvar_csv_ranking(dados, caminho_saida=ARQUIVO_RANKING):
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    colunas = [
        'Ano',
        'Rank_Geral',
        'Rank_Componente',
        'Questao',
        'Componente',
        'Gabarito_Oficial',
        'Taxa_Acerto_%',
        'Taxa_Erro_%',
        'Acertos',
        'Erros',
        'Em_Branco',
        'Anulados',
        'Total_Alunos',
        'Status'
    ]
    with open(caminho_saida, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=colunas, delimiter=';')
        writer.writeheader()
        for r in dados:
            linha = {
                'Ano': r['Ano'],
                'Rank_Geral': r['Rank_Geral'],
                'Rank_Componente': r['Rank_Componente'],
                'Questao': r['Questao'],
                'Componente': r['Componente'],
                'Gabarito_Oficial': r['Gabarito_Oficial'],
                'Taxa_Acerto_%': f"{r['Taxa_Acerto_%']:.2f}" if r['Taxa_Acerto_%'] is not None else '',
                'Taxa_Erro_%': f"{r['Taxa_Erro_%']:.2f}" if r['Taxa_Erro_%'] is not None else '',
                'Acertos': r['Acertos'],
                'Erros': r['Erros'],
                'Em_Branco': r['Em_Branco'],
                'Anulados': r['Anulados'],
                'Total_Alunos': r['Total_Alunos'],
                'Status': r['Status']
            }
            writer.writerow(linha)
    print(f"[OK] Arquivo consolidado de Ranking salvo em: {caminho_saida}")

def salvar_rankings_por_ano(dados, pasta_saida=PASTA_POR_ANO):
    os.makedirs(pasta_saida, exist_ok=True)
    anos = sorted(set(r['Ano'] for r in dados))
    for ano in anos:
        itens_ano = [r for r in dados if r['Ano'] == ano]
        caminho_ano = os.path.join(pasta_saida, f"ranking_questoes_{ano}.csv")
        salvar_csv_ranking(itens_ano, caminho_ano)

def salvar_csv_estatisticas(estatisticas, caminho_saida=ARQUIVO_ESTATISTICAS):
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    colunas = list(estatisticas[0].keys())
    with open(caminho_saida, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=colunas, delimiter=';')
        writer.writeheader()
        writer.writerows(estatisticas)
    print(f"[OK] Arquivo de Estatísticas Anuais salvo em: {caminho_saida}")

def exibir_tabela(dados, ano_filtro=None, comp_filtro=None, apenas_validas=False):
    anos = sorted(set(r['Ano'] for r in dados))
    if ano_filtro:
        anos = [a for a in anos if a == ano_filtro]
        
    for ano in anos:
        itens_ano = [r for r in dados if r['Ano'] == ano]
        if comp_filtro:
            itens_ano = [r for r in itens_ano if r['Tipo_Curto'] == comp_filtro.upper()]
        if apenas_validas:
            itens_ano = [r for r in itens_ano if r['Status'] == 'Válida']
            
        print(f"\n{'='*82}")
        print(f" RANKING DE QUESTÕES - ENADE {ano} (UFCG - Ciência da Computação)")
        print(f"{'='*82}")
        print(f"{'Rank G.':<8}{'Rank C.':<8}{'Questão':<10}{'Comp.':<6}{'Acerto (%)':<14}{'Acertos/Total':<16}{'Gab.':<6}{'Status':<14}")
        print(f"{'-'*82}")
        for r in itens_ano:
            rg = f"{r['Rank_Geral']}º" if r['Rank_Geral'] != '-' else '-'
            rc = f"{r['Rank_Componente']}º" if r['Rank_Componente'] != '-' else '-'
            taxa = f"{r['Taxa_Acerto_%']:6.2f}%" if r['Taxa_Acerto_%'] is not None else '  -   '
            fracao = f"{r['Acertos']}/{r['Total_Alunos']}"
            print(f"{rg:<8}{rc:<8}{r['Questao']:<10}{r['Tipo_Curto']:<6}{taxa:<14}{fracao:<16}{r['Gabarito_Oficial']:<6}{r['Status']:<14}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Rankear questões do Enade por taxa de acerto e gerar estatísticas.")
    parser.add_argument("--ano", type=int, help="Filtrar por ano específico (ex: 2005, 2008, 2011, 2014, 2017, 2021)")
    parser.add_argument("--tipo", type=str, choices=['FG', 'CE'], help="Filtrar por tipo: FG (Formação Geral) ou CE (Componente Específico)")
    parser.add_argument("--apenas-validas", action="store_true", help="Exibir apenas questões válidas")
    parser.add_argument("--tabela", action="store_true", help="Exibir a tabela completa no terminal")
    args = parser.parse_args()

    linhas = carregar_dados()
    dados_ranqueados = processar_ranking(linhas)
    estatisticas_anuais = gerar_estatisticas_anuais(dados_ranqueados)
    
    salvar_csv_ranking(dados_ranqueados)
    salvar_rankings_por_ano(dados_ranqueados)
    salvar_csv_estatisticas(estatisticas_anuais)

    if args.tabela or args.ano or args.tipo:
        exibir_tabela(dados_ranqueados, ano_filtro=args.ano, comp_filtro=args.tipo, apenas_validas=args.apenas_validas)
