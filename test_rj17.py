# Importações necessárias
import streamlit as st
import geopandas as gpd
import folium
from folium import Choropleth, LayerControl, GeoJsonTooltip
from folium.plugins import Draw
from shapely.geometry import shape, box
from streamlit_folium import st_folium
import plotly.graph_objects as go
from folium.plugins import MiniMap

# Configuração do Streamlit
st.set_page_config(page_title="Dashboard Interativo - Risco de Atropelamento", layout="wide")

# Importar o arquivo CSS para o Streamlit
with open("style.css") as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

# Adicionar a imagem no topo da sidebar com tamanho ajustado
st.sidebar.image("logo.png", width=130)

st.markdown(
    """
    <div style="display: flex; align-items: flex-start; justify-content: flex-start; background-color: #0F2355; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
        <h1 style="color: white; font-size: 48px; margin: 0;">Dashboard Interativo: Risco de Atropelamento</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Configuração de CSS Global
st.markdown(
    """
    <style>
        
    /* Estilo global */
    * {
        font-family: 'Exo', sans-serif !important;
    }
    .stApp {
        background-color: #0F2355 !important; /* Fundo azul da página */
    }

    /* Header e título principal */
    header {
        background-color: #0F2355 !important;
    }

    h1 {
        color: white !important;
        font-size: 48px !important; /* Tamanho maior do título */
        font-family: 'Exo', sans-serif !important; /* Aplicar Exo ao título */
        text-align: flex-start;
        margin: 0;
    }

   /* Caixa branca para mapa e gráfico */
    .main {
        background-color: white !important;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
        margin: 20px auto 0 auto; /* Remove margem inferior */
        max-width: 95%; /* Ajuste para centralizar e controlar tamanho */
    }

    iframe {
        width: 100% !important;
        height: calc(100vh - 300px) !important; /* Ajuste para usar altura da viewport */
        border-radius: 10px;
        border: none; /* Remove bordas adicionais */
    }

    /* Remove padding ou margin adicionais de elementos internos */
    .element-container {
        padding: 0 !important;
        margin: 0 !important;
    }
    .main iframe {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Subtítulo "Mapa Interativo" */
    h2 {
        color: #0F2355 !important;
        font-size: 24px;
        font-family: 'Exo', sans-serif !important; /* Garantir uso da fonte Exo */
        font-weight: bold;
        text-align: left;
        margin-bottom: 10px;
        background-color: white !important; /* Fundo branco para o título */
        padding: 10px;
        border-radius: 5px;
    }

    /* Estilo das abas */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0F2355 !important; /* Fundo azul geral das abas */
        border-bottom: none !important; /* Remove borda inferior, se houver */
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #0F2355 !important; /* Fundo azul para abas não selecionadas */
        color: white !important; /* Texto branco para abas não selecionadas */
        font-weight: bold !important;
        border-radius: 5px 5px 0 0 !important;
        padding: 10px !important;
        border: none !important; /* Remove borda ao redor das abas */
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: white !important; /* Fundo branco para aba selecionada */
        color: #0F2355 !important; /* Texto azul para aba selecionada */
        font-weight: bold !important;
        border-top: 2px solid #0F2355 !important; /* Adiciona borda superior azul */
        border-left: 2px solid #0F2355 !important;
        border-right: 2px solid #0F2355 !important;
        border-radius: 5px 5px 0 0 !important; /* Ajusta borda para encaixar visualmente */
    }

    .stTabs [data-baseweb="tab"][aria-selected="false"] {
        border: none !important; /* Remove borda das abas não selecionadas */
    }


    /* Ajuste no botão "Selecionar todos" para exibir o texto completo */
    span.st-bp {
        background-color: #0F2355 !important; /* Fundo azul */
        color: white !important; /* Texto branco */
        font-family: 'Exo', sans-serif !important; /* Fonte negrito no botão */
        font-weight: bold !important; /* Texto em negrito */
        border-radius: 5px !important; /* Cantos arredondados */
        padding: 5px 20px !important; /* Aumenta o espaço interno */
        white-space: nowrap !important; /* Evita quebra de linha */
        overflow: visible !important; /* Garante que o conteúdo fique visível */
        text-overflow: unset !important; /* Remove os "..." */
        max-width: none !important; /* Permite que o texto ocupe todo o espaço necessário */
    }

    /* Texto dentro do botão "Selecionar todos" */
    span.st-bp > span {
        color: white !important; /* Texto branco */
        font-family: 'Exo', sans-serif !important; /* Fonte negrito no botão */
        font-weight: bold !important; /* Texto em negrito */
        white-space: nowrap !important; /* Garante que o texto não quebre */
        text-overflow: unset !important; /* Remove os "..." */
        overflow: visible !important; /* Garante que o conteúdo fique visível */
    }

    /* Ícone "Delete" no botão */
    span.st-bp svg {
        fill: white !important; /* Cor do ícone branco */
    }

    /* Hover no botão "Selecionar todos" */
    span.st-bp:hover {
        background-color: #0F2355 !important; /* Azul mais escuro no hover */
        color: white !important;
    }

    /* Hover no ícone "Delete" */
    span.st-bp svg:hover {
        fill: #0F2355 !important; /* Ícone azul mais escuro no hover */
    }

    /* Ajuste adicional para a borda dos botões */
    .st-multi-select-box > div {
        border: 2px solid #0F2355 !important;
        border-radius: 5px !important;
    }

    /* Texto no select box e áreas urbanas */
    .stSelectbox div, .stRadio div {
        color: ##0F2355 !important;
        font-family: 'Exo', sans-serif !important; /* Fonte negrito no botão */
        font-weight: bold !important; /* Texto em negrito */
    }

    /* Inputs e caixas de seleção */
    div[data-baseweb="select"], div[data-baseweb="input"] {
        border: 2px solid #0F2355 !important;
        border-radius: 5px !important;
        padding: 5px !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: white !important;
        color: #0F2355 !important;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] label {
        color: #0F2355 !important;
        font-family: 'Exo', sans-serif !important; /* Fonte negrito no botão */
        font-weight: bold !important; /* Texto em negrito */
    }

    /* Hover nos botões */
    button:hover {
        background-color: #0F2355 !important;
        color: white !important;
    }

    /* Ajuste no tamanho do mapa */
    iframe {
        width: 100% !important;
        height: 800px !important; /* Aumentado para acompanhar a área branca */
        border-radius: 10px;
        border: none; /* Remove bordas adicionais */
    }

    /* Ajuste para o iframe do mapa */
    iframe.st-emotion-cache-1tvzk6f {
        height: 700px !important; /* Define uma altura fixa de 700px */
        max-height: none !important; /* Remove limite máximo de altura */
        margin-bottom: 0 !important; /* Remove a margem inferior */
    }
    
    </style>
    """,
    unsafe_allow_html=True
)

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
            hexagonos_h3.loc[index, 'risk_mean_KmP'] = segmentos_no_hex['KmP'].mean()
            hexagonos_h3.loc[index, 'risk_mean_rounded_KmP'] = segmentos_no_hex['KmP'].mean().round()
            hexagonos_h3.loc[index, 'risk_mean_KmP_dark'] = segmentos_no_hex['KmP_dark'].mean()
            hexagonos_h3.loc[index, 'risk_mean_rounded_KmP_dark'] = segmentos_no_hex['KmP_dark'].mean().round()
        else:
            hexagonos_h3.loc[index, 'risk_mean_KmP'] = 0
            hexagonos_h3.loc[index, 'risk_mean_rounded_KmP'] = 0
            hexagonos_h3.loc[index, 'risk_mean_KmP_dark'] = 0
            hexagonos_h3.loc[index, 'risk_mean_rounded_KmP_dark'] = 0

    hexagonos_h3.to_file('hexagonos_h3_com_risco.geojson', driver='GeoJSON')

hexagonos_h3 = gpd.read_file('hexagonos_h3_com_risco.geojson')

# Escolha do tipo de risco pelo usuário
st.sidebar.header("Configurações de Risco")
tipo_risco = st.sidebar.selectbox("Selecione o tipo de risco:", ["Diurno", "Noturno"], index=0)
coluna_risco = "KmP" if tipo_risco == "Diurno" else "KmP_dark"
coluna_risco_rounded = f"risk_mean_rounded_{coluna_risco}"

# Filtros
st.sidebar.header("Filtros")
risks_list = list(range(7))
selected_risks = st.sidebar.multiselect(
    "Selecione os Riscos:",
    ["Selecionar todos"] + [f"Risco {r}" for r in risks_list],
    default=["Selecionar todos"]
)
concessions_list = malha_viaria['empresa'].unique().tolist()
selected_concessions = st.sidebar.multiselect(
    "Selecione a Concessão:",
    ["Selecionar todos"] + concessions_list,
    default=["Selecionar todos"]
)
show_areas_urbanas = st.sidebar.selectbox("Áreas Urbanas:", ["Mostrar", "Esconder"], index=1)

# Filtro por coordenadas
st.sidebar.header("Filtrar por Coordenadas")
pair_1 = st.sidebar.text_input("Coordenadas Iniciais (Latitude, Longitude):", placeholder="Ex: -22.817762, -43.372672")
pair_2 = st.sidebar.text_input("Coordenadas Finais (Latitude, Longitude - opcional):", placeholder="Ex: -22.664081, -43.222538")

usar_filtro_coordenadas = False
bbox = None
if pair_1:
    try:
        lat_ini, lon_ini = map(float, pair_1.split(","))
        if pair_2:
            lat_fim, lon_fim = map(float, pair_2.split(","))
            bbox = box(min(lon_ini, lon_fim), min(lat_ini, lat_fim), max(lon_ini, lon_fim), max(lat_ini, lat_fim))
        else:
            bbox = Point(lon_ini, lat_ini).buffer(0.01)  # Pequena área ao redor do ponto
        usar_filtro_coordenadas = True
    except ValueError:
        st.sidebar.error("Erro: Insira coordenadas válidas.")

# Aba 1: Mapa Interativo
with tabs[0]:
    st.header("Mapa Interativo")

    # Inicializar mapa
    m = folium.Map(location=[-22.90, -43.20], zoom_start=8, tiles="OpenStreetMap")
    draw = Draw(export=True)
    draw.add_to(m)
    MiniMap(toggle_display=True).add_to(m)
    
    # Aplicar filtros
    hexagonos_filtrados = hexagonos_h3.copy()

    if usar_filtro_coordenadas:
        hexagonos_filtrados = hexagonos_filtrados[hexagonos_filtrados.intersects(bbox)]

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

    # Renderizar o mapa inicial
    map_data = st_folium(m, width=None, height=600)

    # Aplicar filtro por desenho
    if map_data and "all_drawings" in map_data:
        desenhos = map_data["all_drawings"]
        if desenhos:
            # Capturar a última geometria desenhada pelo usuário
            ultima_geometria = shape(desenhos[-1]["geometry"])

            # Aplicar filtro nos hexágonos já filtrados anteriormente
            hexagonos_filtrados = hexagonos_filtrados[hexagonos_filtrados.intersects(ultima_geometria)]

            # Atualizar o mapa apenas se houver hexágonos filtrados
            if not hexagonos_filtrados.empty:
                m = folium.Map(location=[-22.90, -43.20], zoom_start=8, tiles="OpenStreetMap")
                MiniMap(toggle_display=True).add_to(m)

                Choropleth(
                    geo_data=hexagonos_filtrados,
                    data=hexagonos_filtrados,
                    columns=["index", coluna_risco_rounded],
                    key_on="feature.properties.index",
                    fill_color="RdYlGn_r",
                    fill_opacity=0.6,
                    line_opacity=0.2,
                    legend_name=f"Risco Médio ({tipo_risco})",
                    name="Hexágonos Filtrados",
                    highlight=True,
                ).add_to(m)

                folium.GeoJson(
                    hexagonos_filtrados,
                    name="Hexágonos Filtrados",
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

                # Renderizar o mapa atualizado
                st_folium(m, width=None, height=600)

    else:
        # Mensagem de aviso se não houver desenhos ou erro ao capturar dados do mapa
        st.warning("Não foi possível obter os desenhos. Certifique-se de que a ferramenta de desenho está funcionando corretamente.")
        
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
        title=dict(text=f"Distribuição de Risco ({tipo_risco})", font=dict(color="#0F2355")),
        xaxis_title="Categoria de Risco",
        yaxis_title="% em Hexágonos",
        xaxis=dict(title=dict(font=dict(color='#0F2355')), tickfont=dict(color='#0F2355')),
        yaxis=dict(title=dict(font=dict(color='#0F2355')), tickfont=dict(color='#0F2355')),
        autosize=True,
        barmode="group",
        legend=dict(title=dict(font=dict(color='#0F2355')), font=dict(color='#0F2355'))
    )

    st.plotly_chart(fig, use_container_width=True)
