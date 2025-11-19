import requests
import os
from math import radians, sin, cos, atan2, sqrt
from enum import Enum
from plot import plot_total, plot_pm25_avgerage
from constants import record_time_key, BASE_DIR

# how to exe: airBox.py <address>  <Number(random)>

MINISTRY_OF_ENVIRONMENT_API_KEY = os.environ.get('MOE_API_KEY')
MOE_API_BASE_URL = 'https://data.moenv.gov.tw/api/v2'

# Google API 取得經緯度
def geocoding(address):
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    geocoding_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={google_api_key}'
    response = requests.get(geocoding_url)

    # # Uncomment this section to understand the geocode response
    # with open(f'{BASE_DIR}/geocode.json', 'w') as f:
    #     f.write(response.text)
    
    json_data = response.json()
    location = json_data['results'][0]['geometry']['location']
    latlon = [location['lat'], location['lng']]
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
            min_distance = distance_to_station
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
                    record_time_key: record['datacreationdate']
                }
                station_records.append(filtered_record)
                if len(station_records) == target_amount:
                    break
        offset += 1000
    
    # # Uncomment this section to view the pollution api response 
    # pm25_filename = f"{BASE_DIR}/pm25_station_{station['siteid']}.txt"
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
                    record_time_key: record['monitordate']
                }
                additional_data_records.append(filtered_record)
                if len(additional_data_records) == target_amount:
                    break
        offset += 1000
    
    # # Uncomment this section to view the additional data api response 
    # additional_data_filename = f"{BASE_DIR}/{data_name.value}_station_{station['siteid']}.txt"
    # with open(additional_data_filename, "w") as f:
    #     for record in additional_data_records:
    #         f.write(f"{record}\n") 
    
    return additional_data_records

def get_temperature_from_station(days, station):
        return get_additional_data_from_station(days, station, AdditionalData.temperature)

def get_humidity_from_station(days, station):
        return get_additional_data_from_station(days, station, AdditionalData.humidity)

def run(data):
    address_latlon = geocoding(data.address)
    air_quality_stations = get_air_quality_stations()
    nearest_station = get_nearest_station_from_latlon(address_latlon, air_quality_stations)
    past_days = 7
    pollution = get_pollution_from_station(past_days, nearest_station)
    temperature_records = get_temperature_from_station(past_days, nearest_station)
    humidity_records = get_humidity_from_station(past_days, nearest_station)
    plot_total(pollution, temperature_records, humidity_records)
    plot_pm25_avgerage(pollution)
    return f"地址: {data.address}~緯度: {address_latlon[0]}~經度: {address_latlon[1]}~~APP: TODO~區域: {nearest_station['areaname']}~名稱: {nearest_station['sitename']} / TODO~裝置 ID: {nearest_station['siteid']}~緯度: {nearest_station['twd97lat']}~經度: {nearest_station['twd97lon']}"
