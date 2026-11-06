import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Desemprego", layout="wide", page_icon="📊")

try:
    df_2012 = pd.read_csv("Tabela5-sem_emprego_2012.csv", sep=";", decimal=",")
    df_2026 = pd.read_csv("Tabela5-sem_emprego_2026.csv", sep=";", decimal=",")
except FileNotFoundError:
    st.error("Certifique-se de que os arquivos CSV estão no mesmo diretório ou com caminhos corretos.")
    st.stop()

col_homens_2012 = [c for c in df_2012.columns if "homens" in c.lower()][0]
col_mulheres_2012 = [c for c in df_2012.columns if "mulheres" in c.lower()][0]

col_homens_2026 = [c for c in df_2026.columns if "homens" in c.lower()][0]
col_mulheres_2026 = [c for c in df_2026.columns if "mulheres" in c.lower()][0]

df_2012["Total_2012"] = df_2012[col_homens_2012] + df_2012[col_mulheres_2012]
df_2026["Total_2026"] = df_2026[col_homens_2026] + df_2026[col_mulheres_2026]

df_comparativo = pd.merge(
    df_2012[["Sigla", "Estado", col_homens_2012, col_mulheres_2012, "Total_2012"]],
    df_2026[["Sigla", col_homens_2026, col_mulheres_2026, "Total_2026"]],
    on="Sigla"
)

df_comparativo.rename(columns={
    col_homens_2012: "Homens_2012",
    col_mulheres_2012: "Mulheres_2012",
    col_homens_2026: "Homens_2026",
    col_mulheres_2026: "Mulheres_2026"
}, inplace=True)


# --- SIDEBAR E FILTROS ---
st.sidebar.header("🔍 Filtros")

ufs = sorted(df_comparativo["Sigla"].unique())
ufs_sel = st.sidebar.multiselect("Selecione o UF: ", ufs, default=ufs)

generos = ["Masculino", "Feminino"]
generos_sel = st.sidebar.multiselect("Gênero", generos, default=generos)

if not ufs_sel or not generos_sel:
    st.warning("Selecione pelo menos um UF e um Gênero.")
    st.stop()


# --- PROCESSAMENTO DOS DADOS FILTRADOS ---
df_filtrado = df_comparativo[df_comparativo["Sigla"].isin(ufs_sel)].copy()

# Cálculo das reduções individuais para evitar o problema de valores zerados
df_filtrado["Reducao_Homens"] = df_filtrado["Homens_2012"] - df_filtrado["Homens_2026"]
df_filtrado["Reducao_Mulheres"] = df_filtrado["Mulheres_2012"] - df_filtrado["Mulheres_2026"]

# Preparação do DataFrame Long para o primeiro gráfico
df_genero_long = df_filtrado.melt(
    id_vars=["Estado", "Sigla"],
    value_vars=["Homens_2012", "Mulheres_2012", "Homens_2026", "Mulheres_2026"],
    var_name="Categoria",
    value_name="Desocupados"
)

df_genero_long["Gênero"] = df_genero_long["Categoria"].apply(lambda x: "Masculino" if "Homens" in x else "Feminino")
df_genero_long["Ano"] = df_genero_long["Categoria"].apply(lambda x: "2012" if "2012" in x else "2026")

df_genero_long_filtrado = df_genero_long[df_genero_long["Gênero"].isin(generos_sel)]


# --- LAYOUT DA TELA PRINCIPAL ---
st.title("📊 População Desempregada")

# Subheader 1: Gráfico de Barras Agrupadas
st.subheader("1. Comparação da População Desocupada por Gênero e UF (2012 vs 2026)")
fig_genero = px.bar(
    df_genero_long_filtrado,
    x="Sigla",
    y="Desocupados",
    color="Gênero",
    barmode="group",
    facet_row="Ano",
    title="Desocupação por UF, Gênero e Ano",
    labels={"Sigla": "UF", "Desocupados": "Quantidade de Desocupados"},
    height=600
)
st.plotly_chart(fig_genero, use_container_width=True)


# Subheader 2: Gráficos de Redução Absoluta Divididos por Gênero
st.subheader("2. Redução da População Desocupada por Gênero (2012 para 2026)")
st.caption("Valores positivos indicam melhora (redução do número de desempregados)")

# Criando duas colunas lado a lado para colocar os gráficos de Homens e Mulheres
col1, col2 = st.columns(2)

with col1:
    if "Masculino" in generos_sel:
        df_reducao_m = df_filtrado.sort_values(by="Reducao_Homens", ascending=False)
        fig_m = px.bar(
            df_reducao_m,
            x="Sigla",
            y="Reducao_Homens",
            title="Redução Absoluta: Homens",
            labels={"Sigla": "UF", "Reducao_Homens": "Diferença Absoluta (2012 - 2026)"},
            color="Reducao_Homens",
            color_continuous_scale=px.colors.sequential.Blues
        )
        st.plotly_chart(fig_m, use_container_width=True)
        
        if not df_reducao_m.empty:
            campeao_m = df_reducao_m.iloc[0]
            st.info(f"Maior redução masculina: **{campeao_m['Estado']} ({campeao_m['Sigla']})** com **{int(campeao_m['Reducao_Homens'])}** menos desocupados.")
    else:
        st.info("Gênero Masculino não selecionado no filtro.")

with col2:
    if "Feminino" in generos_sel:
        df_reducao_f = df_filtrado.sort_values(by="Reducao_Mulheres", ascending=False)
        fig_f = px.bar(
            df_reducao_f,
            x="Sigla",
            y="Reducao_Mulheres",
            title="Redução Absoluta: Mulheres",
            labels={"Sigla": "UF", "Reducao_Mulheres": "Diferença Absoluta (2012 - 2026)"},
            color="Reducao_Mulheres",
            color_continuous_scale=px.colors.sequential.RdPu
        )
        st.plotly_chart(fig_f, use_container_width=True)
        
        if not df_reducao_f.empty:
            campeao_f = df_reducao_f.iloc[0]
            st.info(f"Maior redução feminina: **{campeao_f['Estado']} ({campeao_f['Sigla']})** com **{int(campeao_f['Reducao_Mulheres'])}** menos desocupadas.")
    else:
        st.info("Gênero Feminino não selecionado no filtro.")
        
        
st.subheader("3. Notícias recentes sobre os índices da PNAD Contínua (IBGE)")
st.caption("Os dados mais recentes da Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD Contínua) indicam um cenário altamente aquecido no mercado de trabalho geral:")

st.caption("Taxa de Desocupação:")
st.write("O desemprego no Brasil recuou para 5,2% no trimestre encerrado em setembro, estabelecendo o menor índice para este período na série histórica iniciada em 2012.")

st.caption("Recorde de Ocupação:")
st.write("A parcela da população em idade ativa que está efetivamente trabalhando atingiu o recorde de 59% no 3º trimestre. O número total de pessoas ocupadas no país estabilizou-se no patamar histórico superior a 103 milhões. ")


st.caption("Rendimento Médio:")
st.write("O rendimento mensal real habitual do trabalhador brasileiro ficou estimado em R$ 3.790, registrando um crescimento real de 3,6% na comparação anual.")