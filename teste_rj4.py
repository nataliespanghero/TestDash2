import streamlit as st
from streamlit_javascript import st_javascript
import geopandas as gpd
import folium
from folium import Choropleth, LayerControl, GeoJsonTooltip
from streamlit_folium import st_folium
from streamlit_tags import st_tags
import plotly.graph_objects as go

# Carregar dados
malha_viaria = gpd.read_file('Risco.geojson')
hexagonos_h3 = gpd.read_file('H3.geojson')
municipios = gpd.read_file('MUN_RJ.geojson')
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

# Adicionar CSS personalizado
st.markdown(
    """
    <style>
        .main {
            max-width: 95%;
            margin: auto;
        }
        .stSidebar {
            width: 25%;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Dashboard Interativo: Risco de Atropelamento no Estado do Rio de Janeiro")

# Capturar dimensões da janela do navegador com JavaScript
js_code = """
const width = window.innerWidth;
const height = window.innerHeight;
return {width, height};
"""
dimensions = st_javascript(js_code)

# Ajustar largura e altura do mapa
if dimensions:
    map_width = int(dimensions['width'] * 0.8)  # 80% da largura da janela
    map_height = int(dimensions['height'] * 0.6)  # 60% da altura da janela
else:
    map_width = 900
    map_height = 600

# Layout da página
st.sidebar.header("Configurações")

# Selectbox de municípios com checkboxes
municipios_list = municipios['NM_MUN'].unique().tolist()
selected_municipios = st_tags(
    label="Selecione os Municípios",
    text="Selecione...",
    suggestions=municipios_list,
    maxtags=len(municipios_list)
)

# Mostrar número de municípios selecionados
st.sidebar.write(f"{len(selected_municipios)} Município(s) selecionado(s)")

# Selectbox de riscos com checkboxes
risks_list = list(range(7))
selected_risk = st_tags(
    label="Selecione os Riscos",
    text="Selecione...",
    suggestions=[f"Risco {r}" for r in risks_list],
    maxtags=len(risks_list)
)

# Mostrar número de riscos selecionados
st.sidebar.write(f"{len(selected_risk)} Risco(s) selecionado(s)")

# SelectBox de áreas urbanas
show_areas_urbanas = st.sidebar.selectbox(
    "Áreas Urbanas:", 
    options=["Mostrar", "Esconder"],
    index=1  # "Esconder" como padrão
)

# Filtrar municípios e hexágonos
if selected_municipios:
    municipios_filtrados = municipios[municipios['NM_MUN'].isin(selected_municipios)]
    hexagonos_filtrados = hexagonos_h3[hexagonos_h3.intersects(municipios_filtrados.unary_union)]
else:
    municipios_filtrados = municipios
    hexagonos_filtrados = hexagonos_h3

if selected_risk:
    selected_risk_values = [int(r.split()[1]) for r in selected_risk]  # Extrair os valores numéricos
    hexagonos_filtrados = hexagonos_filtrados[hexagonos_filtrados['risk_mean_rounded'].isin(selected_risk_values)]

# Criar mapa
m = folium.Map(location=[-22.90, -43.20], zoom_start=8, tiles="OpenStreetMap")

# Adicionar municípios abaixo de todas as camadas
folium.GeoJson(
    municipios_filtrados,
    name="Municípios", 
    style_function=lambda x: {'color': 'blue', 'weight': 0.5, 'fillOpacity': 0.1},
).add_to(m)

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
    areas_urbanas_filtradas = areas_urbanas[areas_urbanas.intersects(municipios_filtrados.unary_union)]
    folium.GeoJson(
        areas_urbanas_filtradas, 
        name="Áreas Urbanas", 
        style_function=lambda x: {'color': 'gray', 'weight': 1, 'fillOpacity': 0.5},
        tooltip=GeoJsonTooltip(fields=['Densidade'], aliases=['Densidade de urbanização:'], localize=True),
    ).add_to(m)

LayerControl().add_to(m)

# Exibir mapa
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
