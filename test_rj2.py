import streamlit as st
import geopandas as gpd
import folium
from folium import Choropleth, LayerControl, GeoJsonTooltip
from streamlit_folium import st_folium
import plotly.express as px

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

st.title("Dashboard Interativo: Risco de Atropelamento no Estado do Rio de Janeiro")

# Layout da página
st.sidebar.header("Configurações")

# SelectBox de municípios com "Selecionar todos"
selected_municipios = st.sidebar.multiselect(
    "Selecione os municípios:", 
    options=["Selecionar todos"] + municipios['NM_MUN'].unique().tolist(), 
    default=[]
)
if "Selecionar todos" in selected_municipios:
    selected_municipios = municipios['NM_MUN'].unique().tolist()

# SelectBox de risco com "Selecionar todos"
selected_risk = st.sidebar.multiselect(
    "Selecione o risco:", 
    options=["Selecionar todos"] + list(range(7)), 
    default=[]
)
if "Selecionar todos" in selected_risk:
    selected_risk = list(range(7))

# SelectBox de áreas urbanas com placeholder
show_areas_urbanas = st.sidebar.selectbox(
    "Áreas Urbanas:", 
    options=["Escolha uma opção", "Mostrar", "Esconder"],
    index=0
)

# Mostrar número de municípios selecionados
if selected_municipios:
    st.sidebar.write(f"{len(selected_municipios)} Município(s) selecionado(s)")

# Filtrar municípios e hexágonos
if selected_municipios:
    municipios_filtrados = municipios[municipios['NM_MUN'].isin(selected_municipios)]
    hexagonos_filtrados = hexagonos_h3[hexagonos_h3.intersects(municipios_filtrados.unary_union)]
else:
    municipios_filtrados = municipios
    hexagonos_filtrados = hexagonos_h3

if selected_risk:
    hexagonos_filtrados = hexagonos_filtrados[hexagonos_filtrados['risk_mean_rounded'].isin(selected_risk)]

# Criar mapa
m = folium.Map(location=[-22.90, -43.20], zoom_start=8, tiles="OpenStreetMap")

# Adicionar municípios abaixo de todas as camadas
folium.GeoJson(
    municipios,
    name="Municípios", 
    style_function=lambda x: {'color': 'blue', 'weight': 0.5, 'fillOpacity': 0.1}
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
    legend_name="Risco Médio"
).add_to(m)

# Adicionar tooltip aos hexágonos
folium.GeoJson(
    hexagonos_filtrados,
    tooltip=GeoJsonTooltip(fields=['risk_mean_rounded'], aliases=['Risco:'], localize=True)
).add_to(m)

# Adicionar áreas urbanas acima de todas as camadas
if show_areas_urbanas == "Mostrar":
    areas_urbanas_filtradas = areas_urbanas[areas_urbanas.intersects(municipios_filtrados.unary_union)]
    folium.GeoJson(
        areas_urbanas_filtradas, 
        name="Áreas Urbanas", 
        style_function=lambda x: {'color': 'gray', 'weight': 0.5, 'fillOpacity': 0.3},
        tooltip=GeoJsonTooltip(fields=['Densidade'], aliases=['Densidade de urbanização:'], localize=True)
    ).add_to(m)

LayerControl().add_to(m)

# Exibir mapa
st_folium(m, width=800, height=500)

# Seção de gráfico
st.sidebar.header("Distribuição de Risco por Categoria")

# Calcular % de risco por categoria (usar dados completos para garantir todas as categorias)
risco_percentual = (
    hexagonos_h3['risk_mean_rounded']
    .value_counts(normalize=True)
    .reindex(range(7), fill_value=0)
    .reset_index()
)
risco_percentual.columns = ["Categoria de Risco", "%"]
risco_percentual["%"] *= 100

# Criar gráfico de barras
fig = px.bar(
    risco_percentual, 
    x="Categoria de Risco", 
    y="%", 
    title="Distribuição de Risco", 
    color="Categoria de Risco",
    color_discrete_map={
        0: "#00FF00",  # Verde
        1: "#80FF00",
        2: "#FFFF00",
        3: "#FFBF00",
        4: "#FF8000",
        5: "#FF4000",
        6: "#FF0000"   # Vermelho
    }
)
fig.update_layout(
    xaxis=dict(tickmode='linear', tickvals=list(range(7))),
    legend=dict(itemsizing='constant')
)

# Exibir gráfico no Streamlit
st.sidebar.plotly_chart(fig)


