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
from warnings import simplefilter
simplefilter(action='ignore')

# how to exe: airBox.py <address>  <Number(random)>

# Google API 取得經緯度
def geocoding(place):
    api_key = "REMOVED"
    url = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}".format(place, api_key)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.prettify()

    json_data = json.loads(text)
    #print(json_data)
    latlon = json_data['results'][0]['geometry']['location']
    latlon = list(latlon.values())
    return latlon

def get_all_device_detail():
    ssl._create_default_https_context = ssl._create_unverified_context

    url = 'https://pm25.lass-net.org/API-1.0.0/project/airbox/latest/'
    json_data = request.urlopen(url).read().decode("utf-8")
    json_data = json.loads(json_data)
    
    df = pd.DataFrame.from_dict(json_data["feeds"])
    
    pol = ['s_d0','s_d1','s_d2','s_h0','s_t0','c_d0','c_d0_method']
    cols = ['date','time','area','device_id','name','SiteName','gps_lat','gps_lon','gps_alt','gps_fix','gps_num']
    df = df[cols]
    
    mask = (df['area']=="NA")|(df['area'].isna())
    df = df[~mask]
    df = df.sort_values(["area","gps_lat","gps_lon","device_id"])        
    df = df.reset_index(drop=True)
    return df

# Calculate distances between all devices and specified latlon, and get the nearest airbox device's id.
def get_nearest_deviceID_from_latlon(latlon, devices_df):
    distance = (((devices_df['gps_lat'] - latlon[0]).abs()**2) +
                ((devices_df['gps_lon'] - latlon[1]).abs()**2) )**0.5
    
    nearest_idx = distance.sort_values().iloc[:3].index
    device_id = devices_df.loc[nearest_idx[0], "device_id"]
    return device_id

def get_7days_pollution_from_deviceID(device_id):
    # PM2.5 Lass-net open API
    ssl._create_default_https_context = ssl._create_unverified_context

    url = 'https://pm25.lass-net.org/API-1.0.0/device/'+device_id+'/history/'
    json_data = request.urlopen(url).read().decode("utf-8")
    json_data = json.loads(json_data)

    # Parse json
    terms = json_data["feeds"][0]['AirBox']
    data = [items[1] for term in terms for items in term.items()]

    # Transfer datatype of time to timestamp, and adjust time zone
    df = pd.DataFrame.from_dict(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%dT%H:%M:%SZ")
    df['timestamp'] = df['timestamp']+pd.Timedelta("08:00:00")
    df['timestamp']
    
    all_df = df
    # Get specified columns
    # s_d0=PM2.5, s_d1=PM10, s_d2=PM1, s_h0=humidity, s_t0=temperature
    feats = ['timestamp', 's_d0', 's_d1', 's_d2', 's_h0', 's_t0',]
    df = df[feats]
    
    # Average pollution data in hours
    df.index = df['timestamp']
    df = df.resample("H").mean() 
    
    return df, all_df

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
        avg_pol_df = pd.concat([avg_pol_df, pol_df[cond].mean()], ignore_index=True)



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
    my_latlon = geocoding( data.address )
    devices_df = get_all_device_detail()
    device_ID = get_nearest_deviceID_from_latlon(my_latlon, devices_df)
    pol_df, all_df = get_7days_pollution_from_deviceID( device_ID )
    plot_total( pol_df )
    plot_avg( pol_df )
    feats = ['app','area','SiteName','name','device_id','gps_lat','gps_lon']
    detail = all_df.iloc[0][feats]
    string = f"地址: {data.address}~緯度: {my_latlon[0]}~經度: {my_latlon[1]}~~APP: {detail['app']}~區域: {detail['area']}~名稱: {detail['SiteName']} / {detail['name']}~裝置 ID: {detail['device_id']}~緯度: {detail['gps_lat']}~經度: {detail['gps_lon']}"
    print( string )
