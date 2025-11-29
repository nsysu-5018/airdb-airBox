import os
from constants import temperature_folder, humiditiy_folder, past_days, \
    AdditionalData, MOE_API_BASE_URL, MINISTRY_OF_ENVIRONMENT_API_KEY, record_time_key, pm25_api_endpoint_mapping
import logging
import requests
import json
from datetime import datetime, timedelta
import zoneinfo
from collections import defaultdict

logger = logging.getLogger("uvicorn")


def fetch_and_save_additional_data():
    logger.info(f'airbox - fetch and save additional data')

    # create folder for cached data
    os.makedirs(temperature_folder, exist_ok=True)
    os.makedirs(humiditiy_folder, exist_ok=True)

    temperature_data = defaultdict(list)
    temperature_data_amount = 0
    humidity_data = defaultdict(list)
    humidity_data_amount = 0
    offset = 0
    records_per_day = 24
    station_amount = len(pm25_api_endpoint_mapping.keys())
    target_amount_per_station = records_per_day * past_days
    target_amount = target_amount_per_station * station_amount
    # track consecutive empty fetches to prevent infinite loops
    consecutive_empty_fetch = 0
    max_empty_fetch = 3

    # current datetime
    timezone = zoneinfo.ZoneInfo("Asia/Taipei")
    current_datetime = datetime.now(timezone)
    
    while temperature_data_amount < target_amount or humidity_data_amount < target_amount:
        # track counts to detect empty fetches
        initial_temperature_amount = temperature_data_amount
        initial_humidity_amount = humidity_data_amount

        particulate_matter_api_url = f'{MOE_API_BASE_URL}/aqx_p_35?api_key={MINISTRY_OF_ENVIRONMENT_API_KEY}&offset={offset}'
        response = requests.get(particulate_matter_api_url)
        json_data = response.json()
        records = json_data['records']
        for record in records:            
            # check if record time is within past_days 
            record_datetime = datetime.strptime(record['monitordate'], '%Y-%m-%d %H:%M')
            record_datetime = record_datetime.replace(tzinfo=timezone)
            if current_datetime - record_datetime > timedelta(hours =  target_amount_per_station):
                continue

            # extract data
            if record['itemengname'] == 'AMB_TEMP':
                new_record = {
                    'siteid': record['siteid'],
                    'temperature': record['concentration'],
                    record_time_key: record['monitordate']
                }
                temperature_data[record['siteid']].append(new_record)
                temperature_data_amount = temperature_data_amount + 1
            elif record['itemengname'] == 'RH':
                new_record = {
                    'siteid': record['siteid'],
                    'humidity': record['concentration'],
                    record_time_key: record['monitordate']
                }
                humidity_data[record['siteid']].append(new_record)
                humidity_data_amount = humidity_data_amount + 1
        offset += 1000

        # prevent infinite loop
        if len(temperature_data) == initial_temperature_amount or len(humidity_data) == initial_humidity_amount:
            consecutive_empty_fetch = consecutive_empty_fetch + 1
            if consecutive_empty_fetch == max_empty_fetch:
                break
        if offset >= 30000: # safety fallback
            break

    # save to temperature and humitidy data to file based on station ID
    for stationId in temperature_data.keys():
        station_temperature_data = temperature_data[stationId]
        with open(f'{temperature_folder}/station_{stationId}.json', 'w', encoding='utf8') as f:
            json.dump(station_temperature_data, f, indent=2, ensure_ascii=False)
    for stationId in humidity_data.keys():
        station_humidity_data = humidity_data[stationId]
        with open(f'{humiditiy_folder}/station_{stationId}.json', 'w', encoding='utf8') as f:
            json.dump(station_humidity_data, f, indent=2, ensure_ascii=False)

def load_additional_data(stationId:int):
    logger.info(f'airbox - load additional data')
    
    # fetch data if one of the data file is missing
    temperature_data_file = f'{temperature_folder}/station_{stationId}.json'
    humidity_data_file = f'{humiditiy_folder}/station_{stationId}.json'
    if not os.path.exists(temperature_data_file) or not os.path.exists(humidity_data_file):
        fetch_and_save_additional_data()
    
    # read data file
    temperature_data = None
    with open(temperature_data_file, 'r') as f:
        temperature_data = json.load(f)
    humidity_data = None
    with open(humidity_data_file, 'r') as f:
        humidity_data = json.load(f)
    
    return temperature_data, humidity_data
