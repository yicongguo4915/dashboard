import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style("white")
import streamlit as st
import numpy as np
# streamlit run /Users/yicong/Desktop/streamlit/finalproject.py

# Data Cleaning
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
fire['IncidentCount'] = 1


# remove bad data (many record has Fire Extinguished Date earlier than fire start date)
fire.drop(fire[fire['Started'] < '2013-01-01'].index , inplace=True)
fire.drop(fire[fire['Extinguished'] < '2013-01-01'].index , inplace=True)
fire.drop(fire[fire['DayUsed'] < 0 ].index , inplace=True)
# fire.to_csv('out.csv', index=False)

month = fire['month'].unique()
county = list(fire['Counties'].unique())
county.insert(0, "")
month.sort()
county.sort()


incident = ['All Incident', 'Major Incident', 'Non-Major Incident']

st.set_page_config(layout='wide', initial_sidebar_state='auto')
st.title("California Wildfire Analysis")
st.subheader("Incidents and Trends Summary")

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

    optionals = st.beta_expander("Optional Parameters: search by County", False)
    county_selected = optionals.selectbox("Select Dynamic", options=county)
    if county_selected:
        countyselection = fire.loc[fire["Counties"] == county_selected]
        fire = countyselection


firesum = fire.groupby(['ArchiveYear']).sum()
st.dataframe(firesum[['AcresBurned', 'IncidentCount', 'Injuries', 'Fatalities', 'StructuresDamaged', 'StructuresDestroyed']])
year = list(firesum.index)

#create bar plot for average temps by month
fig, ax = plt.subplots(figsize=(10,4))
ax.bar(year, firesum['Major'],label = 'Major Incident', alpha =0.8)
ax.bar(year, firesum['NotMajor'],bottom = firesum['Major'], label = 'Non-Major Incident', alpha =0.8)
ax.ticklabel_format(useOffset=False, style='plain')   # disable scientific notation

ax2 = ax.twinx()
ax2.plot(year, firesum['IncidentCount'],marker = 'o',color = 'red')

ax.set_xlabel("Year", size=14)
ax.set_ylabel("Total acres of land Burned", size=14)
ax2.set_ylabel("Total number of wildfire incidents", size=14, color = 'red')

ax.legend(loc = 'upper left')
# plt.show()
st.pyplot(fig)


st.subheader("Wildfire control & suppression effort")
col1,col2 = st.beta_columns([1,1.15])
# create boxplot to show distribution for wildfire duration
# , width=0, height=0, use_container_width=True
plt.figure(figsize=(5, 5))
with col1:
    sns.boxplot(x = 'ArchiveYear', y= 'DayUsed', data=fire, palette="coolwarm")
    plt.xlabel("Year", size=12)
    plt.ylabel("Lasting Duration (days)", size=12)
    st.pyplot(plt)

# create histogram to show distribution for wildfire duration
with col2:
    fig = sns.displot(data = fire, x= 'DayUsed', palette="coolwarm", hue='ArchiveYear')
    plt.xlabel("Lasting Duration (days)", size=12)
    plt.ylabel("Number of Instances", size=12)
    st.pyplot(fig)


# https://discuss.streamlit.io/t/select-an-item-from-multiselect-on-the-sidebar/1276/2
# https://stackoverflow.com/questions/60412158/how-to-display-code-in-streamlit-based-on-user-answer
# https://stackoverflow.com/questions/45475962/labeling-boxplot-with-median-values
# https://datavizpyr.com/show-mean-mark-on-boxplot-using-seaborn-in-python/
# https://discuss.streamlit.io/t/cannot-change-matplotlib-figure-size/10295/4
