import csv
import os
import statistics
from collections import Counter, defaultdict

PASTA_RELATORIOS = "relatorios_csv"
PASTA_MICRODADOS = "microdados_tratados"

ARQUIVO_RANKING = os.path.join(PASTA_RELATORIOS, "ranking_questoes_por_ano.csv")
ARQUIVO_OBJETIVOS = os.path.join(PASTA_RELATORIOS, "Enade_Objetivo_Conhecimento - Enade_Objetivo_Conhecimento.csv")
if not os.path.exists(ARQUIVO_OBJETIVOS):
    ARQUIVO_OBJETIVOS = "Enade_Objetivo_Conhecimento - Enade_Objetivo_Conhecimento.csv"

# Saídas
ARQUIVO_OPCOES = os.path.join(PASTA_RELATORIOS, "estatistica_distribuicao_opcoes.csv")
ARQUIVO_MAIS_ERRADAS = os.path.join(PASTA_RELATORIOS, "analise_questoes_mais_erradas.csv")
ARQUIVO_ANULADAS = os.path.join(PASTA_RELATORIOS, "analise_questoes_anuladas.csv")
ARQUIVO_COMPARATIVO_ASSUNTOS = os.path.join(PASTA_RELATORIOS, "comparativo_assuntos_longitudinal.csv")
ARQUIVO_ANALISE_GERAL = os.path.join(PASTA_RELATORIOS, "analise_geral_questoes.csv")

# Mapeamento Curricular UFCG (Ciência da Computação)
MAPEAMENTO_CURRICULO_UFCG = {
     # --- COMPONENTE ESPECÍFICO ---
    'Algoritmos e Estruturas de Dados': {
        'status': 'Obrigatória',
        'disciplina': 'Estruturas de Dados e Algoritmos (EDA) / Lab. EDA (LEDA) / Análise e Técnicas de Algoritmos (ATAL)'
    },
    'Banco de Dados': {
        'status': 'Obrigatória',
        'disciplina': 'Bancos de Dados I (BD1)'
    },
    'Engenharia de Software': {
        'status': 'Obrigatória',
        'disciplina': 'Engenharia de Software (ES) / Análise de Sistemas (AS) / Projeto de Software I/II (P1/P2)'
    },
    'Engenharia de Software e Interação Homem-Computador': {
        'status': 'Obrigatória / Optativa',
        'disciplina': 'Engenharia de Software (ES) / Interface Humano-Computador (IHC - optativa)'
    },
    'Fundamentos e Técnicas de Programação': {
        'status': 'Obrigatória',
        'disciplina': 'Programação I (P1) / Lab. P1 (LP1) / Programação II (P2) / Lab. P2 (LP2)'
    },
    'Interação Homem-Computador (IHC)': {
        'status': 'Obrigatória / Optativa',
        'disciplina': 'Análise de Sistemas (AS) / Interface Humano-Computador (IHC - optativa)'
    },
    'Lógica e Matemática Discreta': {
        'status': 'Obrigatória',
        'disciplina': 'Fundamentos de Matemática para Ciência da Computação I e II / Lógica para Computação'
    },
    'Organização e Arquitetura de Computadores': {
        'status': 'Obrigatória',
        'disciplina': 'Organização e Arquitetura de Computadores (OAC) / Introdução à Computação (IC)'
    },
    'Sistemas Operacionais': {
        'status': 'Obrigatória',
        'disciplina': 'Sistemas Operacionais (SO) / Programação Concorrente (PC)'
    },
    'Redes de Computadores': {
        'status': 'Obrigatória',
        'disciplina': 'Redes de Computadores (RC)'
    },
    'Redes de Computadores e Sistemas Distribuídos': {
        'status': 'Obrigatória / Optativa',
        'disciplina': 'Redes de Computadores (RC) / Sistemas Distribuídos (SD)'
    },
    'Paradigmas de Linguagens de Programação': {
        'status': 'Obrigatória',
        'disciplina': 'Paradigmas de Linguagens de Programação (PLP)'
    },
    'Teoria da Computação': {
        'status': 'Obrigatória',
        'disciplina': 'Teoria da Computação (TC)'
    },
    'Teoria dos Grafos': {
        'status': 'Obrigatória',
        'disciplina': 'Teoria dos Grafos (TG)'
    },
    'Sistemas Distribuídos': {
        'status': 'Obrigatória / Optativa',
        'disciplina': 'Programação Concorrente (PC) / Sistemas Distribuídos (SD)'
    },
    'Inteligência Artificial': {
        'status': 'Obrigatória',
        'disciplina': 'Inteligência Artificial (IA)'
    },
    'Sistemas Digitais': {
        'status': 'Obrigatória / Optativa',
        'disciplina': 'Introdução a computação / Projeto de Sistemas Digitais (Optativa)'
    },
    'Probabilidade e Estatística': {
        'status': 'Obrigatória',
        'disciplina': 'Introdução à Probabilidade (IP) / Estatística Aplicada (EA)'
    },
    'Compiladores': {
        'status': 'Obrigatória',
        'disciplina': 'Compiladores (COMP)'
    },
    'Linguagens Formais, Autômatos e Compiladores': { #Antes de 2014
        'status': 'Obrigatória',
        'disciplina': 'Teoria da Computação / Compiladores'
    },
    'Sistemas Operacionais e Arquitetura de Computadores': { #Antes de 2014
        'status': 'Obrigatória',
        'disciplina': 'Sistemas Operacionais (SO) / Organização e Arquitetura de Computadores (OAC)'
    },
    'Teoria da Computabilidade e Complexidade': { #Antes de 2014
        'status': 'Obrigatória (Tópico Avançado)',
        'disciplina': 'Teoria da Computação / Análise e Técnicas de Algoritmos (ATAL)'
    },
    'Inteligência Artificial e Computacional': { #Antes de 2014
        'status': 'Optativa / Eletiva',
        'disciplina': 'Inteligência Artificial (IA)'
    },
    'Computação Gráfica e Processamento de Imagem': {
        'status': 'Ausente',
        'disciplina': 'Atualmente não há disciplina no currículo da UFCG.'
    },
    # --- FORMAÇÃO GERAL ---
    'Ética, Computador e Sociedade': {
        'status': 'Obrigatória',
        'disciplina': 'Direito e Cidadania / Informática e Sociedade'
    },
    'Ética, Computador e Sociedade / Segurança': {
            'status': 'Obrigatória / Optativa',
            'disciplina': 'Direito e Cidadania / Segurança de Sistemas / Informática e Sociedade'
    },

    'Ciência, tecnologia e inovação / Inovação tecnológica': {
        'status': 'Obrigatória / Optativa',
        'disciplina': 'Direito e Cidadania / Economia / Empreendedorismo e Inovação'
    },
    'Estado, sociedade e trabalho / Relações de trabalho / Gig Economy': {
        'status': 'Obrigatória / Optativa',
        'disciplina': 'Direito e Cidadania / Economia / Informática e Sociedade'
    },
    'Ética, democracia e cidadania / Políticas públicas': {
        'status': 'Obrigatória / Optativa',
        'disciplina': 'Direito e Cidadania / Língua Portuguesa / Informática e Sociedade'
    },
    'Cidades, habitação e qualidade de vida / Mobilidade urbana': {
        'status': 'Obrigatória / Optativa',
        'disciplina': 'Economia / Sistemas de Informações Geográficas / Informática e Sociedade'
    },
    'Meio ambiente, biodiversidade e sustentabilidade / Ecologia': {
        'status': 'Transversal / Optativa',
        'disciplina': 'Informática e Sociedade'
    },
    'Globalização, processos migratórios e política internacional': {
        'status': 'Obrigatória / Optativa',
        'disciplina': 'Economia / Informática e Sociedade / Transformação Digital'
    },
    'Sociodiversidade, multiculturalismo, acessibilidade e inclusão': {
        'status': 'Obrigatória / Optativa',
        'disciplina': 'Direito e Cidadania / Libras - Língua Brasileira de Sinais / Interface Humano-Computador'
    },
        'Promoção da saúde, prevenção de doenças e segurança alimentar': {
        'status': 'Ausente',
        'disciplina': 'Atualmente não há disciplina no currículo da UFCG.'
    }
}

# Diagnóstico específico dos motivos de anulação pelo INEP
DIAGNOSTICO_ANULACOES = {
    ('2021', 'CE_04'): {
        'motivo': 'Ambiguidade Jurídico-Conceitual / Duplicidade de Interpretação',
        'explicacao': 'Questão sobre a LGPD. Divergência na doutrina sobre consentimento em dados sensíveis gerou interpretações concorrentes para a validade dos itens II e III.'
    },
    ('2021', 'CE_05'): {
        'motivo': 'Divergência Terminológica / Ausência de Resposta Unívoca',
        'explicacao': 'Questão sobre desenvolvimento iterativo e evolutivo. Conflito entre terminologia do modelo formal de ciclo de vida e práticas ágeis/Scrum.'
    },
    ('2021', 'CE_09'): {
        'motivo': 'Inconsistência entre Enunciado e Figura Técnica',
        'explicacao': 'Questão sobre regiões críticas e exclusão mútua em SO. A representação gráfica continha marcação ambígua das seções de entrada e saída, invalidando a relação asserção-razão.'
    },
    ('2021', 'CE_13'): {
        'motivo': 'Erro Conceitual na Associação de Dispositivos por Camada',
        'explicacao': 'Questão de redes sobre o modelo OSI/TCP-IP. Associação de Switch L2/L3 e roteamento com encapsulamento de quadros permitiu mais de uma combinação de respostas corretas.'
    },
    ('2021', 'CE_17'): {
        'motivo': 'Ambiguidade na Definição de Modelos de Serviço em Nuvem',
        'explicacao': 'Questão sobre Cloud Computing (IaaS/PaaS/SaaS). Falha de redação nos itens romanos permitiu interpretação de que o item IV também era tecnicamente verdadeiro.'
    },
    ('2021', 'CE_21'): {
        'motivo': 'Problema de Impressão e Legibilidade de Figura (Item Z)',
        'explicacao': 'Questão sobre morfologia matemática em PDI (dilatação/erosão). A perda de contraste visual nas imagens impressas nos cadernos levou o INEP a desconsiderar o item (Z).'
    },
    ('2021', 'CE_24'): {
        'motivo': 'Erro na Formulação das Propriedades de Algoritmos de Ordenação',
        'explicacao': 'Questão sobre complexidade e estabilidade (Quicksort/Mergesort). A asserção sobre a estabilidade in-place continha premissa tecnicamente equivocada no gabarito preliminar.'
    },
    ('2021', 'CE_25'): {
        'motivo': 'Falha na Semântica Lógica de Predicado em Prolog (Item Z)',
        'explicacao': 'Implementação do predicado saoirmas(X,Y) em Prolog. A regra falhava ao distinguir meio-irmãos e relação bilateral (pai E mãe compartilhados), tornando a resposta formalmente incompleta.'
    },
    ('2017', 'CE_13'): {
        'motivo': 'Duplicidade de Equivalência Lógica por De Morgan',
        'explicacao': 'Formalização de sentença condicional em lógica proposicional. Por equivalência lógica direta e aplicação das Leis de De Morgan, duas alternativas resultavam na mesma tabela-verdade.'
    },
    ('2017', 'CE_17'): {
        'motivo': 'Inconsistência na Equação de Recorrência / Teorema Mestre',
        'explicacao': 'Equação de recorrência T(n) = 2T(n/2) + O(n). Houve divergência entre os termos da recorrência informada e as alternativas expressas em complexidade assintótica.'
    },
    ('2017', 'CE_18'): {
        'motivo': 'Imprecisão na Caracterização do Filtro para Ruído Impulsivo',
        'explicacao': 'Questão sobre Processamento de Imagens Médicas com ruído Sal e Pimenta. Ambiguidade na definição de filtro não-linear vs filtro espacial causou anulação após recursos.'
    },
    ('2014', 'CE_03'): {
        'motivo': 'Falha na Quantificação de Complexidade e Memória Auxiliar',
        'explicacao': 'Avaliação de polinômios pelo método de Horner vs ingênuo. A contagem de espaço de memória auxiliar apresentava falha de formulação nas alternativas.'
    },
    ('2014', 'CE_10'): {
        'motivo': 'Erro de Sintaxe / Comportamento Indefinido em Código C',
        'explicacao': 'Função recursiva com ponteiros em C. A manipulação de ponteiros apresentava comportamento indefinido pelo padrão ANSI C, inviabilizando a execução única esperada.'
    },
    ('2014', 'CE_13'): {
        'motivo': 'Ambiguidade de Escopo de Conectivos em Lógica de Primeira Ordem',
        'explicacao': 'Inferência dedutiva em lógica. Ambiguidade no escopo dos quantificadores universais gerou duas formalizações semanticamente válidas.'
    },
    ('2014', 'CE_23'): {
        'motivo': 'Falha na Premissa da Heurística do Algoritmo de Busca A*',
        'explicacao': 'Questão de IA sobre algoritmo A*. A premissa sobre o comportamento da busca informada com heurística nula continha contradição com o enunciado da alternativa considerada correta.'
    },
    ('2014', 'CE_25'): {
        'motivo': 'Sobreposição Conceitual em Padrões de Projeto (GoF)',
        'explicacao': 'Classificação de padrões GoF (Strategy vs State). As alternativas apresentavam sobreposição funcional que impedia a seleção de uma resposta mutuamente exclusiva.'
    },
    ('2014', 'CE_26'): {
        'motivo': 'Erro na Implementação de Concorrência com Semáforos',
        'explicacao': 'Problema de produtores e consumidores em Java. O código concorrente continha deadlock não intencional na inicialização dos semáforos, invalidando as alternativas de saída.'
    }
}

def carregar_respostas_alunos():
    """
    Carrega as respostas de alunos válidos por ano para cálculo de estatísticas de distratores.
    """
    respostas_por_ano = {}
    anos = ['2005', '2008', '2011', '2014', '2017', '2021']
    for ano in anos:
        caminho = os.path.join(PASTA_MICRODADOS, f"ufcg_cc_respostas_questoes_{ano}.csv")
        if not os.path.exists(caminho):
            continue
        with open(caminho, 'r', encoding='utf-8-sig') as f:
            validos = [r for r in csv.DictReader(f, delimiter=';') if 'Presente com resultado válido' in r.get('Presenca', '')]
            respostas_por_ano[ano] = validos
    return respostas_por_ano

def carregar_dados_ranking():
    with open(ARQUIVO_RANKING, 'r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter=';'))

def carregar_textos_questoes():
    textos = {}
    if os.path.exists(ARQUIVO_OBJETIVOS):
        with open(ARQUIVO_OBJETIVOS, 'r', encoding='utf-8') as f:
            r = csv.reader(f)
            next(r)
            for row in r:
                if row and len(row) >= 4:
                    ano = row[0].strip()
                    q = row[2].strip()
                    txt = row[3].strip()
                    textos[(ano, q)] = txt
    return textos

def gerar_tabela_opcoes(ranking_dados, respostas_alunos):
    """
    Gera a tabela completa de distribuição de opções escolhidas (distratores),
    validando o gabarito efetivo diretamente contra as respostas corrigidas pelo INEP.
    """
    dados_opcoes = []
    
    for r in ranking_dados:
        ano = r['Ano']
        q = r['Questao']
        comp = r['Componente']
        obj = r.get('Objetivo_de_Conhecimento', 'Não informado')
        gab_declarado = r['Gabarito_Oficial']
        status = r['Status']
        
        alunos_ano = respostas_alunos.get(ano, [])
        total_alunos = len(alunos_ano)
        if total_alunos == 0:
            continue
            
        col_resp = f"Resposta_{q}"
        col_ace = f"Acerto_{q}"
        respostas = [aluno.get(col_resp, '') for aluno in alunos_ano]
        contagem = Counter(respostas)
        
        # Obter gabarito efetivo (confirmado pelas respostas dos alunos que pontuaram 'Acertou')
        respostas_corretas = set(aluno.get(col_resp) for aluno in alunos_ano if aluno.get(col_ace) == 'Acertou')
        if status == 'Válida' and respostas_corretas:
            gab = list(respostas_corretas)[0]
        else:
            gab = gab_declarado
        
        # Contagem por alternativa
        cA = contagem.get('A', 0)
        cB = contagem.get('B', 0)
        cC = contagem.get('C', 0)
        cD = contagem.get('D', 0)
        cE = contagem.get('E', 0)
        cBranco = contagem.get('Em branco', 0) + contagem.get('Rasura / Dupla marcação', 0) + contagem.get('', 0)
        
        pA = round((cA / total_alunos) * 100, 2)
        pB = round((cB / total_alunos) * 100, 2)
        pC = round((cC / total_alunos) * 100, 2)
        pD = round((cD / total_alunos) * 100, 2)
        pE = round((cE / total_alunos) * 100, 2)
        pBranco = round((cBranco / total_alunos) * 100, 2)
        
        mapa_pct = {'A': pA, 'B': pB, 'C': pC, 'D': pD, 'E': pE}
        
        # Opção mais marcada de todas
        opcao_mais_marcada = max(mapa_pct.keys(), key=lambda k: mapa_pct[k])
        pct_mais_marcada = mapa_pct[opcao_mais_marcada]
        
        # A maioria acertou?
        maioria_acertou = 'Sim' if (status == 'Válida' and gab in mapa_pct and opcao_mais_marcada == gab and pct_mais_marcada > 0) else 'Não'
        
        # Principal distrator (opção errada mais marcada)
        distratores = {k: v for k, v in mapa_pct.items() if k != gab}
        if distratores:
            principal_distrator = max(distratores.keys(), key=lambda k: distratores[k])
            pct_principal_distrator = distratores[principal_distrator]
        else:
            principal_distrator = '-'
            pct_principal_distrator = 0.0
            
        # Classificação do efeito do distrator
        if status != 'Válida':
            efeito = f'Questão Anulada / Desconsiderada ({status})'
        elif pct_principal_distrator > mapa_pct.get(gab, 0):
            efeito = f'Pegadinha Crítica (Distrator {principal_distrator} [{pct_principal_distrator}%] superou Gabarito {gab} [{mapa_pct.get(gab,0)}%])'
        elif pct_principal_distrator >= 25.0:
            efeito = f'Distrator Forte ({principal_distrator} atraiu {pct_principal_distrator:.1f}%)'
        elif mapa_pct.get(gab, 0) >= 65.0:
            efeito = 'Domínio Consolidado (Baixa atração de distratores)'
        else:
            efeito = 'Dispersão de Respostas (Chute generalizado)'
            
        dados_opcoes.append({
            'Ano': ano,
            'Questao': q,
            'Componente': comp,
            'Objetivo_de_Conhecimento': obj,
            'Gabarito_Oficial': gab,
            'Status': status,
            'Total_Alunos': total_alunos,
            'Pct_A': pA,
            'Pct_B': pB,
            'Pct_C': pC,
            'Pct_D': pD,
            'Pct_E': pE,
            'Pct_Branco_Rasura': pBranco,
            'Opcao_Mais_Marcada': opcao_mais_marcada,
            'Pct_Opcao_Mais_Marcada': pct_mais_marcada,
            'A_Maioria_Marcou_Gabarito': maioria_acertou,
            'Principal_Distrator': principal_distrator,
            'Pct_Principal_Distrator': pct_principal_distrator,
            'Efeito_Distrator': efeito
        })
        
    return dados_opcoes

def gerar_tabela_mais_erradas(ranking_dados, dados_opcoes):
    """
    Gera o diagnóstico aprofundado das questões mais erradas (acerto < 40%).
    """
    opcoes_map = {(r['Ano'], r['Questao']): r for r in dados_opcoes}
    mais_erradas = []
    
    # Filtrar questões válidas com menor acerto (< 40%)
    validas = [r for r in ranking_dados if r['Status'] == 'Válida' and r['Taxa_Acerto_%'] != '']
    validas_ordenadas = sorted(validas, key=lambda x: float(x['Taxa_Acerto_%']))
    
    for r in validas_ordenadas:
        taxa_acerto = float(r['Taxa_Acerto_%'])
        if taxa_acerto >= 40.0:
            continue
            
        ano = r['Ano']
        q = r['Questao']
        obj = r.get('Objetivo_de_Conhecimento', 'Não informado')
        gab = r['Gabarito_Oficial']
        
        info_opt = opcoes_map.get((ano, q), {})
        dist_str = f"A:{info_opt.get('Pct_A',0)}% | B:{info_opt.get('Pct_B',0)}% | C:{info_opt.get('Pct_C',0)}% | D:{info_opt.get('Pct_D',0)}% | E:{info_opt.get('Pct_E',0)}%"
        
        # Mapeamento com ementa da UFCG
        info_curr = MAPEAMENTO_CURRICULO_UFCG.get(obj, {
            'status': 'Formação Geral / Transversal' if 'Geral' in r['Componente'] else 'Não mapeado',
            'disciplina': 'Tema de Formação Geral (MEC/INEP)' if 'Geral' in r['Componente'] else 'Eletiva'
        })
        
        p_dist = info_opt.get('Principal_Distrator', '-')
        p_dist_pct = info_opt.get('Pct_Principal_Distrator', 0)
        
        # Diagnóstico da Causa Raiz
        if 'Optativa' in info_curr['status']:
            fator_principal = 'Conteúdo em Disciplina Optativa (Não Cursada pela Maioria)'
            analise = f"O assunto '{obj}' é matéria optativa no curso da UFCG ({info_curr['disciplina']}). Como a maioria dos alunos não cursou, as respostas foram concentradas no distrator {p_dist} ({p_dist_pct}%) ou dispersas por chute."
        elif p_dist_pct > taxa_acerto:
            fator_principal = f"Distrator com Forte Pegadinha (Opção {p_dist} superou Gabarito {gab})"
            analise = f"Mais alunos marcaram o distrator {p_dist} ({p_dist_pct}%) do que o gabarito correto {gab} ({taxa_acerto}%). Indica armadilha clássica no enunciado ou erro de raciocínio típico da matéria."
        elif taxa_acerto < 25.0:
            fator_principal = 'Alta Complexidade Teórica / Enunciado Extenso'
            analise = f"Apenas {taxa_acerto}% acertaram. O conteúdo de '{obj}' exigiu raciocínio formal avançado e análise de múltiplos itens, gerando dispersão generalizada entre as opções."
        else:
            fator_principal = 'Dificuldade Conceitual / Interpretação'
            analise = f"Baixo índice de acerto ({taxa_acerto}%). Embora abordado na disciplina obrigatória '{info_curr['disciplina']}', o tópico demandava domínio aprofundado não retido pelos alunos."
            
        mais_erradas.append({
            'Ano': ano,
            'Questao': q,
            'Componente': r['Componente'],
            'Objetivo_de_Conhecimento': obj,
            'Gabarito_Oficial': gab,
            'Taxa_Acerto_%': f"{taxa_acerto:.2f}",
            'Taxa_Erro_%': r['Taxa_Erro_%'],
            'Opcao_Mais_Marcada': info_opt.get('Opcao_Mais_Marcada', '-'),
            'Pct_Opcao_Mais_Marcada': info_opt.get('Pct_Opcao_Mais_Marcada', 0),
            'Principal_Distrator': p_dist,
            'Pct_Principal_Distrator': p_dist_pct,
            'Distribuicao_Respostas': dist_str,
            'Presenca_na_Ementa_UFCG': info_curr['status'],
            'Disciplina_Correspondente_UFCG': info_curr['disciplina'],
            'Fator_Principal_do_Erro': fator_principal,
            'Analise_Causa_Raiz': analise
        })
        
    return mais_erradas

def gerar_tabela_anuladas(ranking_dados, dados_opcoes):
    """
    Gera o diagnóstico aprofundado das questões invalidadas / anuladas pelo INEP.
    """
    opcoes_map = {(r['Ano'], r['Questao']): r for r in dados_opcoes}
    anuladas = []
    
    itens_invalidos = [r for r in ranking_dados if r['Status'] != 'Válida']
    
    for r in itens_invalidos:
        ano = r['Ano']
        q = r['Questao']
        obj = r.get('Objetivo_de_Conhecimento', 'Não informado')
        gab = r['Gabarito_Oficial']
        status = r['Status']
        
        info_opt = opcoes_map.get((ano, q), {})
        dist_str = f"A:{info_opt.get('Pct_A',0)}% | B:{info_opt.get('Pct_B',0)}% | C:{info_opt.get('Pct_C',0)}% | D:{info_opt.get('Pct_D',0)}% | E:{info_opt.get('Pct_E',0)}%"
        
        info_curr = MAPEAMENTO_CURRICULO_UFCG.get(obj, {
            'status': 'Não aplicável ao curso' if status == 'Não aplicável ao curso' else 'Obrigatória / Eletiva',
            'disciplina': 'Outra Ênfase (SI/Licenciatura)' if status == 'Não aplicável ao curso' else 'Ciência da Computação'
        })
        
        if status == 'Não aplicável ao curso':
            tipo_inv = 'Não aplicável ao currículo de CC (Outra Ênfase no Caderno)'
            motivo = 'Questão de Sistemas de Informação ou Tecnologias'
            explicacao = 'No Enade 2011, o caderno foi compartilhado. Questões com gabarito N eram exclusivas para outros cursos da área de informática.'
        else:
            tipo_inv = 'Item Desconsiderado pelo INEP (Z)' if gab == 'Z' else 'Anulada após Recursos pelo INEP (X)'
            diag = DIAGNOSTICO_ANULACOES.get((ano, q), {
                'motivo': 'Anulação Técnica / Recurso Deferido pelo INEP',
                'explicacao': 'Questão cancelada pelo INEP devido a problemas de formulação, duplicidade de resposta ou erro de gabarito preliminar.'
            })
            motivo = diag['motivo']
            explicacao = diag['explicacao']
            
        anuladas.append({
            'Ano': ano,
            'Questao': q,
            'Componente': r['Componente'],
            'Objetivo_de_Conhecimento': obj,
            'Gabarito_Oficial': gab,
            'Status_Oficial': status,
            'Tipo_Invalidacao': tipo_inv,
            'Opcao_Mais_Marcada_Alunos': info_opt.get('Opcao_Mais_Marcada', '-'),
            'Pct_Opcao_Mais_Marcada': info_opt.get('Pct_Opcao_Mais_Marcada', 0),
            'Distribuicao_Respostas_Alunos': dist_str,
            'Presenca_na_Ementa_UFCG': info_curr['status'],
            'Disciplina_Correspondente_UFCG': info_curr['disciplina'],
            'Motivo_Tecnico_da_Invalidacao': motivo,
            'Explicacao_do_Defeito_da_Questao': explicacao
        })
        
    return anuladas

def gerar_comparativo_assuntos(ranking_dados):
    """
    Gera a tabela de evolução longitudinal dos assuntos entre as edições com objetivos mapeados.
    """
    validas_com_obj = [r for r in ranking_dados if r['Status'] == 'Válida' and r['Objetivo_de_Conhecimento'] not in ['Não mapeado', 'Não informado', '']]
    
    # Agrupar por (Objetivo, Componente)
    dados_assunto = defaultdict(lambda: {'2014': [], '2017': [], '2021': []})
    
    for r in validas_com_obj:
        ano = r['Ano']
        obj = r['Objetivo_de_Conhecimento']
        comp = r['Componente']
        taxa = float(r['Taxa_Acerto_%'])
        dados_assunto[(obj, comp)][ano].append((r['Questao'], taxa))
        
    comparativo = []
    
    for (obj, comp), anos_data in dados_assunto.items():
        q14 = anos_data['2014']
        q17 = anos_data['2017']
        q21 = anos_data['2021']
        
        m14 = round(statistics.mean([x[1] for x in q14]), 2) if q14 else None
        m17 = round(statistics.mean([x[1] for x in q17]), 2) if q17 else None
        m21 = round(statistics.mean([x[1] for x in q21]), 2) if q21 else None
        
        todas_taxas = [x[1] for q_list in anos_data.values() for x in q_list]
        media_geral = round(statistics.mean(todas_taxas), 2)
        total_q = len(todas_taxas)
        
        # Tendência
        valores_existentes = [(ano, m) for ano, m in [('2014', m14), ('2017', m17), ('2021', m21)] if m is not None]
        if len(valores_existentes) >= 2:
            if valores_existentes[-1][1] > valores_existentes[0][1] + 10:
                tendencia = 'Evolução Positiva'
            elif valores_existentes[-1][1] < valores_existentes[0][1] - 10:
                tendencia = 'Queda de Desempenho'
            elif media_geral < 35.0:
                tendencia = 'Dificuldade Crônica (<35%)'
            elif media_geral > 65.0:
                tendencia = 'Consistente em Alto Desempenho (>65%)'
            else:
                tendencia = 'Estável / Oscilante'
        else:
            if media_geral < 35.0:
                tendencia = 'Dificuldade Crônica (<35%)'
            elif media_geral > 65.0:
                tendencia = 'Alto Desempenho (>65%)'
            else:
                tendencia = 'Desempenho Mediano'
                
        # Classificação geral
        if media_geral >= 65.0:
            classificacao = 'Ponto Forte do Curso (>65%)'
        elif media_geral >= 45.0:
            classificacao = 'Desempenho Regular / Médio (45-65%)'
        else:
            classificacao = 'Ponto de Atenção / Crítico (<45%)'
            
        comparativo.append({
            'Objetivo_de_Conhecimento': obj,
            'Componente': comp,
            'Media_Acerto_2014_%': f"{m14:.2f}" if m14 is not None else '-',
            'Questoes_2014': ", ".join([x[0] for x in q14]) if q14 else '-',
            'Media_Acerto_2017_%': f"{m17:.2f}" if m17 is not None else '-',
            'Questoes_2017': ", ".join([x[0] for x in q17]) if q17 else '-',
            'Media_Acerto_2021_%': f"{m21:.2f}" if m21 is not None else '-',
            'Questoes_2021': ", ".join([x[0] for x in q21]) if q21 else '-',
            'Media_Historica_Geral_%': media_geral,
            'Total_Questoes_Avaliadas': total_q,
            'Tendencia_Historica': tendencia,
            'Classificacao_Geral': classificacao
        })
        
    comparativo.sort(key=lambda x: -x['Media_Historica_Geral_%'])
    return comparativo

def _num(valor, padrao=None):
    """Converte texto do CSV para float; devolve padrao se vazio ou inválido."""
    try:
        return float(str(valor).replace(',', '.'))
    except (ValueError, TypeError):
        return padrao


def _ordem_questao(r):
    prefixo, _, num = r['Questao'].partition('_')
    digitos = ''.join(c for c in num if c.isdigit())
    return (r['Ano'], 0 if prefixo == 'FG' else 1, int(digitos) if digitos else 0)


def gerar_tabela_analise_geral_validas(ranking_dados, dados_opcoes, anos=('2014', '2017', '2021')):
    """
    Gera a tabela de análise geral das questões válidas dos anos informados (padrão: 2014, 2017 e 2021),
    combinando distribuição de opções, mapeamento curricular e diagnóstico de anulação.
    """
    opcoes_map = {(r['Ano'], r['Questao']): r for r in dados_opcoes}
    analise = []

    itens = sorted((r for r in ranking_dados if r['Ano'] in anos and r['Status'] == 'Válida'), key=_ordem_questao)

    for r in itens:
        ano = r['Ano']
        q = r['Questao']
        comp = r['Componente']
        obj = r.get('Objetivo_de_Conhecimento', 'Não informado')
        status = r['Status']
        valida = (status == 'Válida')

        op = opcoes_map.get((ano, q), {})
        gab = op.get(
            'Gabarito_Oficial',
            r['Gabarito_Oficial']
        )  # gabarito efetivo, se disponível

        taxa_acerto = _num(r.get('Taxa_Acerto_%'))
        taxa_erro = _num(r.get('Taxa_Erro_%'))

        p_dist = op.get('Principal_Distrator', '-')
        p_dist_pct = op.get('Pct_Principal_Distrator', 0)

        # Mapeamento curricular
        info_curr = MAPEAMENTO_CURRICULO_UFCG.get(
            obj,
            {
                'status': (
                    'Formação Geral / Transversal'
                    if 'Geral' in comp
                    else 'Não aplicável ao curso'
                    if status == 'Não aplicável ao curso'
                    else 'Não mapeado'
                ),
                'disciplina': (
                    'Tema de Formação Geral (MEC/INEP)'
                    if 'Geral' in comp
                    else 'Outra Ênfase (SI/Licenciatura)'
                    if status == 'Não aplicável ao curso'
                    else 'Eletiva / Não mapeada'
                ),
            },
        )

        if not valida or taxa_acerto is None:
            nivel = 'Não se aplica (questão invalidada)'
        elif taxa_acerto < 40.0:
            nivel = 'Difícil (<40%)'
        elif taxa_acerto < 65.0:
            nivel = 'Média (40-65%)'
        else:
            nivel = 'Fácil (>=65%)'

        analise.append({
                'Ano': ano,
                'Questao': q,
                'Componente': comp,
                'Objetivo_de_Conhecimento': obj,
                'Gabarito': gab,
                'Status': status,
                'Total_Alunos': op.get('Total_Alunos', '-'),
                'Taxa_Acerto_%': f"{taxa_acerto:.2f}" if taxa_acerto is not None else '-',
                'Taxa_Erro_%': f"{taxa_erro:.2f}" if taxa_erro is not None else '-',
                'Nivel_Dificuldade': nivel,
                'Pct_A': op.get('Pct_A', '-'),
                'Pct_B': op.get('Pct_B', '-'),
                'Pct_C': op.get('Pct_C', '-'),
                'Pct_D': op.get('Pct_D', '-'),
                'Pct_E': op.get('Pct_E', '-'),
                'Pct_Branco_Rasura': op.get('Pct_Branco_Rasura', '-'),
                'Opcao_Mais_Marcada': op.get('Opcao_Mais_Marcada', '-'),
                'Pct_Opcao_Mais_Marcada': op.get('Pct_Opcao_Mais_Marcada', '-'),
                'A_Maioria_Marcou_Gabarito': op.get('A_Maioria_Marcou_Gabarito', '-'),
                'Principal_Distrator': p_dist,
                'Pct_Principal_Distrator': p_dist_pct,
                'Efeito_Distrator': op.get('Efeito_Distrator', '-'),
                'Presenca_na_Ementa_UFCG': info_curr['status'],
                'Disciplina_Correspondente_UFCG': info_curr['disciplina'],
            })

    return analise

def salvar_csv(dados, caminho):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    if not dados:
        return
    colunas = list(dados[0].keys())
    with open(caminho, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=colunas, delimiter=';')
        writer.writeheader()
        writer.writerows(dados)
    print(f"[OK] Arquivo gerado em: {caminho}")

if __name__ == '__main__':
    print("Iniciando geração das análises aprofundadas...")
    ranking = carregar_dados_ranking()
    respostas = carregar_respostas_alunos()
    
    tabela_opcoes = gerar_tabela_opcoes(ranking, respostas)
    salvar_csv(tabela_opcoes, ARQUIVO_OPCOES)
    
    tabela_mais_erradas = gerar_tabela_mais_erradas(ranking, tabela_opcoes)
    salvar_csv(tabela_mais_erradas, ARQUIVO_MAIS_ERRADAS)
    
    tabela_anuladas = gerar_tabela_anuladas(ranking, tabela_opcoes)
    salvar_csv(tabela_anuladas, ARQUIVO_ANULADAS)
    
    tabela_comparativo = gerar_comparativo_assuntos(ranking)
    salvar_csv(tabela_comparativo, ARQUIVO_COMPARATIVO_ASSUNTOS)

    tabela_geral = gerar_tabela_analise_geral_validas(ranking, tabela_opcoes)
    salvar_csv(tabela_geral, ARQUIVO_ANALISE_GERAL)
    
    print("\nProcessamento concluído com sucesso!")
