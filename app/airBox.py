import warnings
warnings.filterwarnings("ignore")
import ssl
import json 
import pandas as pd
import matplotlib.pyplot  as plt
import matplotlib.gridspec as gridspec
from datetime import time
from urllib import request
import requests
from bs4 import BeautifulSoup
import os
from math import radians, sin, cos, atan2, sqrt
from enum import Enum
from warnings import simplefilter
simplefilter(action='ignore')

# how to exe: airBox.py <address>  <Number(random)>

MINISTRY_OF_ENVIRONMENT_API_KEY = os.environ.get('MOE_API_KEY')
MOE_API_BASE_URL = 'https://data.moenv.gov.tw/api/v2'

# Google API 取得經緯度
def geocoding(place):
    api_key = os.environ.get("GOOGLE_API_KEY")
    url = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}".format(place, api_key)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.prettify()

    json_data = json.loads(text)

    # Convert single quotes to double quotes
    result_raw = str(json_data)
    result_fix = result_raw.replace("'", '"')
    json_data = json.loads(result_fix)

    # # output geocode response to file for debugging
    # geocode_filename = f"geocode_{place.replace(' ', '_')}.json"
    # with open(geocode_filename, "w") as f:
    #     f.write(result_fix)

    latlon = json_data['results'][0]['geometry']['location']
    latlon = list(latlon.values())
    return latlon

def get_air_quality_stations():
    air_quality_stations_api_url = f'{MOE_API_BASE_URL}/aqx_p_07?api_key={MINISTRY_OF_ENVIRONMENT_API_KEY}'
    response = requests.get(air_quality_stations_api_url)
    json_data = response.json()

    # # Uncomment this section to understand the metadata of the stations api response
    # station_metadata = json_data['fields']
    # print(station_metadata)

    air_quality_stations = json_data['records']
    return air_quality_stations

def haversine_distance(lat1, lon1, lat2, lon2):
    # Earth radius in kilometers (use 6371 for km, 3958.8 for miles)
    R = 6371  

    # Convert degrees to radians
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Differences
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def get_nearest_station_from_latlon(latlon, air_quality_stations):
    """
    Find the nearest air quality monitoring station to a given latitude/longitude.
    
    Parameters
    ----------
    latlon : list[float]
        A list containing `[latitude, longitude]` representing the target location.
        Must have exactly two elements.
    air_quality_stations : list[dict]
        A list of station objects. Each station dict must contain:
        - 'twd97lon' : str or float — station longitude
        - 'twd97lat' : str or float — station latitude

    Returns
    -------
    dict
        The station dictionary representing the closest station to the given coordinates.
    """

    min_distance = float('inf')
    closest_station = None
    for station in air_quality_stations:
        station_latitude = float(station['twd97lat'])
        station_longitude = float(station['twd97lon'])
        distance_to_station = haversine_distance(latlon[0], latlon[1], station_latitude, station_longitude)
        if distance_to_station < min_distance:
            closest_station = station
    return closest_station


def get_pollution_from_station(days, station):
    station_records = []
    offset = 0
    records_per_day = 24
    target_amount = records_per_day * days
    while len(station_records) < target_amount:
        particulate_matter_api_url = f'{MOE_API_BASE_URL}/aqx_p_488?api_key={MINISTRY_OF_ENVIRONMENT_API_KEY}&offset={offset}'
        response = requests.get(particulate_matter_api_url)
        json_data = response.json()
        records = json_data['records']
        for record in records:
            if record['siteid'] == station['siteid']:
                filtered_record = {
                    'county': record['county'],
                    'sitename': record['sitename'],
                    'siteid': record['siteid'],
                    'pm2.5': record['pm2.5_conc'],
                    'record_time': record['datacreationdate']
                }
                station_records.append(filtered_record)
                if len(station_records) == target_amount:
                    break
        offset += 1000
    
    # # Uncomment this section to view the pollution api response 
    # pm25_filename = f"pm25_station_{station['siteid']}.txt"
    # with open(pm25_filename, "w") as f:
    #     for record in station_records:
    #         f.write(f"{record}\n") 
    
    return station_records

class AdditionalData(Enum):
    temperature = 'temperature'
    humidity = 'humidity'

def get_additional_data_from_station(days, station, data_name):
    field_english_name = ''
    if data_name == AdditionalData.temperature:
        field_english_name = 'AMB_TEMP'
    elif data_name == AdditionalData.humidity:
        field_english_name = 'RH'

    additional_data_records = []
    offset = 0
    records_per_day = 24
    target_amount = records_per_day * days
    while len(additional_data_records) < target_amount:
        particulate_matter_api_url = f'{MOE_API_BASE_URL}/aqx_p_35?api_key={MINISTRY_OF_ENVIRONMENT_API_KEY}&offset={offset}'
        response = requests.get(particulate_matter_api_url)
        json_data = response.json()
        records = json_data['records']
        for record in records:
            if record['siteid'] == station['siteid'] and record['itemengname'] == field_english_name:
                filtered_record = {
                    'county': record['county'],
                    'sitename': record['sitename'],
                    'siteid': record['siteid'],
                    data_name.value: record['concentration'],
                    'record_time': record['monitordate']
                }
                additional_data_records.append(filtered_record)
                if len(additional_data_records) == target_amount:
                    break
        offset += 1000
    
    # # Uncomment this section to view the additional data api response 
    # additional_data_filename = f"{data_name.value}_station_{station['siteid']}.txt"
    # with open(additional_data_filename, "w") as f:
    #     for record in additional_data_records:
    #         f.write(f"{record}\n") 
    
    return additional_data_records

def get_temperature_from_station(days, station):
        return get_additional_data_from_station(days, station, AdditionalData.temperature)

def get_humidity_from_station(days, station):
        return get_additional_data_from_station(days, station, AdditionalData.humidity)

def plot_total( pol_df ):
    quality = ['great','normal','notWell','bad','danger']
    pm25_standard = [0, 15, 35, 55, 250]
    fig = plt.figure(figsize=(18, 6))
    gs = gridspec.GridSpec(18, 2, figure=fig)

    # Get date of 7 days, and use it to set x label of plot.
    dates = pol_df.index.to_series()
    dates = dates[dates.dt.time == time(0, 0, 0)]

    # PM2.5 
    ax = fig.add_subplot(gs[:8, :])
    ax.plot(pol_df['s_d0'], color="royalblue")
    ax.plot(pol_df.loc[dates.index, "s_d0"], "o")
    ax.set_title("PM2.5", loc="left", fontsize=14, pad=10)

    colors = ['lime','gold','orangered','red','darkviolet']
    for st, color in zip(pm25_standard, colors):
        if st == 0:
            ax.fill_between(pol_df.index, st, pol_df['s_d0'], color=color)
        else:
            ax.fill_between(pol_df.index, st, pol_df['s_d0'], where=pol_df['s_d0']>st, color=color, interpolate=True)
            if pol_df['s_d0'].max() > st:
                ax.axhline(y=st, color='black', linestyle='--')

    # Temperature
    ax1 = fig.add_subplot(gs[11:, 0])
    ax1.tick_params(rotation=20, axis='x')
    ax1.plot(pol_df['s_t0'], color="royalblue")
    ax1.plot(pol_df.loc[dates.index, "s_t0"], "o")
    ax1.set_title('Temperature', loc="left", fontsize=14, pad=10)

    tmp = ax1.get_yticks()
    ax1.fill_between(pol_df.index, pol_df['s_t0'], color='orange', alpha=0.6)
    ax1.set_ylim(min(tmp), max(tmp))

    # Humidity
    ax2 = fig.add_subplot(gs[11:, 1])
    ax2.tick_params(rotation=20, axis='x')
    ax2.plot(pol_df['s_h0'], color="royalblue")
    ax2.plot(pol_df.loc[dates.index, "s_h0"], "o")
    ax2.set_title('Humidity', loc="left", fontsize=14, pad=10)

    tmp = ax2.get_yticks()
    ax2.fill_between(pol_df.index, pol_df['s_h0'], color='lightseagreen', alpha=0.6)
    ax2.set_ylim(min(tmp), max(tmp))

    plt.savefig( 'fig_one.jpg', bbox_inches='tight' )
    plt.close()


def plot_avg( pol_df ):
    # 七天中各小時平均值
    cur_hour = pol_df.index[-1].hour
    pm25_standard = [0, 15, 35, 55, 250]
    # Get mean pollution data of 7 days.
    avg_pol_df = pd.DataFrame(columns=pol_df.columns)
    timestamp = pol_df.index.to_series()
    for i in range(24):
        cond = timestamp.dt.time == time(i, 0, 0)
        # Fixed By M123040019: 'append' was removed from pandas 2.0
        #avg_pol_df = avg_pol_df.append(pol_df[cond].mean(), ignore_index=True)
        avg_pol_df = pd.concat([avg_pol_df, pd.DataFrame([pol_df[cond].mean()])], ignore_index=True)



    # Rotate 資料，以目前時間為最後一筆
    dft = avg_pol_df
    data = pd.concat([dft.iloc[cur_hour+1:], dft.iloc[:cur_hour+1]])
    data = data.reset_index(drop=True)

    xt = [i for i in range(24)]
    xts = xt[cur_hour+1:]+xt[:cur_hour+1]

    # Set plot
    plt.figure(figsize=(9, 3))
    plt.plot(data['s_d0'], 'o-', color="royalblue")
    plt.xticks(xt, xts)
    plt.title("PM2.5 (7 days average for each hour in day.)", loc="left", fontsize=14, pad=10)
                
    # Set color
    colors = ['lime','gold','orangered','red','darkviolet']
    for st, color in zip(pm25_standard, colors):
        if st == 0:
            plt.fill_between(list( data.index), st, list(data['s_d0']), color=color)
        else:
            plt.fill_between(list(data.index), st, list(data['s_d0']), where=data['s_d0']>st, color=color, interpolate=True)
            if data['s_d0'].max() > st:
                plt.axhline(y=st, color='black', linestyle='--')            

    plt.savefig( 'fig_two.jpg')


def run(data):
    address_latlon = geocoding(data.address)
    air_quality_stations = get_air_quality_stations()
    nearest_station = get_nearest_station_from_latlon(address_latlon, air_quality_stations)
    past_days = 7
    pollution = get_pollution_from_station(past_days, nearest_station)
    temperature_records = get_temperature_from_station(past_days, nearest_station)
    humidity_records = get_humidity_from_station(past_days, nearest_station)
    # plot_total( pol_df )
    # plot_avg( pol_df )
    # feats = ['app','area','SiteName','name','device_id','gps_lat','gps_lon']
    # detail = all_df.iloc[0][feats]
    # string = f"地址: {data.address}~緯度: {my_latlon[0]}~經度: {my_latlon[1]}~~APP: {detail['app']}~區域: {detail['area']}~名稱: {detail['SiteName']} / {detail['name']}~裝置 ID: {detail['device_id']}~緯度: {detail['gps_lat']}~經度: {detail['gps_lon']}"
    # return string
