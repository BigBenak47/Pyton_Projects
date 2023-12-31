# -*- coding: utf-8 -*-
"""final projectcsmc.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1B5f2xvlBpWlyXRKJBfAuXtk19Us3xobY
"""

# Commented out IPython magic to ensure Python compatibility.
# written by ben and kris
# Install necessary libraries
!pip install pandas matplotlib beautifulsoup4

# Import libraries
import requests
import pandas as pd
import matplotlib.pyplot as plt
import time
import concurrent.futures
from bs4 import BeautifulSoup
from matplotlib.dates import MonthLocator, DayLocator, DateFormatter

# %matplotlib inline

API_KEY = "ff7eda1d09338981bfdfb3ea71948a2b400f4b33ffc0a8c68f7da613cf05bd85"

def fetch_data(city_month):
    time.sleep(1)  # Introducing a delay
    city, month = city_month
    aq_param = "pm25"
    start_date = f"{month}-01"
    end_date = f"{month}-28" if month.endswith("02") else f"{month}-30"
    params = {
        "city": city,
        "parameter": aq_param,
        "date_from": start_date,
        "date_to": end_date,
        "order_by": "datetime",
        "sort": "asc",
        "limit": 10000,
        "format": "json"
    }
    headers = {"X-API-Key": API_KEY}
    openaq = "https://api.openaq.org/v2/measurements"
    response = requests.get(openaq, params=params, headers=headers)
    if response.status_code == 200:
        return city, response.json().get("results", [])
    else:
        print(f"Error for {city} ({start_date} to {end_date}): {response.status_code}")
        print(response.json())
        return city, []

def _remove(data):
    return [item.strip() for item in data]

def scrape_weather_data(city, month, year):
    base_url = f"https://www.timeanddate.com/weather/usa/{city.lower().replace(' ', '-')}/historic?month={month}&year={year}"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extracting temperature data
    _table = soup.find('table', {'id':'wt-his'})
    if _table:
        _data = [[[i.text for i in c.find_all('th')], *[i.text for i in c.find_all('td')]] for c in _table.find_all('tr')]
        [h1], [h2], *data, _ = _data
        _h2 = _remove(h2)
        weather_data = {tuple(_remove(h1)):[dict(zip(_h2, _remove([a, *i]))) for [[a], *i] in data]}

        # Convert weather data to DataFrame
        df = pd.DataFrame()
        for date, data_list in weather_data.items():
            for data in data_list:
                temp_data = {key: value for key, value in data.items() if key in ['Temp', 'Weather']}
                temp_data['Date'] = date
                df = pd.concat([df, pd.DataFrame([temp_data])], ignore_index=True)

        # Convert 'Temp' column to numeric
        df['Temp'] = df['Temp'].str.extract('(\d+)').astype(int)

        return df
    else:
        print(f"Could not find weather data table for {city} for {month}-{year}")
        return None

def plot_data(city, data, ylabel):
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'].apply(lambda x: x['utc']))
    df.set_index('date', inplace=True)
    fig, ax = plt.subplots()  # Create a new figure and a set of subplots
    df['value'].plot(ax=ax, label=city)  # Plot data on the axes
    ax.legend()
    ax.set_xlabel('Date')
    ax.set_ylabel(ylabel)
    # Set major ticks to the first day of each month
    ax.xaxis.set_major_locator(MonthLocator())
    # Set minor ticks to each day
    ax.xaxis.set_minor_locator(DayLocator())
    # Set major tick labels to the month and year
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
    fig.autofmt_xdate()  # Auto-format the x-axis labels for better readability
    plt.show()  # Display the plot

def main():
    cities = ["Kansas City", "Bakersfield", "Fairbanks", "Honolulu", "Wilmington"]
    months = [f"{year}-{month:02}" for year in [2021, 2022] for month in range(1, 13)]

    city_month_combinations = [(city, month) for city in cities for month in months]

    all_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_data, city_month_combinations)
        for city, data in results:
            if city not in all_data:
                all_data[city] = []
            all_data[city].extend(data)

    # Display scraped weather data
    for city in cities:
        for month in range(1, 13):
            weather_data = scrape_weather_data(city, month, 2021)
            if weather_data is not None:
                # Plot temperature data
                plt.figure()  # Create a new figure
                weather_data['Temp'].plot(label=city)
                plt.legend()
                plt.xlabel('Date')
                plt.ylabel('Temperature (°F)')
                plt.show()  # Display the plot

    # Plot PM2.5 data
    for city, data in all_data.items():
        if data and 'date' in data[0]:
            plot_data(city, data, 'PM2.5 (µg/m³)')
        else:
            print(f"No 'date.utc' column available for {city}")

main()