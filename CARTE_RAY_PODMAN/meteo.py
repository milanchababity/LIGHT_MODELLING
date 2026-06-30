import requests, json, os, datetime
import main

METEO_URL = "https://archive-api.open-meteo.com/v1/archive?latitude={0}&longitude={1}&start_date={2}&end_date={3}&hourly=diffuse_radiation,direct_radiation"

def format_meteo_data(data):
    # returns a [day][hour][direct radiation / diffuse radiation] table
    clean_data = []
    daily_results = []
    for i in range(0, len(data["hourly"]["time"])):
        if i > 0 and i % 24 == 0:
            clean_data.append(daily_results)
            daily_results = []
        daily_results.append([data["hourly"]["direct_radiation"][i], data["hourly"]["diffuse_radiation"][i]])
    clean_data.append(daily_results)
    return clean_data

def get_station_infos(content):
    return { "latitude": content["latitude"], "longitude": content["longitude"] }

def compute_day_of_years(start_date, end_date):
    day_of_years = []
    date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    while (date.strftime("%Y-%m-%d") <= end_date):
        doy = date.timetuple().tm_yday,
        day_of_years.append(doy[0])
        date += datetime.timedelta(days=1)
    return day_of_years

def read_meteo(filename, args):
    start_date = args["date_start_crop"][0:10]
    end_date = args["date_end_crop"][0:10]
    day_of_years = compute_day_of_years(start_date, end_date)
    data = None
    station_infos = None
    is_create = False
    if not os.path.isfile(filename):
        is_create = True
    else:
        with open(filename) as f:
            content = json.load(f)
        data = format_meteo_data(content)
        station_infos = get_station_infos(content)
        if len(data) != len(day_of_years): # wrong number of days in meteo file
            is_create = True
    if is_create: # Create file if not found or data size is not as expected
        data, station_infos = create_meteo_file(args["latitude"], args["longitude"], start_date, end_date, len(day_of_years), filename)
    else:
        main.log("Reading weather data from {0} file".format(os.path.basename(filename)))
    return (day_of_years, data, station_infos)

def create_meteo_file(lat, lon, start_date, end_date, duration, meteo_file):
    url = METEO_URL.format(lat, lon, start_date, end_date)
    response = requests.get(url)
    if response.status_code != 200:
        main.error("API returned error code {0}".format(response.status_code))
    content = response.json()
    # check for missing data
    if len(content["hourly"]["time"]) != 24 * duration or len(content["hourly"]["direct_radiation"]) != 24 * duration or len(content["hourly"]["diffuse_radiation"]) != 24 * duration:
        main.error("Open-meteo API returned incomplete weather data. Aborting simulation.")
    # Save to file
    out_file = open(meteo_file, "w")
    json.dump(content, out_file, indent = 6)
    out_file.close()
    return (format_meteo_data(content), get_station_infos(content))