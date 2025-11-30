import matplotlib.pyplot  as plt
import matplotlib.dates as mdates
from datetime import datetime
from collections import defaultdict
import numpy as np
from constants import record_time_key, pm25_value_key, total_plot_path, pm25_average_plot_path, AdditionalData

def plot_simple_metric(ax, data, value_key, title, fill_color):
    """
    Plot a simple time-series metric with filled area and line.
    
    Args:
        ax: matplotlib axis object
        data: list of dictionaries containing the data
        value_key: key for the value field in data dictionaries
        title: title for the plot
        fill_color: color for the filled area
    """
    times = []
    values = []

    for record in data:
        try:
            time = datetime.strptime(record[record_time_key], '%Y-%m-%d %H:%M')
            value = float(record[value_key])
            times.append(time)
            values.append(value)
        except (TypeError, ValueError) as e:
            continue

    # Sort by time
    sorted_data = sorted(zip(times, values), key=lambda x: x[0])
    times, values = zip(*sorted_data)

    # Plot the filled area
    ax.fill_between(times, values, alpha=0.7, color=fill_color, 
                     edgecolor=fill_color, linewidth=2)

    # Add line on top
    ax.plot(times, values, color='#2183b3', linewidth=2)

    ax.set_title(title, fontsize=14, loc='left')

    # Format x-axis to show dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_ha('center')

def plot_total(pollution_data, temperature_data, humidity_data):
    """
    Generate a composite environmental chart summarizing PM2.5, temperature,
    and humidity trends over time.

    Parameters
    ----------
    pollution_data : list of dict
        Records containing timestamped pollutant values.
    temperature_data : list of dict
        Timestamped temperature records passed to `plot_simple_metric`.
    humidity_data : list of dict
        Timestamped humidity records passed to `plot_simple_metric`.

    Description
    -----------
    The function creates a figure with three subplots:
        • A full-width panel showing PM2.5 concentrations.  
          Data are parsed, sorted by time, and drawn with color-coded
          filled regions corresponding to commonly used health thresholds.
          A reference line highlights specific breakpoints, and the
          metric is plotted as a line on top.
        • A lower-left panel displaying temperature trends using the
          generic `plot_simple_metric` helper.
        • A lower-right panel displaying humidity trends, also using
          `plot_simple_metric`.

    Returns
    -------
    None
        The function saves the plot to a local file and does not return a value.
    """

    fig = plt.figure(figsize=(18, 6))
        # --- AXES LAYOUT ---
    ax1 = fig.add_subplot(2, 1, 1)       # full-width top row
    ax2 = fig.add_subplot(2, 2, 3)       # bottom-left
    ax3 = fig.add_subplot(2, 2, 4)

    ###    pm2.5
    # Parse the data
    times = []
    pm25_values = []

    for record in pollution_data:
        try:
            time = datetime.strptime(record[record_time_key], '%Y-%m-%d %H:%M')
            pm25 = float(record[pm25_value_key])
            times.append(time)
            pm25_values.append(pm25)
        except (TypeError, ValueError) as e:
            continue

    # Sort by time
    sorted_data = sorted(zip(times, pm25_values))
    times, pm25_values = zip(*sorted_data)

    # Fill areas based on PM2.5 levels (Taiwan AQI standards)
    # Good: 0-15.4 (green)
    # Moderate: 15.5-35.4 (yellow)
    # Unhealthy for Sensitive: 35.5-54.4 (orange)
    # Unhealthy: 54.5+ (red)

    ax1.fill_between(times, 0, pm25_values, 
                    color='#00ff01', alpha=0.8, interpolate=True)

    ax1.fill_between(times, 15, pm25_values,
                    where=[v > 15 for v in pm25_values],
                    color='#fed700', alpha=1, interpolate=True)

    ax1.fill_between(times, 35, pm25_values,
                    where=[v > 35 for v in pm25_values],
                    color='#ff9835', alpha=1, interpolate=True)

    ax1.fill_between(times, 55, pm25_values,
                    where=[v > 55 for v in pm25_values],
                    color='#ca0034', alpha=1, interpolate=True)

    # Plot the line
    ax1.plot(times, pm25_values, color='darkblue', linewidth=1.5)

    # Add reference lines
    ax1.axhline(y=15, color='black', linestyle='--', linewidth=1)
    ax1.axhline(y=35, color='black', linestyle='--', linewidth=1)

    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.DayLocator())
    plt.xticks(rotation=0)

    # Labels and title
    ax1.set_title('PM2.5', fontsize=12, loc='left')
    ax1.set_ylim(0, max(pm25_values) * 1.1)

    ## Temperature
    plot_simple_metric(ax2, temperature_data, AdditionalData.temperature.data_value_key,
                       AdditionalData.temperature.plot_title, '#ffc866')

    ### Humidity
    plot_simple_metric(ax3, humidity_data, AdditionalData.humidity.data_value_key, 
                       AdditionalData.humidity.plot_title, '#7acfce')

    plt.tight_layout()
    plt.savefig(total_plot_path, bbox_inches='tight', dpi=300)
    plt.close()

def plot_pm25_avgerage(pollution_data):
    """
    Generate and save a 24-hour PM2.5 average plot based on a 7-day dataset.

    This function processes a list of pollution records, groups the
    measurements by hour across all days, computes hourly averages, and produces
    a line plot with shaded regions indicating values below or above a fixed
    threshold. A green fill highlights values up to the threshold, while a yellow
    fill marks segments exceeding it.

    Parameters
    ----------
    pollution_data : list of dict
        Records containing timestamped pollutant values.

    Returns
    -------
    None
        The function saves the PM2.5 hourly-average plot to a local file and does not return a value.

    Notes
    -----
    • Invalid or unparsable records are silently skipped.
    """

    # Group PM2.5 values by hour
    hourly_data = defaultdict(list)

    for record in pollution_data:
        try:
            # Parse the record_time to extract the hour
            dt = datetime.strptime(record['record_time'], '%Y-%m-%d %H:%M')
            hour = dt.hour
            pm25_value = float(record[pm25_value_key])
            hourly_data[hour].append(pm25_value)
        except (ValueError, TypeError):
            continue

    # Calculate average for each hour
    hours = list(range(24))
    averages = []

    for hour in hours:
        if hour in hourly_data and hourly_data[hour]:
            avg = np.mean(hourly_data[hour])
            averages.append(avg)
        else:
            averages.append(np.nan)

    # Create the plot
    fig = plt.figure(figsize=(9, 3))
    ax = fig.add_subplot(1, 1, 1)

    # Reorder hours to start from 14 (2 PM) like in the image
    hour_labels = list(range(14, 24)) + list(range(0, 14))
    reordered_averages = averages[14:] + averages[:14]

    # Plot the line with markers
    ax.plot(range(24), reordered_averages, 'o-', color='blue', linewidth=2, markersize=6)

    # Fill areas smoothly following the line
    threshold = 15
    x_values = np.array(range(24))
    y_values = np.array(reordered_averages)

    # Fill green area (from 0 to min of threshold or actual value)
    ax.fill_between(x_values, 0, np.minimum(y_values, threshold), 
                    color='lime', alpha=1.0)

    # Fill yellow area (from threshold to actual value, where value > threshold)
    ax.fill_between(x_values, threshold, y_values, 
                    where=(y_values > threshold), 
                    color='gold', alpha=1.0, interpolate=True)

    # Add threshold line
    ax.axhline(y=threshold, color='black', linestyle='--', linewidth=1.5)

    # Customize the plot
    ax.set_xlim(-0.5, 23.5)
    ax.set_ylim(0, max(reordered_averages) * 1.1)
    ax.set_xticks(range(24))
    ax.set_xticklabels(hour_labels)
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('PM2.5 (7 days average for each hour in day.)', fontsize=12)
    ax.grid(False)
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)

    plt.tight_layout()
    plt.savefig(pm25_average_plot_path, dpi=300)
    plt.close()