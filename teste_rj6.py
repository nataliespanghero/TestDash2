import streamlit as st
from streamlit_javascript import st_javascript
import geopandas as gpd
import folium
from folium import Choropleth, LayerControl, GeoJsonTooltip
from streamlit_folium import st_folium
import plotly.graph_objects as go

# Carregar dados
malha_viaria = gpd.read_file('Risco2.geojson')
hexagonos_h3 = gpd.read_file('H3.geojson')
areas_urbanas = gpd.read_file('AU.geojson')

# Calcular risco médio por hexágono, se necessário
if 'risk_mean_rounded' not in hexagonos_h3.columns:
    for index, row in hexagonos_h3.iterrows():
        segmentos_no_hex = malha_viaria[malha_viaria.intersects(row.geometry)]
        if not segmentos_no_hex.empty:
            hexagonos_h3.loc[index, 'risk_mean'] = segmentos_no_hex['KmP'].mean()
            hexagonos_h3.loc[index, 'risk_mean_rounded'] = segmentos_no_hex['KmP'].mean().round()
        else:
            hexagonos_h3.loc[index, 'risk_mean'] = 0
            hexagonos_h3.loc[index, 'risk_mean_rounded'] = 0

    hexagonos_h3.to_file('hexagonos_h3_com_risco.geojson', driver='GeoJSON')

hexagonos_h3 = gpd.read_file('hexagonos_h3_com_risco.geojson')

# Configuração do Streamlit
st.set_page_config(page_title="Dashboard Interativo - Risco de Atropelamento", layout="wide")

st.title("Dashboard Interativo: Risco de Atropelamento")

# Executar código JavaScript para obter largura e altura da janela do navegador
dimensions = st_javascript(
    """
    const width = window.innerWidth;
    const height = window.innerHeight;
    return {width, height};
    """
)

# Verificar se dimensions é válido
if dimensions and 'width' in dimensions and 'height' in dimensions:
    map_width = dimensions['width'] * 0.95  # 95% da largura da tela
    map_height = dimensions['height'] * 0.6  # 60% da altura da tela
else:
    st.warning("Não foi possível obter o tamanho da tela. Usando valores padrão.")
    map_width = 800  # Largura padrão
    map_height = 600  # Altura padrão

# Layout da página
st.sidebar.header("Configurações")

# Filtro de Riscos
risks_list = list(range(7))
selected_risks = st.sidebar.multiselect(
    "Selecione os Riscos:",
    options=["Selecionar todos"] + [f"Risco {r}" for r in risks_list],
    default=["Selecionar todos"]
)

# Filtro de Concessões
concessions_list = malha_viaria['empresa'].unique().tolist()
selected_concessions = st.sidebar.multiselect(
    "Selecione a Concessão:",
    options=["Selecionar todos"] + concessions_list,
    default=["Selecionar todos"]
)

# Opção de Áreas Urbanas
show_areas_urbanas = st.sidebar.selectbox(
    "Áreas Urbanas:",
    options=["Mostrar", "Esconder"],
    index=1  # Esconder como padrão
)

# Botão para aplicar filtros
if st.sidebar.button("Aplicar Filtros"):
    hexagonos_filtrados = hexagonos_h3.copy()

    # Filtro de riscos
    if "Selecionar todos" not in selected_risks:
        selected_risk_values = [int(r.split()[1]) for r in selected_risks]
        hexagonos_filtrados = hexagonos_filtrados[
            hexagonos_filtrados['risk_mean_rounded'].isin(selected_risk_values)
        ]

    # Filtro de concessões
    if "Selecionar todos" not in selected_concessions:
        segmentos_filtrados = malha_viaria[malha_viaria['empresa'].isin(selected_concessions)]
        if not segmentos_filtrados.empty:
            hexagonos_filtrados = hexagonos_filtrados[
                hexagonos_filtrados.intersects(segmentos_filtrados.unary_union)
            ]
else:
    # Nenhum filtro aplicado, mostrar dados completos
    hexagonos_filtrados = hexagonos_h3

# Criar mapa
if hexagonos_filtrados.empty:
    st.error("Nenhum hexágono foi encontrado para os filtros aplicados.")
else:
    m = folium.Map(location=[-22.90, -43.20], zoom_start=8, tiles="OpenStreetMap")

    # Adicionar camada de hexágonos com risco médio
    Choropleth(
        geo_data=hexagonos_filtrados,
        data=hexagonos_h3,  # Usar dados completos para manter escala de cores fixa
        columns=["index", "risk_mean_rounded"],
        key_on="feature.properties.index",
        fill_color="RdYlGn_r",
        fill_opacity=0.6,
        line_opacity=0.2,
        legend_name="Risco Médio",
        name="Hexágonos Selecionados",
        highlight=True,
    ).add_to(m)

    # Adicionar borda cinza clara aos hexágonos
    folium.GeoJson(
        hexagonos_filtrados,
        name="Hexágonos",
        style_function=lambda x: {
            'color': 'lightgray',
            'weight': 0.3,
            'fillOpacity': 0
        },
        tooltip=GeoJsonTooltip(fields=['risk_mean_rounded'], aliases=['Risco:'], localize=True),
    ).add_to(m)

    # Adicionar áreas urbanas acima de todas as camadas
    if show_areas_urbanas == "Mostrar":
        folium.GeoJson(
            areas_urbanas, 
            name="Áreas Urbanas", 
            style_function=lambda x: {'color': 'gray', 'weight': 1, 'fillOpacity': 0.5},
            tooltip=GeoJsonTooltip(fields=['Densidade'], aliases=['Densidade de urbanização:'], localize=True),
        ).add_to(m)

    LayerControl().add_to(m)

    # Exibir mapa com dimensões ajustáveis
    st_folium(m, width=map_width, height=map_height)

# Seção de gráfico
st.sidebar.header("Distribuição de Risco por Categoria")

# Calcular % de risco por categoria para hexágonos filtrados
risco_percentual_filtrado = (
    hexagonos_filtrados['risk_mean_rounded']
    .value_counts(normalize=True)
    .reindex(range(7), fill_value=0)
    .reset_index()
)
risco_percentual_filtrado.columns = ["Categoria de Risco", "%"]
risco_percentual_filtrado["%"] *= 100

# Criar gráfico de barras categorizado com quadradinhos para legenda
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
    title="Distribuição de Risco",
    xaxis_title="Categoria de Risco",
    yaxis_title="% em Hexágonos",
    autosize=True,
    barmode="group",
    legend=dict(
        title="Risco",
        itemsizing="constant",
        borderwidth=1
    )
)

# Exibir gráfico no Streamlit
st.sidebar.plotly_chart(fig)
