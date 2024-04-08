import pandas as pd
import pandas as pd
import folium
import matplotlib.pyplot as plt
import numpy as np
from folium.plugins import HeatMapWithTime, HeatMap
import pickle
import streamlit as st
from streamlit_folium import st_folium
from streamlit_folium import folium_static
import geopandas as gpd


st.set_page_config(
    page_title="st_folium Example",
    page_icon="🔎",
    layout="wide"
)

@st.cache_data
def load_data_temporal(vue):
    if vue == 'Daily vision':
        fichier_pickle = "ny_per_hour.pickle"
    else:  # vue == 'Weekly vision'
        fichier_pickle = "ny_per_dow.pickle"

    with open(fichier_pickle, "rb") as fichier:
        data = pickle.load(fichier)

    m = folium.Map([40.73, -73.94], tiles="CartoDB Positron", zoom_start=11, scrollWheelZoom=False)

    ny_uni = pd.read_csv('newyork_uni.csv')
    text_analysis = {'School':{'Daily vision':'Here we see the pike around 8AM which corresponds to the opening of the school buildings. After 6PM the schools start to close and the visits frequency drop.',
                        'Weekly vision': 'The schools are less frequencted the week-end where students take a break'},
                'Night Club': {'Daily vision':'The nightclubs are active during the night,with a gradual increase up to midnight and a quick decrease.',
                                'Weekly vision': 'The nightclubs are getting crowded at the end of the week when the New-Yorkers need a break from their stressful week.'},
                'Shopping': {'Daily vision':'The shopping venues are getting more and more visited untill 6PM, after that the visits decrease strongly',
                                'Weekly vision': 'The New-Yorkers are pretty constant when it comes to shopping, the venues visits are pretty stable.'},
                'Restaurant': {'Daily vision':'The Ney-Yorkers eat all day long but we observe 3 pikes : the breakfast one around 9AM and then lunch and diner respectively around 1PM and 7PM',
                                'Weekly vision': 'The New-Yorkers are pretty constant when it comes to restaurants visits, but we can see a slight increase over the week and then a decrase on Sunday. The New-Yorkers appear to eat more at home on this special day.'},
                }
    

    return data, m, ny_uni, text_analysis

@st.cache_data
def load_data_geo():
    ny_uni = pd.read_csv('newyork_uni.csv')
    nybb = gpd.read_file("neighborhoods.geojson")
    m = folium.Map([40.73, -73.94], tiles="CartoDB Positron", zoom_start=11, scrollWheelZoom=False)
    ny_gdf_neighborhoods = pd.read_csv('newyork_df.csv')
    
    data = pd.DataFrame(nybb["ntaname"])

    # Nightclub
    nightclub_df = ny_gdf_neighborhoods[ny_gdf_neighborhoods["Category"] == "NightClub"]
    nightclub_counts = nightclub_df.groupby("ntaname").size().reset_index(name="Night Club").sort_values(by='Night Club', ascending=False)
    data = pd.merge(data, nightclub_counts, on='ntaname', how='left').fillna(0)

    # Restaurant
    resto_df = ny_gdf_neighborhoods[ny_gdf_neighborhoods["Category"] == "Restaurant"]
    resto_counts = resto_df.groupby("ntaname").size().reset_index(name="Restaurant").sort_values(by='Restaurant', ascending=False)
    data = pd.merge(data, resto_counts, on='ntaname', how='left').fillna(0)

    # Shopping
    shop_df = ny_gdf_neighborhoods[ny_gdf_neighborhoods["Category"] == "Shopping"]
    shop_counts = shop_df.groupby("ntaname").size().reset_index(name="Shopping").sort_values(by='Shopping', ascending=False)
    data = pd.merge(data, shop_counts, on='ntaname', how='left').fillna(0)

    # School
    school_df = ny_gdf_neighborhoods[ny_gdf_neighborhoods["Category"] == "School"]
    school_counts = school_df.groupby("ntaname").size().reset_index(name="School").sort_values(by='School', ascending=False)
    data = pd.merge(data, school_counts, on='ntaname', how='left').fillna(0)

    data = pd.merge(nybb[['ntaname', 'geometry']], data, on='ntaname', how='inner')

    return m, nybb, data, ny_uni



st.title('New York City Check-Ins Analysis')

analysis = st.sidebar.selectbox(
    'Select the analysis',
    ('Temporal analysis', 'Geographical analysis'), key="disabled")

if analysis == "Temporal analysis":

    vue_choisie = st.sidebar.radio("Select the analysis temporality", ('Daily vision', 'Weekly vision'))

    data, m, ny_uni, text_analysis = load_data_temporal(vue_choisie)

    elements = ['School', 'Restaurant', 'Shopping', 'Night Club']
    valeur_selectionnee = st.sidebar.radio("Select the establishement type", elements)

    st.markdown(f"## Geographical view of the visits to {valeur_selectionnee.lower()}s over time with a {vue_choisie.lower()} :")

    if valeur_selectionnee == "School":

        for lat, lng, name in zip(ny_uni['Latitude'], ny_uni['Longitude'], ny_uni["NAME"]):
            folium.CircleMarker(
            [lat, lng],
            radius=2,
            tooltip=name,
            color='blue',
            fill=True,
            weight=7,
            fill_color='black',
            fill_opacity=0.75,
            opacity=0,
            parse_html=False).add_to(m)

    if vue_choisie == 'Daily vision':
        indexx = [str(hour) + "h" for hour in data[valeur_selectionnee].keys()]
    else:  
        indexx = [dow for dow in data[valeur_selectionnee].keys()]


    hm = HeatMapWithTime(data=list(data[valeur_selectionnee].values()),
                        index=indexx, 
                        radius=6,
                        blur=1,
                        auto_play=True,
                        max_speed=3,
                        min_speed=0.5,
                        max_opacity=1,
                        position='bottomright')
    hm.add_to(m)

    folium_static(m)

    st.markdown(f"## Aggregated view of the visits with a {vue_choisie.lower()} :")

    if valeur_selectionnee in data:

        keys = list(data[valeur_selectionnee].keys())  # Assurez-vous que ceci donne les jours/nombres attendus
        frequences = [len(data[valeur_selectionnee][key]) for key in keys]  # Utilisez la valeur directement
        #print(frequences)
        total_check_ins = sum(frequences)
        
        if total_check_ins > 0:
            frequences = [freq / total_check_ins for freq in frequences]

        plt.figure(figsize=(10, 6))
        plt.bar(range(len(frequences)), frequences, color='skyblue')
        
        if vue_choisie == 'Daily vision':
            plt.xlabel('Hour of the day')
        else:  # 'Weekly vision'
            plt.xlabel('Day of the week')
        
        plt.ylabel('Visits frequency (en %)')
        plt.title(f'Fisits frequency over time for {valeur_selectionnee}')
        plt.xticks(range(len(frequences)), keys, rotation=45)
        
        plt.gca().set_yticklabels(['{:.0f}%'.format(y*100) for y in plt.gca().get_yticks()])
        
        plt.tight_layout()
        st.pyplot(plt)

    st.markdown(f"{text_analysis[valeur_selectionnee][vue_choisie]}", unsafe_allow_html=True)

elif analysis == 'Geographical analysis':

    m, nybb, data, ny_uni = load_data_geo()

    elements = ['School', 'Restaurant', 'Shopping', 'Night Club']
    valeur_selectionnee = st.sidebar.radio("Select the establishement type", elements)

    data_selected = data[["ntaname", "geometry", valeur_selectionnee]]

    folium.Choropleth(
        geo_data=data_selected,
        name='choropleth',
        data=data_selected,
        columns=['ntaname', valeur_selectionnee],
        key_on='feature.properties.ntaname',
        fill_color='plasma_r',  # Utiliser un dégradé de couleur de jaune à bleu
        fill_opacity=0.7,
        line_opacity=0.4,
        legend_name=f'Number of {valeur_selectionnee.lower()} check-ins by neighborhood.',
        bins=50,
        highlight=True,
        tooltip=folium.features.GeoJsonTooltip(
        fields=['ntaname',valeur_selectionnee],
        aliases=['ntaname',valeur_selectionnee],
        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;") 
    )
    ).add_to(m)

    feature = folium.features.GeoJson(
                data=data_selected,
                name='North Carolina',
                smooth_factor=2,
                style_function=lambda x: {'color':'black','fillColor':'transparent','weight':0.5},
                tooltip=folium.features.GeoJsonTooltip(
                    fields=['ntaname',
                            valeur_selectionnee],
                    aliases=["NTA :",
                                'Number of check-ins:'], 
                    localize=True,
                    sticky=False,
                    labels=True,
                    style="""
                        background-color: #F0EFEF;
                        border: 2px solid black;
                        border-radius: 3px;
                        box-shadow: 3px;
                    """,
                    max_width=800,),
                        highlight_function=lambda x: {'weight':3,'fillColor':'grey'},
                    ).add_to(m)    

    if valeur_selectionnee == "School":

        for lat, lng, name in zip(ny_uni['Latitude'], ny_uni['Longitude'], ny_uni["NAME"]):
            folium.CircleMarker(
            [lat, lng],
            radius=3,
            tooltip=name,
            color='blue',
            fill=True,
            weight=7,
            fill_color='black',
            fill_opacity=0.75,
            opacity=0,
            parse_html=False).add_to(m)

    folium_static(m)