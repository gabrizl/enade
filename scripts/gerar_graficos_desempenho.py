import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração de estilo visual dos gráficos
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300

PASTA_GRAFICOS = "graficos_analise"
ARQUIVO_CSV = "microdados_tratados/ufcg_cc_respostas_questoes_todos_anos.csv"

os.makedirs(PASTA_GRAFICOS, exist_ok=True)

def carregar_dados():
    print(f"Carregando dados de: {ARQUIVO_CSV}")
    df = pd.read_csv(ARQUIVO_CSV, sep=';', encoding='utf-8-sig', low_memory=False)
    
    # Filtrar apenas alunos presentes com resultado válido para análise de acertos/erros
    df_presentes = df[df['Presenca'].str.contains('Presente com resultado válido', na=False, case=False)].copy()
    print(f"Total de registros: {len(df)} | Alunos presentes com resultado válido: {len(df_presentes)}")
    return df, df_presentes


def analisar_questoes_por_ano(df_presentes):
    """
    Calcula as taxas de acerto, erro e anulação para cada questão em cada ano,
    dividido estritamente por Formação Geral (FG) e Componente Específico (CE).
    """
    anos = sorted(df_presentes['Ano'].dropna().unique())
    resumo_questoes = []

    for ano in anos:
        df_ano = df_presentes[df_presentes['Ano'] == ano]
        total_alunos = len(df_ano)
        if total_alunos == 0:
            continue

        # 1. Analisar Formação Geral (FG)
        cols_acerto_fg = [c for c in df_ano.columns if c.startswith('Acerto_FG_')]
        for col in cols_acerto_fg:
            num_q = col.replace('Acerto_FG_', '')
            serie = df_ano[col].dropna()
            if len(serie) == 0:
                continue
            
            acertos = (serie == 'Acertou').sum()
            erros = (serie == 'Errou').sum()
            branco = (serie == 'Em branco').sum()
            anulado = (serie == 'Item anulado').sum() + (serie == 'Item desconsiderado').sum()

            validos_resposta = acertos + erros + branco
            if validos_resposta > 0:
                taxa_acerto = (acertos / validos_resposta) * 100
                taxa_erro = (erros / validos_resposta) * 100
            else:
                taxa_acerto = np.nan
                taxa_erro = np.nan

            resumo_questoes.append({
                'Ano': int(ano),
                'Tipo': 'Formação Geral (FG)',
                'Questao': f'FG_{num_q}',
                'Total_Alunos': total_alunos,
                'Acertos': acertos,
                'Erros': erros,
                'Em_Branco': branco,
                'Anulados': anulado,
                'Taxa_Acerto_%': taxa_acerto,
                'Taxa_Erro_%': taxa_erro
            })

        # 2. Analisar Componente Específico (CE)
        cols_acerto_ce = [c for c in df_ano.columns if c.startswith('Acerto_CE_')]
        for col in cols_acerto_ce:
            num_q = col.replace('Acerto_CE_', '')
            serie = df_ano[col].dropna()
            if len(serie) == 0:
                continue

            acertos = (serie == 'Acertou').sum()
            erros = (serie == 'Errou').sum()
            branco = (serie == 'Em branco').sum()
            anulado = (serie == 'Item anulado').sum() + (serie == 'Item desconsiderado').sum()
            nao_aplicavel = (serie == 'Não aplicável').sum()

            if nao_aplicavel == len(serie):
                continue

            validos_resposta = acertos + erros + branco
            if validos_resposta > 0:
                taxa_acerto = (acertos / validos_resposta) * 100
                taxa_erro = (erros / validos_resposta) * 100
            else:
                taxa_acerto = np.nan
                taxa_erro = np.nan

            resumo_questoes.append({
                'Ano': int(ano),
                'Tipo': 'Componente Específico (CE)',
                'Questao': f'CE_{num_q}',
                'Total_Alunos': total_alunos,
                'Acertos': acertos,
                'Erros': erros,
                'Em_Branco': branco,
                'Anulados': anulado,
                'Taxa_Acerto_%': taxa_acerto,
                'Taxa_Erro_%': taxa_erro
            })

    df_resumo = pd.DataFrame(resumo_questoes)
    df_resumo.to_csv(os.path.join(PASTA_GRAFICOS, "tabela_resumo_desempenho_questoes.csv"), index=False, sep=';', encoding='utf-8-sig')
    return df_resumo


def gerar_graficos_extremos_separados(df_resumo):
    """
    Gera gráficos 2x2 para cada ano separando estritamente:
    - Linha 1: Conhecimento Geral (Mais Acertadas vs Mais Erradas)
    - Linha 2: Conhecimento Específico (Mais Acertadas vs Mais Erradas)
    """
    anos = sorted(df_resumo['Ano'].unique())

    for ano in anos:
        df_ano = df_resumo[df_resumo['Ano'] == ano].copy()

        df_fg = df_ano[(df_ano['Tipo'] == 'Formação Geral (FG)') & (df_ano['Taxa_Acerto_%'].notna())].copy()
        df_ce = df_ano[(df_ano['Tipo'] == 'Componente Específico (CE)') & (df_ano['Taxa_Acerto_%'].notna())].copy()

        # FG Top 4 (pois FG costuma ter 7-8 questões no total)
        top_acerto_fg = df_fg.nlargest(4, 'Taxa_Acerto_%').sort_values('Taxa_Acerto_%', ascending=True)
        top_erro_fg = df_fg.nlargest(4, 'Taxa_Erro_%').sort_values('Taxa_Erro_%', ascending=True)

        # CE Top 5
        top_acerto_ce = df_ce.nlargest(5, 'Taxa_Acerto_%').sort_values('Taxa_Acerto_%', ascending=True)
        top_erro_ce = df_ce.nlargest(5, 'Taxa_Erro_%').sort_values('Taxa_Erro_%', ascending=True)

        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(f'ENADE {ano} - Desempenho Separado por Tipo de Conhecimento (UFCG - CC)', fontsize=15, fontweight='bold', y=0.98)

        # 1. FG Mais Acertadas
        b1 = axes[0, 0].barh(top_acerto_fg['Questao'], top_acerto_fg['Taxa_Acerto_%'], color='#1b5e20', alpha=0.85, edgecolor='black')
        axes[0, 0].set_title('Conhecimento Geral (FG) - Mais Acertadas', fontsize=12, fontweight='bold', color='#1b5e20')
        axes[0, 0].set_xlabel('Taxa de Acerto (%)', fontsize=10)
        axes[0, 0].set_xlim(0, 108)
        for b in b1:
            w = b.get_width()
            axes[0, 0].text(w + 1.5, b.get_y() + b.get_height()/2, f'{w:.1f}%', va='center', fontsize=10, fontweight='bold')

        # 2. FG Mais Erradas
        b2 = axes[0, 1].barh(top_erro_fg['Questao'], top_erro_fg['Taxa_Erro_%'], color='#b71c1c', alpha=0.85, edgecolor='black')
        axes[0, 1].set_title('Conhecimento Geral (FG) - Mais Erradas', fontsize=12, fontweight='bold', color='#b71c1c')
        axes[0, 1].set_xlabel('Taxa de Erro (%)', fontsize=10)
        axes[0, 1].set_xlim(0, 108)
        for b in b2:
            w = b.get_width()
            axes[0, 1].text(w + 1.5, b.get_y() + b.get_height()/2, f'{w:.1f}%', va='center', fontsize=10, fontweight='bold')

        # 3. CE Mais Acertadas
        b3 = axes[1, 0].barh(top_acerto_ce['Questao'], top_acerto_ce['Taxa_Acerto_%'], color='#0d47a1', alpha=0.85, edgecolor='black')
        axes[1, 0].set_title('Conhecimento Específico (CE) - Mais Acertadas', fontsize=12, fontweight='bold', color='#0d47a1')
        axes[1, 0].set_xlabel('Taxa de Acerto (%)', fontsize=10)
        axes[1, 0].set_xlim(0, 108)
        for b in b3:
            w = b.get_width()
            axes[1, 0].text(w + 1.5, b.get_y() + b.get_height()/2, f'{w:.1f}%', va='center', fontsize=10, fontweight='bold')

        # 4. CE Mais Erradas
        b4 = axes[1, 1].barh(top_erro_ce['Questao'], top_erro_ce['Taxa_Erro_%'], color='#e65100', alpha=0.85, edgecolor='black')
        axes[1, 1].set_title('Conhecimento Específico (CE) - Mais Erradas', fontsize=12, fontweight='bold', color='#e65100')
        axes[1, 1].set_xlabel('Taxa de Erro (%)', fontsize=10)
        axes[1, 1].set_xlim(0, 108)
        for b in b4:
            w = b.get_width()
            axes[1, 1].text(w + 1.5, b.get_y() + b.get_height()/2, f'{w:.1f}%', va='center', fontsize=10, fontweight='bold')

        plt.tight_layout()
        caminho_salvar = os.path.join(PASTA_GRAFICOS, f'extremos_separados_enade_{ano}.png')
        plt.savefig(caminho_salvar, bbox_inches='tight')
        plt.close()
        print(f"Gráfico separado salvo: {caminho_salvar}")


def gerar_grafico_evolucao_notas(df_presentes):
    cols_notas = ['Nota_Geral', 'Nota_Formacao_Geral', 'Nota_Especifica_Computacao',
                  'Nota_Objetiva_FG', 'Nota_Discursiva_FG', 'Nota_Objetiva_CE', 'Nota_Discursiva_CE']
    
    df_calc = df_presentes.copy()
    for col in cols_notas:
        if col in df_calc.columns:
            df_calc[col] = pd.to_numeric(df_calc[col].astype(str).str.replace(',', '.'), errors='coerce')

    medias = df_calc.groupby('Ano')[cols_notas].mean().reset_index()

    plt.figure(figsize=(12, 6))
    plt.plot(medias['Ano'], medias['Nota_Geral'], marker='o', linewidth=3, markersize=8, label='Nota Geral', color='#1565c0')
    plt.plot(medias['Ano'], medias['Nota_Formacao_Geral'], marker='s', linewidth=2.5, markersize=7, label='Conhecimento Geral (FG)', color='#2e7d32')
    plt.plot(medias['Ano'], medias['Nota_Especifica_Computacao'], marker='^', linewidth=2.5, markersize=7, label='Conhecimento Específico (CE)', color='#e65100')

    plt.title('Evolução das Médias das Notas no ENADE (UFCG - Ciência da Computação)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Ano do ENADE', fontsize=12, fontweight='bold')
    plt.ylabel('Média da Nota (0 a 100)', fontsize=12, fontweight='bold')
    plt.xticks(medias['Ano'], [str(int(a)) for a in medias['Ano']], fontsize=11)
    plt.ylim(0, 100)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=11)

    for _, row in medias.iterrows():
        plt.annotate(f"{row['Nota_Geral']:.1f}", (row['Ano'], row['Nota_Geral']), textcoords="offset points", xytext=(0,10), ha='center', fontweight='bold', color='#1565c0')
        plt.annotate(f"{row['Nota_Formacao_Geral']:.1f}", (row['Ano'], row['Nota_Formacao_Geral']), textcoords="offset points", xytext=(0,10), ha='center', color='#2e7d32')
        plt.annotate(f"{row['Nota_Especifica_Computacao']:.1f}", (row['Ano'], row['Nota_Especifica_Computacao']), textcoords="offset points", xytext=(0,-15), ha='center', color='#e65100')

    plt.tight_layout()
    caminho_notas = os.path.join(PASTA_GRAFICOS, 'evolucao_notas_medias_ufcg.png')
    plt.savefig(caminho_notas, bbox_inches='tight')
    plt.close()


def gerar_dashboard_html_separado(df_resumo, df_presentes):
    """
    Gera o dashboard HTML separando com clareza Conhecimento Geral e Conhecimento Específico.
    """
    anos = sorted(df_resumo['Ano'].unique())
    
    tabelas_html = ""
    for ano in anos:
        df_ano = df_resumo[df_resumo['Ano'] == ano].copy()
        
        df_fg = df_ano[(df_ano['Tipo'] == 'Formação Geral (FG)') & (df_ano['Taxa_Acerto_%'].notna())]
        df_ce = df_ano[(df_ano['Tipo'] == 'Componente Específico (CE)') & (df_ano['Taxa_Acerto_%'].notna())]

        top_acerto_fg = df_fg.nlargest(4, 'Taxa_Acerto_%')
        top_erro_fg = df_fg.nlargest(4, 'Taxa_Erro_%')

        top_acerto_ce = df_ce.nlargest(5, 'Taxa_Acerto_%')
        top_erro_ce = df_ce.nlargest(5, 'Taxa_Erro_%')

        tabelas_html += f"""
        <div class="ano-card">
            <div class="ano-header">
                <h3>📅 ENADE {ano}</h3>
                <span class="badge-ano">{df_ano['Total_Alunos'].iloc[0]} Estudantes Presentes</span>
            </div>

            <!-- BLOCO 1: CONHECIMENTO GERAL -->
            <div class="tipo-bloco">
                <h4 class="bloco-titulo bg-fg">📘 Conhecimento Geral (Formação Geral)</h4>
                <div class="row">
                    <div class="col">
                        <h5 class="text-success">✅ Mais Acertadas (FG)</h5>
                        <table>
                            <thead><tr><th>Questão</th><th>% Acerto</th><th>% Erro</th></tr></thead>
                            <tbody>
                                {''.join([f"<tr><td><b>{r['Questao']}</b></td><td class='badge-success'>{r['Taxa_Acerto_%']:.1f}%</td><td>{r['Taxa_Erro_%']:.1f}%</td></tr>" for _, r in top_acerto_fg.iterrows()])}
                            </tbody>
                        </table>
                    </div>
                    <div class="col">
                        <h5 class="text-danger">❌ Mais Erradas (FG)</h5>
                        <table>
                            <thead><tr><th>Questão</th><th>% Erro</th><th>% Acerto</th></tr></thead>
                            <tbody>
                                {''.join([f"<tr><td><b>{r['Questao']}</b></td><td class='badge-danger'>{r['Taxa_Erro_%']:.1f}%</td><td>{r['Taxa_Acerto_%']:.1f}%</td></tr>" for _, r in top_erro_fg.iterrows()])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- BLOCO 2: CONHECIMENTO ESPECÍFICO -->
            <div class="tipo-bloco">
                <h4 class="bloco-titulo bg-ce">💻 Conhecimento Específico (Ciência da Computação)</h4>
                <div class="row">
                    <div class="col">
                        <h5 class="text-primary">✅ Mais Acertadas (CE)</h5>
                        <table>
                            <thead><tr><th>Questão</th><th>% Acerto</th><th>% Erro</th></tr></thead>
                            <tbody>
                                {''.join([f"<tr><td><b>{r['Questao']}</b></td><td class='badge-primary'>{r['Taxa_Acerto_%']:.1f}%</td><td>{r['Taxa_Erro_%']:.1f}%</td></tr>" for _, r in top_acerto_ce.iterrows()])}
                            </tbody>
                        </table>
                    </div>
                    <div class="col">
                        <h5 class="text-warning">❌ Mais Erradas (CE)</h5>
                        <table>
                            <thead><tr><th>Questão</th><th>% Erro</th><th>% Acerto</th></tr></thead>
                            <tbody>
                                {''.join([f"<tr><td><b>{r['Questao']}</b></td><td class='badge-warning'>{r['Taxa_Erro_%']:.1f}%</td><td>{r['Taxa_Acerto_%']:.1f}%</td></tr>" for _, r in top_erro_ce.iterrows()])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="img-container">
                <img src="extremos_separados_enade_{ano}.png" alt="Gráficos ENADE {ano}">
            </div>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Desempenho ENADE - Separado por Tipo de Conhecimento (UFCG)</title>
    <style>
        :root {{
            --primary: #0d47a1;
            --success: #1b5e20;
            --danger: #b71c1c;
            --warning: #e65100;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 24px;
        }}
        .header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .header h1 {{ margin: 0 0 10px 0; font-size: 26px; }}
        .header p {{ margin: 0; opacity: 0.9; font-size: 15px; }}
        .card {{
            background: var(--card-bg);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid #e2e8f0;
            margin-bottom: 25px;
        }}
        .card h2 {{ margin-top: 0; font-size: 18px; color: var(--primary); }}
        .card img {{ width: 100%; border-radius: 6px; }}
        .ano-card {{
            background: var(--card-bg);
            padding: 24px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            margin-bottom: 30px;
            border: 1px solid #cbd5e1;
        }}
        .ano-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .ano-header h3 {{ margin: 0; font-size: 22px; color: #0f172a; }}
        .badge-ano {{
            background: #e2e8f0;
            color: #334155;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        .tipo-bloco {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
        }}
        .bloco-titulo {{
            margin: -16px -16px 14px -16px;
            padding: 10px 16px;
            border-top-left-radius: 7px;
            border-top-right-radius: 7px;
            color: white;
            font-size: 15px;
            font-weight: bold;
        }}
        .bg-fg {{ background: linear-gradient(90deg, #1b5e20, #2e7d32); }}
        .bg-ce {{ background: linear-gradient(90deg, #0d47a1, #1565c0); }}
        .row {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .col {{
            flex: 1;
            min-width: 280px;
            background: white;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
        }}
        .col h5 {{ margin: 0 0 10px 0; font-size: 14px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th, td {{
            padding: 7px 10px;
            text-align: left;
            border-bottom: 1px solid #f1f5f9;
        }}
        th {{ background-color: #f8fafc; font-weight: 600; color: #475569; }}
        .text-success {{ color: var(--success); }}
        .text-danger {{ color: var(--danger); }}
        .text-primary {{ color: var(--primary); }}
        .text-warning {{ color: var(--warning); }}
        .badge-success {{ color: var(--success); font-weight: bold; }}
        .badge-danger {{ color: var(--danger); font-weight: bold; }}
        .badge-primary {{ color: var(--primary); font-weight: bold; }}
        .badge-warning {{ color: var(--warning); font-weight: bold; }}
        .img-container {{ margin-top: 20px; text-align: center; }}
        .img-container img {{ max-width: 100%; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Painel de Desempenho ENADE (2005 a 2021)</h1>
        <p>Curso: <b>Ciência da Computação (Bacharelado)</b> | Instituição: <b>UFCG</b></p>
        <p style="margin-top: 5px; font-size: 13px;">Foco: <b>Separação entre Conhecimento Geral e Conhecimento Específico</b></p>
    </div>

    <div class="card">
        <h2>📈 Evolução das Médias das Notas (Conhecimento Geral vs. Específico)</h2>
        <img src="evolucao_notas_medias_ufcg.png" alt="Evolução das Notas">
    </div>

    <h2>Análise Detalhada por Edição do ENADE</h2>
    {tabelas_html}
</body>
</html>
"""
    caminho_html = os.path.join(PASTA_GRAFICOS, "dashboard_desempenho_enade.html")
    with open(caminho_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"\n[SUCESSO] Dashboard interativo atualizado em:\n  -> {caminho_html}")


def main():
    print("=== Gerando Gráficos Separados por FG e CE ===")
    df, df_presentes = carregar_dados()
    df_resumo = analisar_questoes_por_ano(df_presentes)
    
    gerar_graficos_extremos_separados(df_resumo)
    gerar_grafico_evolucao_notas(df_presentes)
    gerar_dashboard_html_separado(df_resumo, df_presentes)
    print("\nProcessamento finalizado com sucesso!")


if __name__ == "__main__":
    main()
