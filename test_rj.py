import streamlit as st
import geopandas as gpd
import folium
from folium import Choropleth, LayerControl
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

# SelectBox de municípios
selected_municipios = st.sidebar.multiselect(
    "Selecione os municípios:", 
    municipios['NM_MUN'].unique(), 
    default=[]
)

# Botão para mostrar/ocultar áreas urbanas
show_areas_urbanas = st.sidebar.selectbox("Áreas Urbanas:", ["Mostrar", "Esconder"])

# SelectBox de risco
selected_risk = st.sidebar.multiselect(
    "Selecione o risco:", 
    list(range(7)), 
    default=[]
)

# Mostrar número de municípios selecionados
if selected_municipios:
    st.sidebar.write(f"{len(selected_municipios)} Município(s) selecionado(s)")

# Filtrar municípios e hexágonos
if selected_municipios:
    municipios_filtrados = municipios[municipios['NM_MUN'].isin(selected_municipios)]
else:
    municipios_filtrados = municipios

hexagonos_filtrados = hexagonos_h3[hexagonos_h3.intersects(municipios_filtrados.unary_union)]

if selected_risk:
    hexagonos_filtrados = hexagonos_filtrados[hexagonos_filtrados['risk_mean_rounded'].isin(selected_risk)]

# Criar mapa
m = folium.Map(location=[-22.90, -43.20], zoom_start=8, tiles="OpenStreetMap")

# Adicionar camada de hexágonos com risco médio
Choropleth(
    geo_data=hexagonos_filtrados,
    data=hexagonos_filtrados,
    columns=["index", "risk_mean_rounded"],
    key_on="feature.properties.index",
    fill_color="RdYlGn_r",
    fill_opacity=0.6,
    line_opacity=0.2,
    legend_name="Risco Médio"
).add_to(m)

# Adicionar áreas urbanas, se necessário
if show_areas_urbanas == "Mostrar":
    folium.GeoJson(
        areas_urbanas, 
        name="Áreas Urbanas", 
        style_function=lambda x: {'color': 'gray', 'weight': 0.5, 'fillOpacity': 0.3}
    ).add_to(m)

# Adicionar municípios selecionados
folium.GeoJson(
    municipios_filtrados, 
    name="Municípios", 
    style_function=lambda x: {'color': 'blue', 'weight': 2}
).add_to(m)

LayerControl().add_to(m)

# Exibir mapa
st_folium(m, width=800, height=500)

# Seção de gráfico
st.sidebar.header("Distribuição de Risco por Categoria")

# Calcular % de risco por categoria
risco_percentual = (
    hexagonos_filtrados['risk_mean_rounded']
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

# Exibir gráfico no Streamlit
st.sidebar.plotly_chart(fig)
