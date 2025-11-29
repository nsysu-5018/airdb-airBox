from pathlib import Path
from enum import Enum
import os

BASE_DIR = Path(__file__).resolve().parent

# total plot
total_plot_name = 'total'
total_plot_path = f"{BASE_DIR}/{total_plot_name}.jpg"

# pm2.5 average plot
pm25_average_plot_name = 'pm25_average'
pm25_average_plot_path = f"{BASE_DIR}/{pm25_average_plot_name}.jpg"

# Ministry of Environment API
MINISTRY_OF_ENVIRONMENT_API_KEY = os.environ.get('MOE_API_KEY')
MOE_API_BASE_URL = 'https://data.moenv.gov.tw/api/v2'

record_time_key = 'record_time'
past_days = 7

class AdditionalData(Enum):
    temperature = 'temperature'
    humidity = 'humidity'

# cache
cache_folder = f'{BASE_DIR}/cache'
temperature_folder = f'{cache_folder}/temperature'
humiditiy_folder = f'{cache_folder}/humidity'

station_to_api_endpoint = {
    "1": "aqx_p_189", # 基隆
    "2": "aqx_p_190", # 汐止
    "3": "aqx_p_191", # 萬里 not found from all stations
    "4": "aqx_p_192", # 新店
    "5": "aqx_p_193", # 土城
    "6": "aqx_p_194", # 板橋
    "7": "aqx_p_195", # 新莊
    "8": "aqx_p_196", # 菜寮
    "9": "aqx_p_197", # 林口
    "10": "aqx_p_198", # 淡水
    "11": "aqx_p_199", # 士林
    "12": "aqx_p_200", # 中山
    "13": "aqx_p_201", # 萬華
    "14": "aqx_p_202", # 古亭
    "15": "aqx_p_203", # 松山
    "16": "aqx_p_204", # 大同
    "17": "aqx_p_205", # 桃園
    "18": "aqx_p_206", # 大園
    "19": "aqx_p_207", # 觀音
    "20": "aqx_p_208", # 平鎮
    "21": "aqx_p_209", # 龍潭
    "22": "aqx_p_210", # 湖口
    "23": "aqx_p_211", # 竹東
    "24": "aqx_p_212", # 新竹
    "25": "aqx_p_213", # 頭份
    "26": "aqx_p_214", # 苗栗
    "27": "aqx_p_215", # 三義
    "28": "aqx_p_216", # 豐原
    "29": "aqx_p_217", # 沙鹿
    "30": "aqx_p_218", # 大里
    "31": "aqx_p_219", # 忠明
    "32": "aqx_p_220", # 西屯
    "33": "aqx_p_221", # 彰化
    "34": "aqx_p_222", # 線西
    "35": "aqx_p_223", # 二林
    "36": "aqx_p_224", # 南投
    "37": "aqx_p_225", # 斗六
    "38": "aqx_p_226", # 崙背
    "39": "aqx_p_227", # 新港
    "40": "aqx_p_228", # 朴子
    "41": "aqx_p_229", # 臺西
    "42": "aqx_p_230", # 嘉義
    "43": "aqx_p_231", # 新營
    "44": "aqx_p_232", # 善化
    "45": "aqx_p_233", # 安南
    "46": "aqx_p_234", # 臺南
    "47": "aqx_p_235", # 美濃
    "48": "aqx_p_236", # 橋頭
    "49": "aqx_p_237", # 仁武
    "50": "aqx_p_238", # 鳳山
    "51": "aqx_p_239", # 大寮
    "52": "aqx_p_240", # 林園
    "53": "aqx_p_241", # 楠梓
    "54": "aqx_p_242", # 左營
    "56": "aqx_p_243", # 前金
    "57": "aqx_p_244", # 前鎮
    "58": "aqx_p_245", # 小港
    "59": "aqx_p_246", # 屏東
    "60": "aqx_p_247", # 潮州
    "61": "aqx_p_248", # 恆春
    "62": "aqx_p_249", # 臺東
    "63": "aqx_p_250", # 花蓮
    "64": "aqx_p_251", # 陽明
    "65": "aqx_p_252", # 宜蘭
    "66": "aqx_p_253", # 冬山
    "67": "aqx_p_254", # 三重
    "68": "aqx_p_255", # 中壢
    "69": "aqx_p_256", # 竹山
    "70": "aqx_p_257", # 永和
    "71": "aqx_p_258", # 復興
    "72": "aqx_p_259", # 埔里
    "75": "aqx_p_260", # 馬祖
    "77": "aqx_p_261", # 金門
    "78": "aqx_p_262", # 馬公
    "80": "aqx_p_263", # 關山
    "83": "aqx_p_264", # 麥寮
    "84": "aqx_p_461", # 富貴角
    # "85": "missing", # 大城
    # "139": "missing", # 員林
  }

missing_endpoint_site_ids = ["85", "139"]