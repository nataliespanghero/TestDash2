import streamlit as st
from streamlit_javascript import st_javascript
import geopandas as gpd
import folium
from folium import Choropleth, LayerControl, GeoJsonTooltip
from streamlit_folium import st_folium
import plotly.graph_objects as go

# Configuração do Streamlit deve ser o primeiro comando
st.set_page_config(page_title="Dashboard Interativo - Risco de Atropelamento", layout="wide")

# Configuração de CSS Global
st.markdown(
    """
    <style>
    /* Fundo geral */
    .stApp {
        background-color: white; /* Fundo branco */
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #E7E7E9; /* Fundo da sidebar */
    }

    /* Texto geral */
    body, .stApp, .stSelectbox, .stSidebar {
        color: #142782; /* Cor do texto */
    }

    /* Caixinhas dentro do selectbox/multiselect */
    .stSelectbox > div div[role="listbox"] > div {
        background-color: #FF5722; /* Fundo laranja */
        color: white; /* Texto branco */
    }

    /* Fundo do selectbox */
    .stSelectbox > div:first-child {
        background-color: white; /* Fundo branco */
        color: #142782; /* Texto azul */
    }

    /* Legenda e título do gráfico */
    .plotly .legend, .plotly .title {
        color: #142782 !important; /* Texto azul */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Dashboard Interativo: Risco de Atropelamento")

# Carregar dados
malha_viaria = gpd.read_file('Risco3.geojson')
hexagonos_h3 = gpd.read_file('H3.geojson')
areas_urbanas = gpd.read_file('AU.geojson')

# Escolha do tipo de risco pelo usuário
st.sidebar.header("Configurações de Risco")
tipo_risco = st.sidebar.selectbox(
    "Selecione o tipo de risco:",
    options=["Diurno", "Noturno"],
    index=0  # Padrão: Diurno
)

# Determinar colunas a serem usadas com base na escolha
coluna_risco = "KmP" if tipo_risco == "Diurno" else "KmP_dark"
coluna_risco_rounded = f"risk_mean_rounded_{coluna_risco}"

# Filtros
st.sidebar.header("Filtros")

risks_list = list(range(7))
selected_risks = st.sidebar.multiselect(
    "Selecione os Riscos:",
    options=["Selecionar todos"] + [f"Risco {r}" for r in risks_list],
    default=["Selecionar todos"]
)

concessions_list = malha_viaria['empresa'].unique().tolist()
selected_concessions = st.sidebar.multiselect(
    "Selecione a Concessão:",
    options=["Selecionar todos"] + concessions_list,
    default=["Selecionar todos"]
)

show_areas_urbanas = st.sidebar.selectbox(
    "Áreas Urbanas:",
    options=["Mostrar", "Esconder"],
    index=1
)

# Aplicar filtros
hexagonos_filtrados = hexagonos_h3.copy()

if "Selecionar todos" not in selected_risks:
    selected_risk_values = [int(r.split()[1]) for r in selected_risks]
    hexagonos_filtrados = hexagonos_filtrados[
        hexagonos_filtrados[coluna_risco_rounded].isin(selected_risk_values)
    ]

if "Selecionar todos" not in selected_concessions:
    segmentos_filtrados = malha_viaria[malha_viaria['empresa'].isin(selected_concessions)]
    if not segmentos_filtrados.empty:
        hexagonos_filtrados = hexagonos_filtrados[
            hexagonos_filtrados.intersects(segmentos_filtrados.unary_union)
        ]

# Divisão em colunas (mapa à esquerda, gráfico à direita)
col1, col2 = st.columns([2, 1])  # 2/3 para o mapa, 1/3 para o gráfico

with col1:
    # Criar mapa
    if hexagonos_filtrados.empty:
        st.error("Nenhum hexágono foi encontrado para os filtros aplicados.")
    else:
        m = folium.Map(location=[-22.90, -43.20], zoom_start=8, tiles="OpenStreetMap")

        Choropleth(
            geo_data=hexagonos_filtrados,
            data=hexagonos_h3,
            columns=["index", coluna_risco_rounded],
            key_on="feature.properties.index",
            fill_color="RdYlGn_r",
            fill_opacity=0.6,
            line_opacity=0.2,
            legend_name=f"Risco Médio ({tipo_risco})",
            name="Hexágonos Selecionados",
            highlight=True,
        ).add_to(m)

        folium.GeoJson(
            hexagonos_filtrados,
            name="Hexágonos",
            style_function=lambda x: {
                'color': 'lightgray',
                'weight': 0.3,
                'fillOpacity': 0
            },
            tooltip=GeoJsonTooltip(fields=[coluna_risco_rounded], aliases=['Risco:'], localize=True),
        ).add_to(m)

        if show_areas_urbanas == "Mostrar":
            folium.GeoJson(
                areas_urbanas,
                name="Áreas Urbanas",
                style_function=lambda x: {'color': 'gray', 'weight': 1, 'fillOpacity': 0.5},
            ).add_to(m)

        LayerControl().add_to(m)

        st_folium(m, width=800, height=600)

with col2:
    # Gráfico
    risco_percentual_filtrado = (
        hexagonos_filtrados[coluna_risco_rounded]
        .value_counts(normalize=True)
        .reindex(range(7), fill_value=0)
        .reset_index()
    )
    risco_percentual_filtrado.columns = ["Categoria de Risco", "%"]
    risco_percentual_filtrado["%"] *= 100

    fig = go.Figure()
    cores = ["#008000", "#7FFF00", "#FFFF00", "#FFBF00", "#FF8000", "#FF4000", "#FF0000"]

    for i, cor in enumerate(cores):
        fig.add_trace(go.Bar(
            x=[risco_percentual_filtrado.loc[i, 'Categoria de Risco']],
            y=[risco_percentual_filtrado.loc[i, '%']],
            name=f"Risco {i}",
            marker_color=cor
        ))

    fig.update_layout(
        title=f"Distribuição de Risco ({tipo_risco})",
        xaxis_title="Categoria de Risco",
        yaxis_title="% em Hexágonos",
        autosize=True,
        barmode="group",
    )

    st.plotly_chart(fig, use_container_width=True)


