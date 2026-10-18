from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "V_OCORRENCIA_AMPLA.csv"
SOURCE_URL = (
    "https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos/"
    "areas-de-atuacao/seguranca-operacional/ocorrencias-aeronauticas"
)
DOWNLOAD_DATE = "18/10/2026"
BLUE, ORANGE, RED, LIGHT_BLUE = "#1D4ED8", "#F59E0B", "#DC2626", "#93C5FD"
CLASS_COLORS = {"Acidente": RED, "Incidente Grave": ORANGE}

st.set_page_config(
    page_title="Ocorrências Aeronáuticas no Brasil", page_icon="✈️", layout="wide"
)
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:12px 16px;}
    [data-testid="stMetricLabel"] {color:#475569;}
    [data-testid="stSidebar"] {background:#F8FAFC;}
    </style>
    """,
    unsafe_allow_html=True,
)


def clean_text(series: pd.Series, fallback: str = "Não informado") -> pd.Series:
    """Padroniza categorias sem transformar ausências em valores inventados."""
    return series.fillna(fallback).astype(str).str.strip().replace("", fallback)


@st.cache_data(show_spinner=False)
def load_data(csv_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Carrega o CSV e cria visões por aeronave e por ocorrência."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {csv_path.name}")

    with csv_path.open("r", encoding="utf-8-sig") as file:
        update_line = file.readline().strip()

    aircraft = pd.read_csv(
        csv_path,
        sep=";",
        skiprows=1,
        encoding="utf-8-sig",
        na_values=["null", "NULL", ""],
        low_memory=False,
    )
    aircraft["Data_da_Ocorrencia"] = pd.to_datetime(
        aircraft["Data_da_Ocorrencia"], errors="coerce"
    )
    aircraft["Hora"] = pd.to_numeric(
        aircraft["Hora_da_Ocorrencia"].str.slice(0, 2), errors="coerce"
    )

    numeric_columns = [
        "Latitude", "Longitude", "PMD", "Numero_de_Assentos",
        "Lesoes_Fatais_Tripulantes", "Lesoes_Fatais_Passageiros",
        "Lesoes_Fatais_Terceiros", "Lesoes_Graves_Tripulantes",
        "Lesoes_Graves_Passageiros", "Lesoes_Graves_Terceiros",
    ]
    for column in numeric_columns:
        if aircraft[column].dtype == "object":
            aircraft[column] = aircraft[column].str.replace(",", ".", regex=False)
        aircraft[column] = pd.to_numeric(aircraft[column], errors="coerce")

    fatal_columns = [
        "Lesoes_Fatais_Tripulantes", "Lesoes_Fatais_Passageiros",
        "Lesoes_Fatais_Terceiros",
    ]
    serious_columns = [
        "Lesoes_Graves_Tripulantes", "Lesoes_Graves_Passageiros",
        "Lesoes_Graves_Terceiros",
    ]
    aircraft["Fatalidades"] = aircraft[fatal_columns].fillna(0).sum(axis=1)
    aircraft["Lesoes_Graves"] = aircraft[serious_columns].fillna(0).sum(axis=1)

    categorical_columns = [
        "Classificacao_da_Ocorrencia", "UF", "Regiao", "Fase_da_Operacao",
        "Operacao", "Danos_a_Aeronave", "Categoria_da_Aeronave",
        "Tipo_de_Ocorrencia", "Descricao_do_Tipo", "Municipio", "Modelo",
        "Nome_do_Fabricante",
    ]
    for column in categorical_columns:
        aircraft[column] = clean_text(aircraft[column])

    aircraft["Ano"] = aircraft["Data_da_Ocorrencia"].dt.year.astype("Int64")
    aircraft["Mes"] = aircraft["Data_da_Ocorrencia"].dt.month.astype("Int64")

    # Uma ocorrência pode envolver várias aeronaves. Esta visão impede contagens
    # duplicadas nos gráficos de tempo, localização, UF e classificação.
    occurrences = (
        aircraft.sort_values(["Data_da_Ocorrencia", "Numero_da_Ocorrencia"])
        .drop_duplicates("Numero_da_Ocorrencia")
        .copy()
    )
    update_date = update_line.replace("Atualizado em:", "").strip()
    return aircraft, occurrences, update_date


def format_int(value: float | int) -> str:
    return f"{value:,.0f}".replace(",", ".")


def common_layout(fig: go.Figure, height: int = 390) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=15, r=15, t=30, b=20),
        font=dict(family="Arial", color="#0F172A"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend_title_text="",
        hoverlabel=dict(bgcolor="white"),
    )
    return fig


try:
    aircraft_raw, occurrences_raw, source_update = load_data(CSV_PATH)
except (FileNotFoundError, UnicodeDecodeError, pd.errors.ParserError) as error:
    st.error(f"Não foi possível carregar a base: {error}")
    st.info("Mantenha V_OCORRENCIA_AMPLA.csv na mesma pasta de app.py.")
    st.stop()

st.title("Ocorrências Aeronáuticas no Brasil")
st.caption("Acidentes e incidentes graves registrados na base pública da ANAC/CENIPA")

with st.expander("Sobre a base e a metodologia", expanded=False):
    st.markdown(
        f"""
        **Fonte:** [Agência Nacional de Aviação Civil (ANAC) e CENIPA]({SOURCE_URL})  
        **Arquivo utilizado:** `V_OCORRENCIA_AMPLA.csv`  
        **Data do download:** {DOWNLOAD_DATE}  
        **Atualização declarada no arquivo:** {source_update}  
        **Período disponível:** {occurrences_raw['Data_da_Ocorrencia'].min():%d/%m/%Y} a
        {occurrences_raw['Data_da_Ocorrencia'].max():%d/%m/%Y}

        A base contém ocorrências classificadas como **Acidente** ou **Incidente
        Grave**. Cada linha descreve uma aeronave associada a uma ocorrência. Como
        uma ocorrência pode envolver mais de uma aeronave, os gráficos de tempo,
        local, UF e classificação usam o número único da ocorrência. As análises de
        modelo, peso, assentos, danos e lesões usam os registros de aeronaves.

        Campos categóricos vazios aparecem como “Não informado”. Nas somas de lesões,
        ausência de registro é tratada como zero para fins de agregação.
        """
    )

st.sidebar.header("Filtros")
min_date = occurrences_raw["Data_da_Ocorrencia"].min().date()
max_date = occurrences_raw["Data_da_Ocorrencia"].max().date()
date_range = st.sidebar.date_input(
    "Período da ocorrência",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY",
)
classification_options = sorted(
    occurrences_raw["Classificacao_da_Ocorrencia"].unique().tolist()
)
selected_classifications = st.sidebar.multiselect(
    "Classificação", classification_options, default=classification_options
)
region_options = sorted(
    value for value in occurrences_raw["Regiao"].unique() if value != "Não informado"
)
selected_regions = st.sidebar.multiselect("Região", region_options)
state_options = sorted(
    value for value in occurrences_raw["UF"].unique() if value != "Não informado"
)
selected_states = st.sidebar.multiselect("UF", state_options)
operation_options = sorted(
    value for value in aircraft_raw["Operacao"].unique() if value != "Não informado"
)
selected_operations = st.sidebar.multiselect("Tipo de operação", operation_options)
st.sidebar.caption("Deixe Região, UF ou Tipo de operação vazios para incluir todos.")

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

mask_aircraft = aircraft_raw["Data_da_Ocorrencia"].dt.date.between(start_date, end_date)
mask_aircraft &= aircraft_raw["Classificacao_da_Ocorrencia"].isin(selected_classifications)
if selected_regions:
    mask_aircraft &= aircraft_raw["Regiao"].isin(selected_regions)
if selected_states:
    mask_aircraft &= aircraft_raw["UF"].isin(selected_states)
if selected_operations:
    mask_aircraft &= aircraft_raw["Operacao"].isin(selected_operations)

aircraft = aircraft_raw.loc[mask_aircraft].copy()
occurrences = (
    aircraft.sort_values(["Data_da_Ocorrencia", "Numero_da_Ocorrencia"])
    .drop_duplicates("Numero_da_Ocorrencia")
    .copy()
)
if occurrences.empty:
    st.warning("Nenhum registro atende aos filtros selecionados. Ajuste os filtros laterais.")
    st.stop()

total_occurrences = occurrences["Numero_da_Ocorrencia"].nunique()
total_aircraft = len(aircraft)
total_fatalities = int(aircraft["Fatalidades"].sum())
fatal_occurrences = aircraft.groupby("Numero_da_Ocorrencia")["Fatalidades"].sum().gt(0).sum()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Ocorrências", format_int(total_occurrences))
kpi2.metric("Aeronaves envolvidas", format_int(total_aircraft))
kpi3.metric("Fatalidades registradas", format_int(total_fatalities))
kpi4.metric(
    "Ocorrências com fatalidade",
    f"{fatal_occurrences / total_occurrences:.1%}".replace(".", ","),
)

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("1. Evolução anual das ocorrências")
    st.markdown("**Pergunta:** Como acidentes e incidentes graves evoluíram ao longo do tempo?")
    timeline = (
        occurrences.groupby(["Ano", "Classificacao_da_Ocorrencia"], observed=True)
        .size().reset_index(name="Ocorrencias")
    )
    fig1 = px.line(
        timeline, x="Ano", y="Ocorrencias", color="Classificacao_da_Ocorrencia",
        markers=True, color_discrete_map=CLASS_COLORS,
        labels={"Ano":"Ano da ocorrência", "Ocorrencias":"Ocorrências (un.)",
                "Classificacao_da_Ocorrencia":"Classificação"},
    )
    fig1.update_yaxes(rangemode="tozero")
    fig1.update_xaxes(dtick=5)
    st.plotly_chart(common_layout(fig1), width="stretch")
    peak = timeline.loc[timeline["Ocorrencias"].idxmax()]
    st.caption(
        f"Maior valor no recorte: {format_int(peak['Ocorrencias'])} "
        f"{str(peak['Classificacao_da_Ocorrencia']).lower()}(s) em {int(peak['Ano'])}."
    )

with right:
    st.subheader("2. Estados com mais ocorrências")
    st.markdown("**Pergunta:** Quais UFs concentram o maior número de ocorrências?")
    state_ranking = (
        occurrences.loc[occurrences["UF"] != "Não informado", "UF"]
        .value_counts().head(10).sort_values().rename_axis("UF")
        .reset_index(name="Ocorrencias")
    )
    fig2 = px.bar(
        state_ranking, x="Ocorrencias", y="UF", orientation="h",
        text="Ocorrencias", color_discrete_sequence=[BLUE],
        labels={"Ocorrencias":"Ocorrências (un.)", "UF":"Unidade da Federação"},
    )
    fig2.update_xaxes(rangemode="tozero")
    fig2.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(common_layout(fig2), width="stretch")
    if not state_ranking.empty:
        leader = state_ranking.iloc[-1]
        st.caption(f"No recorte atual, {leader['UF']} lidera com {format_int(leader['Ocorrencias'])} ocorrências.")

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("3. Tipos de ocorrência mais frequentes")
    st.markdown("**Pergunta:** Quais tipos de ocorrência aparecem com maior frequência em cada classificação?")
    valid_types = occurrences[
        occurrences["Descricao_do_Tipo"] != "Não informado"
    ].copy()
    top_types = valid_types["Descricao_do_Tipo"].value_counts().head(10).index
    type_data = (
        valid_types[valid_types["Descricao_do_Tipo"].isin(top_types)]
        .groupby(["Classificacao_da_Ocorrencia", "Descricao_do_Tipo"], observed=True)
        .size()
        .reset_index(name="Ocorrencias")
    )
    fig3 = px.treemap(
        type_data,
        path=["Classificacao_da_Ocorrencia", "Descricao_do_Tipo"],
        values="Ocorrencias",
        color="Classificacao_da_Ocorrencia",
        color_discrete_map=CLASS_COLORS,
        labels={
            "Classificacao_da_Ocorrencia":"Classificação",
            "Descricao_do_Tipo":"Tipo de ocorrência",
            "Ocorrencias":"Ocorrências (un.)",
        },
    )
    fig3.update_traces(
        texttemplate="<b>%{label}</b><br>%{value} ocorrências",
        hovertemplate="%{label}<br>%{value} ocorrências<extra></extra>",
    )
    st.plotly_chart(common_layout(fig3), width="stretch")
    type_totals = type_data.groupby("Descricao_do_Tipo")["Ocorrencias"].sum()
    leading_type = type_totals.idxmax()
    st.caption(
        f"No recorte atual, “{leading_type.capitalize()}” é o tipo mais frequente, "
        f"com {format_int(type_totals.max())} ocorrências."
    )

with right:
    st.subheader("4. Fases da operação")
    st.markdown("**Pergunta:** Em quais fases da operação há mais ocorrências de cada classificação?")
    top_phases = (
        occurrences.loc[occurrences["Fase_da_Operacao"] != "Não informado", "Fase_da_Operacao"]
        .value_counts().head(8).index
    )
    phases = (
        occurrences[occurrences["Fase_da_Operacao"].isin(top_phases)]
        .groupby(["Fase_da_Operacao", "Classificacao_da_Ocorrencia"], observed=True)
        .size().reset_index(name="Ocorrencias")
    )
    phase_order = phases.groupby("Fase_da_Operacao")["Ocorrencias"].sum().sort_values().index
    fig4 = px.bar(
        phases, x="Ocorrencias", y="Fase_da_Operacao",
        color="Classificacao_da_Ocorrencia", orientation="h", text="Ocorrencias",
        category_orders={"Fase_da_Operacao":phase_order.tolist()},
        color_discrete_map=CLASS_COLORS,
        labels={"Ocorrencias":"Ocorrências (un.)", "Fase_da_Operacao":"Fase da operação",
                "Classificacao_da_Ocorrencia":"Classificação"},
    )
    fig4.update_xaxes(rangemode="tozero")
    fig4.update_traces(textposition="inside")
    st.plotly_chart(common_layout(fig4), width="stretch")
    leading_phase = phases.groupby("Fase_da_Operacao")["Ocorrencias"].sum().idxmax()
    st.caption(f"A fase com mais ocorrências no recorte é {leading_phase.lower()}.")

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("5. Composição das classificações")
    st.markdown("**Pergunta:** Qual é a participação de acidentes e incidentes graves no total?")
    composition = (
        occurrences["Classificacao_da_Ocorrencia"].value_counts()
        .rename_axis("Classificacao").reset_index(name="Ocorrencias")
    )
    fig5 = px.pie(
        composition, names="Classificacao", values="Ocorrencias", hole=0.48,
        color="Classificacao", color_discrete_map=CLASS_COLORS,
    )
    fig5.update_traces(
        textposition="inside", textinfo="label+percent+value",
        hovertemplate="%{label}: %{value} ocorrências (%{percent})<extra></extra>",
    )
    st.plotly_chart(common_layout(fig5), width="stretch")
    main_class = composition.iloc[0]
    text = f"{main_class['Classificacao']} representa {main_class['Ocorrencias'] / total_occurrences:.1%} do recorte."
    st.caption(text.replace(".", ",", 1))

with right:
    st.subheader("6. Mês e horário das ocorrências")
    st.markdown("**Pergunta:** Em quais combinações de mês e horário há mais ocorrências?")
    month_names = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
                   7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
    heat_data = occurrences.dropna(subset=["Mes", "Hora"]).copy()
    heat_table = pd.crosstab(heat_data["Mes"], heat_data["Hora"]).reindex(
        index=range(1, 13), columns=range(0, 24), fill_value=0
    )
    fig6 = px.imshow(
        heat_table,
        labels={"x":"Hora do dia (h)", "y":"Mês", "color":"Ocorrências (un.)"},
        x=list(range(24)), y=[month_names[m] for m in range(1, 13)],
        color_continuous_scale=[[0,"#EFF6FF"],[0.5,LIGHT_BLUE],[1,BLUE]],
        aspect="auto", text_auto=True,
    )
    fig6.update_xaxes(dtick=2)
    st.plotly_chart(common_layout(fig6), width="stretch")
    max_position = heat_table.stack().idxmax()
    st.caption(
        f"A combinação mais frequente é {month_names[int(max_position[0])]}, "
        f"às {int(max_position[1]):02d}h, com {int(heat_table.loc[max_position])} ocorrências."
    )

st.divider()
st.subheader("7. Assentos e fatalidades")
st.markdown("**Pergunta:** Aeronaves com mais assentos apresentam mais fatalidades por registro?")
scatter = aircraft.dropna(subset=["Numero_de_Assentos"]).copy()
scatter = scatter[scatter["Numero_de_Assentos"].between(1, 600)]
fig7 = px.scatter(
    scatter, x="Numero_de_Assentos", y="Fatalidades",
    color="Classificacao_da_Ocorrencia", color_discrete_map=CLASS_COLORS,
    opacity=0.55, hover_name="Modelo",
    hover_data=["Data_da_Ocorrencia", "Municipio", "UF", "Operacao"],
    labels={"Numero_de_Assentos":"Número de assentos (un.)",
            "Fatalidades":"Fatalidades registradas (pessoas)",
            "Classificacao_da_Ocorrencia":"Classificação"},
)
fig7.update_xaxes(rangemode="tozero")
fig7.update_yaxes(rangemode="tozero")
st.plotly_chart(common_layout(fig7, height=430), width="stretch")
correlation_data = scatter[["Numero_de_Assentos", "Fatalidades"]].dropna()
correlation = correlation_data.corr().iloc[0, 1] if len(correlation_data) > 1 else float("nan")
if pd.notna(correlation):
    text = f"Correlação de Pearson no recorte: {correlation:.2f}. O gráfico mostra associação, não causalidade."
    st.caption(text.replace(".", ",", 1))

with st.expander("Consultar os registros filtrados", expanded=False):
    display_columns = [
        "Numero_da_Ocorrencia", "Data_da_Ocorrencia", "Classificacao_da_Ocorrencia",
        "Municipio", "UF", "Fase_da_Operacao", "Operacao", "Modelo",
        "Numero_de_Assentos", "Fatalidades", "Danos_a_Aeronave",
    ]
    display_names = {
        "Numero_da_Ocorrencia":"Ocorrência", "Data_da_Ocorrencia":"Data",
        "Classificacao_da_Ocorrencia":"Classificação", "Municipio":"Município",
        "Fase_da_Operacao":"Fase da operação", "Operacao":"Operação",
        "Numero_de_Assentos":"Assentos", "Danos_a_Aeronave":"Danos à aeronave",
    }
    st.dataframe(
        aircraft[display_columns].sort_values("Data_da_Ocorrencia", ascending=False)
        .rename(columns=display_names),
        width="stretch", hide_index=True,
    )

st.caption(
    "Fonte: ANAC/CENIPA. Os resultados refletem o arquivo baixado em "
    f"{DOWNLOAD_DATE} e podem mudar em atualizações futuras da base."
)
