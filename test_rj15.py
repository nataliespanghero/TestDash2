# Importações necessárias
import streamlit as st
import geopandas as gpd
import folium
from folium import Choropleth, LayerControl, GeoJsonTooltip
from folium.plugins import Draw
from shapely.geometry import shape
from streamlit_folium import st_folium
import plotly.graph_objects as go

# Configuração do Streamlit
st.set_page_config(page_title="Dashboard Interativo - Risco de Atropelamento", layout="wide")

# Configuração de CSS Global
st.markdown(
    """
    <style>
    .stApp {
        background-color: white !important;
    }
    header {
        background-color: #2F50C1 !important;
    }
    section[data-testid="stSidebar"] {
        background-color: white !important;
        color: #2F50C1 !important;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] label {
        color: #2F50C1 !important;
        font-weight: bold;
    }
    h1 {
        color: #2F50C1 !important;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Adicionar a imagem no topo da sidebar com tamanho ajustado
st.sidebar.image("logo.png", width=130)

# Título principal
st.title("Dashboard Interativo: Risco de Atropelamento")

# Criação das abas
tabs = st.tabs(["Mapa Interativo", "Gráfico de Riscos"])

# Carregar dados
malha_viaria = gpd.read_file('Risco3.geojson')
hexagonos_h3 = gpd.read_file('H3.geojson')
areas_urbanas = gpd.read_file('AU.geojson')

# Escolha do tipo de risco pelo usuário
st.sidebar.header("Configurações de Risco")
tipo_risco = st.sidebar.selectbox("Selecione o tipo de risco:", ["Diurno", "Noturno"], index=0)
coluna_risco_rounded = "risk_mean_rounded_KmP" if tipo_risco == "Diurno" else "risk_mean_rounded_KmP_dark"

# Filtros
st.sidebar.header("Filtros")
selected_risks = st.sidebar.multiselect(
    "Selecione os Riscos:",
    ["Selecionar todos"] + [f"Risco {i}" for i in range(7)],
    default=["Selecionar todos"]
)
selected_concessions = st.sidebar.multiselect(
    "Selecione a Concessão:",
    ["Selecionar todos"] + list(malha_viaria['empresa'].unique()),
    default=["Selecionar todos"]
)
show_areas_urbanas = st.sidebar.selectbox("Áreas Urbanas:", ["Mostrar", "Esconder"], index=1)

# Aba 1: Mapa Interativo
with tabs[0]:
    st.header("Mapa Interativo")

    # Inicializar o mapa
    m = folium.Map(location=[-22.90, -43.20], zoom_start=8, tiles="OpenStreetMap")
    draw = Draw(export=True)
    draw.add_to(m)

    # Aplicar filtros
    hexagonos_filtrados = hexagonos_h3.copy()

    # Capturar desenho
    map_output = st_folium(m, width=800, height=600, key="mapa_interativo")
    desenho = map_output.get("last_active_drawing")

    # Aplicar filtro por desenho
    if desenho:
        try:
            geom = shape(desenho["geometry"])
            hexagonos_filtrados = hexagonos_filtrados[hexagonos_filtrados.intersects(geom)]
        except Exception as e:
            st.error(f"Erro ao processar o desenho: {e}")

    # Aplicar filtros adicionais
    if "Selecionar todos" not in selected_risks:
        selected_risk_values = [int(r.split()[1]) for r in selected_risks]
        hexagonos_filtrados = hexagonos_filtrados[
            hexagonos_filtrados[coluna_risco_rounded].isin(selected_risk_values)
        ]

    if "Selecionar todos" not in selected_concessions:
        concessoes_filtradas = malha_viaria[malha_viaria['empresa'].isin(selected_concessions)]
        if not concessoes_filtradas.empty:
            hexagonos_filtrados = hexagonos_filtrados[
                hexagonos_filtrados.intersects(concessoes_filtradas.unary_union)
            ]

    # Adicionar hexágonos filtrados ao mapa
    if not hexagonos_filtrados.empty:
        Choropleth(
            geo_data=hexagonos_filtrados,
            data=hexagonos_filtrados,
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

    # Renderizar mapa único
    st_folium(m, width=800, height=600)

# Aba 2: Gráfico
with tabs[1]:
    st.header("Gráfico de Riscos")
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
        title=dict(text=f"Distribuição de Risco ({tipo_risco})", font=dict(color="#2F50C1")),
        xaxis_title="Categoria de Risco",
        yaxis_title="% em Hexágonos",
        xaxis=dict(title=dict(font=dict(color='#2F50C1')), tickfont=dict(color='#2F50C1')),
        yaxis=dict(title=dict(font=dict(color='#2F50C1')), tickfont=dict(color='#2F50C1')),
        autosize=True,
        barmode="group",
        legend=dict(title=dict(font=dict(color='#2F50C1')), font=dict(color='#2F50C1'))
    )

    st.plotly_chart(fig, use_container_width=True)
