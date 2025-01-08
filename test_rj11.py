# Importações necessárias
import streamlit as st
import geopandas as gpd
import folium
from folium import Choropleth, LayerControl, GeoJsonTooltip
from streamlit_folium import st_folium
from shapely.geometry import box
import plotly.graph_objects as go

# Configuração do Streamlit
st.set_page_config(page_title="Dashboard Interativo - Risco de Atropelamento", layout="wide")

# Configuração de CSS Global
st.markdown(
    """
    <style>
    /* Fundo geral */
    .stApp {
        background-color: white !important;
    }

    /* Barra superior */
    header {
        background-color: #2F50C1 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: white !important;
        color: #2F50C1 !important;
    }

    /* Textos do sidebar */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] label {
        color: #2F50C1 !important;
        font-weight: bold;
    }

    /* Título */
    h1 {
        color: #2F50C1 !important;
        font-size: 24px;
        font-weight: bold;
    }

    /* Título do gráfico */
    .plotly .title {
        fill: #2F50C1 !important;
    }

    /* Texto das opções nos selectboxes */
    .stSelectbox div, .stMultiselect div, .stRadio div {
        color: #2F50C1 !important; /* Azul */
    }

    /* Bordas das caixinhas de filtros */
    div[data-baseweb="select"], div[data-baseweb="input"] {
        border: 2px solid #2F50C1 !important; /* Borda azul */
        border-radius: 5px !important;
        padding: 5px !important;
    }

    /* Fundo das opções selecionadas */
    .st-multi-select-box > div > div {
        background-color: #2F50C1 !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Adicionar a imagem no topo da sidebar com tamanho ajustado
st.sidebar.image("logo.png", width=130)  # Largura ajustada para ~20% (130px)

# Título principal
st.title("Dashboard Interativo: Risco de Atropelamento")

# Criação das abas
tabs = st.tabs(["Mapa Interativo", "Gráfico de Riscos"])

# Carregar dados
malha_viaria = gpd.read_file('Risco3.geojson')
hexagonos_h3 = gpd.read_file('H3.geojson')
areas_urbanas = gpd.read_file('AU.geojson')

# Calcular riscos para ambos os tipos (diurno e noturno)
if 'risk_mean_KmP' not in hexagonos_h3.columns or 'risk_mean_KmP_dark' not in hexagonos_h3.columns:
    for index, row in hexagonos_h3.iterrows():
        segmentos_no_hex = malha_viaria[malha_viaria.intersects(row.geometry)]

        if not segmentos_no_hex.empty:
            # Risco Diurno
            hexagonos_h3.loc[index, 'risk_mean_KmP'] = segmentos_no_hex['KmP'].mean()
            hexagonos_h3.loc[index, 'risk_mean_rounded_KmP'] = segmentos_no_hex['KmP'].mean().round()

            # Risco Noturno
            hexagonos_h3.loc[index, 'risk_mean_KmP_dark'] = segmentos_no_hex['KmP_dark'].mean()
            hexagonos_h3.loc[index, 'risk_mean_rounded_KmP_dark'] = segmentos_no_hex['KmP_dark'].mean().round()
        else:
            # Caso não haja segmentos
            hexagonos_h3.loc[index, 'risk_mean_KmP'] = 0
            hexagonos_h3.loc[index, 'risk_mean_rounded_KmP'] = 0
            hexagonos_h3.loc[index, 'risk_mean_KmP_dark'] = 0
            hexagonos_h3.loc[index, 'risk_mean_rounded_KmP_dark'] = 0

    # Salvar o GeoJSON com todas as colunas pré-calculadas
    hexagonos_h3.to_file('hexagonos_h3_com_risco.geojson', driver='GeoJSON')

# Recarregar o GeoDataFrame já com os valores calculados
hexagonos_h3 = gpd.read_file('hexagonos_h3_com_risco.geojson')

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

# Filtro por coordenadas
st.sidebar.header("Filtrar por Coordenadas")
lat_ini = st.sidebar.text_input("Latitude Inicial")
lon_ini = st.sidebar.text_input("Longitude Inicial")
lat_fim = st.sidebar.text_input("Latitude Final")
lon_fim = st.sidebar.text_input("Longitude Final")

# Aplicar filtro por coordenadas, se fornecido
if all([lat_ini, lon_ini, lat_fim, lon_fim]):
    try:
        # Converter para float
        lat_ini, lon_ini, lat_fim, lon_fim = map(float, [lat_ini, lon_ini, lat_fim, lon_fim])

        # Criar a bounding box
        bbox = box(min(lon_ini, lon_fim), min(lat_ini, lat_fim), max(lon_ini, lon_fim), max(lat_ini, lat_fim))
        st.sidebar.success("Coordenadas válidas. Aplicando filtro...")

        # Filtrar os dados geoespaciais com a bounding box
        hexagonos_filtrados = hexagonos_h3[hexagonos_h3.intersects(bbox)]
        segmentos_filtrados = malha_viaria[malha_viaria.intersects(bbox)]
    except ValueError:
        st.sidebar.error("Por favor, insira valores numéricos válidos para as coordenadas.")
else:
    # Se não houver coordenadas, usar os dados completos
    hexagonos_filtrados = hexagonos_h3.copy()
    segmentos_filtrados = malha_viaria.copy()

# Aplicar filtros adicionais
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

# Aba 1: Mapa Interativo
with tabs[0]:
    st.header("Mapa Interativo")

    if hexagonos_filtrados.empty:
        st.error("Nenhum hexágono atende aos critérios selecionados.")
    else:
        m = folium.Map(location=[-22.90, -43.20], zoom_start=8, tiles="OpenStreetMap")

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
        xaxis=dict(
            title=dict(font=dict(color='#2F50C1')),
            tickfont=dict(color='#2F50C1')
        ),
        yaxis=dict(
            title=dict(font=dict(color='#2F50C1')),
            tickfont=dict(color='#2F50C1')
        ),
        autosize=True,
        barmode="group",
        legend=dict(
            title=dict(font=dict(color='#2F50C1')),
            font=dict(color='#2F50C1')
        )
    )

    st.plotly_chart(fig, use_container_width=True)



