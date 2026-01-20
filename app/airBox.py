import requests
import os
from math import radians, sin, cos, atan2, sqrt
from fastapi import HTTPException
import json
import logging
from plot import plot_total, plot_pm25_avgerage
from constants import record_time_key, pm25_value_key, past_days, records_per_day, BASE_DIR, station_to_api_endpoint, missing_endpoint_site_ids, MOE_API_BASE_URL, MOE_API_KEY, AdditionalData
from additional import load_additional_data

logger = logging.getLogger("uvicorn")

def geocoding(address):
    """
    Retrieve geographic coordinates for a given address using the Google Geocoding API.

    Parameters
    ----------
    address : str
        The address to be converted into latitude and longitude.

    Returns
    -------
    list[float]
        A list containing two floating-point numbers: [latitude, longitude].

    Raises
    ------
    HTTPException
        If the API returns no results for the provided address, indicating that
        the address could not be resolved.
    """
    logger.info(f"airbox - getting latitude and longtitude for {address}")
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    geocoding_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={google_api_key}'
    response = requests.get(geocoding_url)

    # # Uncomment this section to understand the geocode response
    # with open(f'{BASE_DIR}/geocode.json', 'w') as f:
    #     f.write(response.text)
    
    json_data = response.json()
    results = json_data['results']
    if len(results) == 0:
        raise HTTPException(status_code=400, detail='Invalid address')
    location = results[0]['geometry']['location']
    latlon = [location['lat'], location['lng']]
    return latlon

def get_air_quality_stations():
    logger.info("airbox - getting air quality stations")
    air_quality_stations_api_url = f'{MOE_API_BASE_URL}/aqx_p_07?api_key={MOE_API_KEY}'
    response = requests.get(air_quality_stations_api_url)
    air_quality_stations = response.json()

    # # Uncomment this section to understand response of the stations api
    # with open(f'{BASE_DIR}/all_stations.json', 'w', encoding='utf8') as f:
    #     json.dump(air_quality_stations, f, indent=2, ensure_ascii=False)
       
    filtered_air_quality_stations = [station for station in air_quality_stations if station['siteid'] not in missing_endpoint_site_ids]
    return filtered_air_quality_stations

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
    """
    Retrieve PM2.5 pollution records for a specific monitoring station over a given
    number of days.

    This function queries the Ministry of Environment API in batches and extracts
    hourly PM2.5 measurements for the requested station. It continues fetching data
    until it has collected the expected number of records.

    Parameters
    ----------
    days : int
        Number of days of PM2.5 data to retrieve.
    station : dict
        Dictionary describing the monitoring station.

    Returns
    -------
    list of dict
        A list of records, each containing:
        - 'county': The county of the monitoring station.
        - 'sitename': Human-readable station name.
        - 'siteid': Station identifier.
        - pm25_value_key: PM2.5 concentration value.
        - record_time_key: Timestamp associated with the measurement.
    """

    logger.info("airbox - getting pollution data")
    station_records = []
    offset = 0
    target_amount = records_per_day * days
    pm25_api_endpoint = station_to_api_endpoint[station['siteid']]
    while len(station_records) < target_amount:
        particulate_matter_api_url = f'{MOE_API_BASE_URL}/{pm25_api_endpoint}?api_key={MOE_API_KEY}&offset={offset}'
        response = requests.get(particulate_matter_api_url)
        records = response.json()
        for record in records:
            if record['itemengname'] == 'PM2.5':
                filtered_record = {
                    'county': record['county'],
                    'sitename': record['sitename'],
                    'siteid': record['siteid'],
                    pm25_value_key: record['concentration'],
                    record_time_key: record['monitordate']
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


def run(data):
    address_latlon = geocoding(data.address)
    air_quality_stations = get_air_quality_stations()
    nearest_station = get_nearest_station_from_latlon(address_latlon, air_quality_stations)
    pollution = get_pollution_from_station(past_days, nearest_station)
    temperature_records, humidity_records = load_additional_data(stationId=nearest_station['siteid'])
    plot_total(pollution, temperature_records, humidity_records)
    plot_pm25_avgerage(pollution)
    return f"地址: {data.address}~緯度: {address_latlon[0]}~經度: {address_latlon[1]}~~空氣品質區:{nearest_station['areaname']}~城市: {nearest_station['county']}~鄉鎮: {nearest_station['township']}~測站名稱: {nearest_station['sitename']}~測站編號: {nearest_station['siteid']}~緯度: {nearest_station['twd97lat']}~經度: {nearest_station['twd97lon']}"
