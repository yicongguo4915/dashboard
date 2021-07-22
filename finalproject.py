import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style("white")
import streamlit as st
from PIL import Image
import pydeck as pdk
# streamlit run /Users/yicong/Desktop/streamlit/trash.py

st.set_page_config(layout='wide', initial_sidebar_state='auto')
# Data - Preprocessing
# 1.dropped row with ArcesBurned = blank
# 2. Added two columns which tracks the total arced Acres Burned for major and non-major incident respectively
# 3. Added a new column to calculate number of days it took to extinguish the fire

fire = pd.read_csv("California_Fire_Incidents.csv")
fire.dropna(subset = ["AcresBurned"], inplace=True)
fire.loc[fire['MajorIncident'] == True, 'Major'] = fire['AcresBurned']
fire.loc[fire['MajorIncident'] == False, 'NotMajor'] = fire['AcresBurned']
fire['Started'] = pd.to_datetime(fire.Started)
fire['Extinguished'] = pd.to_datetime(fire.Extinguished)
fire['DayUsed'] = (fire['Extinguished'] - fire['Started']).dt.days
fire['month'] = pd.DatetimeIndex(fire['Started']).month
fire['lat'] = fire['Latitude']
fire['lon'] = fire['Longitude']
fire['IncidentCount'] = 1
fire['Radius'] = fire['AcresBurned']/100

# remove bad data, which are:
# 1.records that have fire Extinguished and start date before 2013
# 2 records with fire Extinguished date earlier than start date
fire.drop(fire[fire['Started'] < '2013-01-01'].index , inplace=True)
fire.drop(fire[fire['Extinguished'] < '2013-01-01'].index , inplace=True)
fire.drop(fire[fire['DayUsed'] < 0 ].index , inplace=True)
# fire.to_csv('out.csv', index=False)

month = fire['month'].unique()
county = list(fire['Counties'].unique())
month.sort()
county.sort()
county.insert(0, "")   # insert empty space into select option (with selectbox user can only select
# 1 county at a time, an empty space option means all the county will be selected, which improves flexibility
incident = ['All Incident', 'Major Incident', 'Non-Major Incident']

# construct user interactive widgets
with st.sidebar:
    month_selected = st.multiselect('Select Month', list(month), default=list(month))
    if month_selected:
        monthselection = fire['month'].isin(month_selected)
        fire = fire[monthselection]

    button = st.radio('Select Incident Type', incident)
    if button == 'All Incident':
        fire = fire
    elif button == 'Major Incident':
        fire = fire[fire['MajorIncident'] == True]
    elif button == 'Non-Major Incident':
        fire = fire[fire['MajorIncident'] == False]

    optionals = st.beta_expander("Optional Filter: search by County", False)
    county_selected = optionals.selectbox("Select County", options=county)
    if county_selected:
        countyselection = fire.loc[fire["Counties"] == county_selected]
        fire = countyselection

def map(data):
    mapdata = data[['lon', 'lat', 'AcresBurned', 'Counties', 'Location', 'Radius']]

    view_state = pdk.ViewState(
        latitude=mapdata["lat"].median(),
        longitude=mapdata["lon"].median(),
        zoom=6,
        pitch=2)

    layer = pdk.Layer(
        "ScatterplotLayer",
        mapdata,
        pickable=True,
        stroked=True,
        filled=True,
        radius_scale=6,
        radius_min_pixels=1,
        radius_max_pixels=100,
        line_width_min_pixels=1,
        get_position='[lon, lat]',
        get_radius = '[Radius]',
        get_fill_color=[255, 140, 0],
        get_line_color=[0, 0, 0],
    )

    r = pdk.Deck(map_style='mapbox://styles/mapbox/light-v9', layers=[layer], initial_view_state=view_state,
                tooltip={"text":  "ArcBurned: {AcresBurned}\n Location: {Location}"})
    r.to_html("scatterplot_layer.html")
    st.pydeck_chart(r)


def remark(data):
    firemedium = list(data.groupby('ArchiveYear')['DayUsed'].median().values)
    firemean = list(data.groupby('ArchiveYear')['DayUsed'].mean().values)
    firemean = [round(num, 1) for num in firemean]
    firecount = list(data.groupby('ArchiveYear')['IncidentCount'].sum().values)

    dict_key= list(data.groupby('ArchiveYear')['DayUsed'].median().index)
    dict_key = [str(x) for x in dict_key]

    dictionary = dict(zip(dict_key, zip(firemedium, firemean, firecount)))

    st.write(f'**The medium and mean wildfire lasting duration:**')
    for x,y in dictionary.items():
        st.write(f' in {x} are **{y[0]}** and **{y[1]}** days respectively, based on **{y[2]}** incidents.')

def summarytable(data):
    firesum = data.groupby(['ArchiveYear']).sum()
    st.dataframe(firesum[['AcresBurned', 'IncidentCount', 'Injuries', 'Fatalities', 'StructuresDamaged', 'StructuresDestroyed']])

def combinationchart(data):
    firesum = data.groupby(['ArchiveYear']).sum()
    year = list(firesum.index)
    fig, ax = plt.subplots(figsize=(10,4))
    ax.bar(year, firesum['Major'],label = 'Major Incident', color = 'mediumblue')
    ax.bar(year, firesum['NotMajor'],bottom = firesum['Major'], label = 'Non-Major Incident', color = 'blueviolet')
    ax.ticklabel_format(useOffset=False, style='plain')   # disable scientific notation

    ax2 = ax.twinx()
    ax2.plot(year, firesum['IncidentCount'],marker = 'o',color = 'coral')

    ax.set_xlabel("Year", size=14)
    ax.set_ylabel("Total Acres Burned", size=14)
    ax2.set_ylabel("Total Incidents", size=14, color = 'coral')

    ax.legend(loc = 'upper left')
    st.pyplot(fig)

# create boxplot to show distribution for wildfire duration
def boxplot(data, figsize=(5,5)):
    plt.figure(figsize=figsize)
    sns.boxplot(x = 'ArchiveYear', y= 'DayUsed', data=data, palette="coolwarm")
    plt.xlabel("Year", size=12)
    plt.ylabel("Lasting Duration (days)", size=12)
    st.pyplot(plt)

# create histogram to show distribution for wildfire duration
def histogram(data, figsize=(5,5)):
    plt.figure(figsize=figsize)
    sns.displot(data = data, y= 'DayUsed', palette="coolwarm", hue='ArchiveYear')
    plt.ylabel("Lasting Duration (days)", size=12)
    plt.xlabel("Number of Instances", size=12)
    st.pyplot(plt)

# main function/ construct user interfaces
def main():
    st.title("California Wildfire Analysis")

    img = Image.open("wildfire.jpeg")
    st.image(img, width=650)

    st.subheader("Incidents and Trends Summary")
    summarytable(fire)
    map(fire)
    combinationchart(fire)

    st.subheader("Wildfire control & suppression effort")
    col1,col2 = st.beta_columns([1,1.15])
    with col1:
        boxplot(fire)
    with col2:
        histogram(fire, figsize=(5,6))

    st.text("")
    st.text("")
    remark(fire)

main()

