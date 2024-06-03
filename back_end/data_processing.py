# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 11:54:19 2023

@author: tagtyk0616
"""
from datetime import datetime
import numpy as np
import pandas as pd
from tqdm import tqdm
from back_end import rain_data
from back_end.api_counter import (InternalServerError, NoDataInStationError,
                                  NetatmoGeneralError, NoActiveTokenError,
                                  NoApiCallsLeftError, InvalidInputError)
# from api_counter import api_counter
# from api_counter import MaxApiCallReachedError


def quickselect_median(lst):
    """
    Quickselect implementation to find median.

    Parameters
    ----------
    lst : list
        The input lists from which median should be found.

    Raises
    ------
    ValueError
        If empty list or mismatched lengths, raises ValueError.

    Returns
    -------
    name : str
        name of median station.
    median_value : float
        the median value.

    """
    if len(lst[0]) != len(lst[1]):
        raise ValueError(
            "Error in quickselect: Mismatched lengths between names and values")

    if len(lst[1]) == 0:
        raise ValueError("Error int quickselect: Empty list provided")

    if len(lst[1]) % 2 == 1:
        return quickselect(lst, len(lst[1]) // 2)

    lower_median = quickselect(lst, len(lst[1]) // 2 - 1)
    upper_median = quickselect(lst, len(lst[1]) // 2)
    median_value = (float(lower_median[1]) + float(upper_median[1])) / 2
    # name = f"{lower_median[0].get_name()}, {upper_median[0].get_name()}"
    name = (lower_median[0], upper_median[0])
    return name, median_value


def quickselect(lst, k):
    """
    Do recuesive quickselect on list with name and value.

    Parameters
    ----------
    lst : list
        2 dimensional list with name on dimension 0 and values on dimension 1.
    k : int
        Helper variable for quickselect.

    Returns
    -------
    pivots : list
        list of [name, value]

    """
    if len(lst[1]) == 1:
        return [lst[0][0], lst[1][0]]

    pivot_index = len(lst[1]) // 2
    pivot = lst[1][pivot_index]
    lows = [[name, value] for name, value in
            zip(lst[0], lst[1]) if value < pivot]
    highs = [[name, value] for name, value in
             zip(lst[0], lst[1]) if value > pivot]
    pivots = [[name, value] for name, value in
              zip(lst[0], lst[1]) if value == pivot]
    if k < len(lows):
        return quickselect(list(zip(*lows)), k)

    if k < len(lows) + len(pivots):
        if len(pivots) == 1:
            return pivots[0]

        return pivots[k - len(lows)]

    return quickselect(list(zip(*highs)), k - len(lows) - len(pivots))


def convert_to_unix_from_stations(station_data_list):
    """
    Get all unix values from stations and put them in a numpy array.

    Parameters
    ----------
    station_data_list : list
        List of numpy arrays with with dates on dimension 0, data on dimension 1 and
        Unix dates on dimension 2 for input station.

    Raises
    ------
    IndexError
        Error if problem with the shape of station_data_array.

    Returns
    -------
    unix_from_stations : numpy array
        Numpy array containting UNIX date values from input list

    """
    unix_from_stations = []
    try:
        for station_data in station_data_list:
            station_data_array = np.array(station_data)
            if np.any(station_data):
                unix_from_station = station_data_array[2, :]
                unix_from_station = unix_from_station.astype(int)
                unix_from_stations.append(unix_from_station)
            else:
                unix_from_stations.append([])
    except IndexError as exc:
        print(station_data_array)
        raise IndexError from exc

    unix_from_stations = np.array(unix_from_stations, dtype=object)
    return unix_from_stations

def find_what_data_each_time_step(station_data_list, station_list,
                                  unix_from_stations, time_step_list):
    """
    Construct a dictionary with rainstations for each time step with data.

    The function creates a dictionary with time steps as keys and the stations
    that have data for that time step as values. If no value exists for the
    time step it is left blank.

    The function checks 15 minutes to the left and right of the time step value
    in order to account for offset data and adds it to the dictonary.
    TODO: Should it always be 15 minutes here?

    Parameters
    ----------
    station_data_list : numpy array
        A numpy array with dates on dimension 0, data on dimension 1 and
        Unix dates on dimension 2 for input station.
    station_list : list
        List of RainStation objects.
    unix_from_stations : numpy array
        Numpy array containting UNIX date values from input list
    time_step_list : list
        List of unix dates with time steps that is used to check if there
        is data near those values.

    Returns
    -------
    data_dict : dict
        A dictionary with timesteps as keys and corresponding stations as
        values.

    """
    data_dict = {}
    counter = 0
    counter2 = 0
    for time_step in tqdm(time_step_list):
        for i, unix in enumerate(unix_from_stations):
            try:
                j = (np.abs(unix[:] - time_step)).argmin()
                if (np.abs(time_step - int(station_data_list[i][2, j]))) < 449:
                    # 15 min both ways
                    if time_step in data_dict:
                        if np.abs(time_step - int(station_data_list[i][2, j])) != 0:
                            print("Nu blev det fel, 0 förväntades men fick:",
                                  (time_step - int(station_data_list[i][2, j])))
                        data_dict[time_step].append(
                            [station_list[i],
                             float(station_data_list[i][1, j])])
                    else:
                        data_dict[time_step] = \
                            [[station_list[i],
                              float(station_data_list[i][1, j])]]
            except IndexError:
                counter += 1
                continue
            except ValueError:
                counter2 += 1
                continue

    # print("counter 1", counter)
    # print("counter 2", counter2)
    return data_dict

def format_median_data_view(data_dict, reference_coordinate):
    """
    Calculate median value for each time step and create a pandas data frame.

    Parameters
    ----------
    data_dict : dict
        A dictionary with timesteps as keys and corresponding stations as
        values.
    reference_coordinate : str
        String that specifies the reference coordinate, used in header as distance from.

    Returns
    -------
    median_view_df : pandas dataframe
        pandas data frame with median values for each time step.
    """
    median_array = []
    for time_step, values in tqdm(data_dict.items()):
        if values:
            data = data_dict[time_step]
            # Transforming data
            stations = [item[0] for item in data]
            values = [item[1] for item in data]
            transformed_data = [stations, values]

            time_step_station, time_step_median_value = \
                quickselect_median(transformed_data)

            if isinstance(time_step_station, tuple):
                name = [station.get_name()
                        for station in time_step_station]
                distance = [int(1000 * round(station.get_distance(), 3))
                            for station in time_step_station]
            else:
                name = time_step_station.get_name()
                distance = int(
                    1000 * round(time_step_station.get_distance(), 3))

            time_step = datetime.utcfromtimestamp(
                int(time_step)).strftime('%Y-%m-%d %H:%M:%S')
            median_array.append(
                [time_step, time_step_median_value, name, distance])

    median_array = np.array(median_array, dtype=object)

    try:
        print(median_array)
        median_view_df = pd.DataFrame(median_array, columns=[
            "Datum",
            "Medianvärde regn [mm]",
            "Stationsnamn",
            f"Avstånd från punkt {reference_coordinate} [m]"])

    except ValueError as exc:
        raise ValueError("Ingen data kunde hittas vid skapande av datavy. \n"
                         "Detta kan bland annat hända om vald period är"
                         " kortar än valt tidssteg.") from exc

    return median_view_df


def format_standard_data_view(data_dict):
    """
    Format the data with station names as headers and time steps as rows.

    Parameters
    ----------
    data_dict : dict
        A dictionary with timesteps as keys and corresponding stations as
        values.

    Returns
    -------
    standard_view_df : pandas dataframe
        pandas data frame with station names as headers and time steps as rows.
    """
    station_names = list(set(station.get_name() for data in data_dict.values()
                         for station, _ in data))
    data_rows = {station_name: [] for station_name in station_names}
    time_steps = data_dict.keys()

    for station_name in station_names:
        for time_step in time_steps:
            if time_step in data_dict:
                data = data_dict[time_step]

                # Get the rain value for the current station and time step
                rain_value = next(
                    (value for station,
                     value in data if station.get_name() == station_name), '-')
            else:
                # The station doesn't have data for the current time step
                rain_value = '-'
            data_rows[station_name].append(rain_value)

    standard_view_df = pd.DataFrame(data_rows)
    dates = [datetime.utcfromtimestamp(int(time_step)).strftime('%Y-%m-%d %H:%M:%S')
             for time_step in time_steps]
    standard_view_df.index = pd.Index(dates, name="Datum")

    return standard_view_df



def format_data_map_view(input_data, data_dict):
    """
    Format the data with each new row being a new data entry.

    Parameters
    ----------
    data_dict : dict
        A dictionary with timesteps as keys and corresponding stations as
        values.

    Returns
    -------
    map_view_df : pandas dataframe
        pandas data frame with rows being new data entries.
    """
    data_rows = []
    for i, (time_step, values) in tqdm(enumerate(data_dict.items())):

        time_step_utc = datetime.utcfromtimestamp(
            time_step).strftime('%Y-%m-%d %H:%M:%S')

        if i == 0:
            row = {
                'Datum': time_step_utc,
                'Stationsnamn': "Referenspunkt",
                'Latitud': input_data.latitude,
                'Longitud': input_data.longitude,
                'Regnvärde [mm]': 0
            }
            data_rows.append(row)

        if values:
            data = data_dict[time_step]
            for station, rain_value in data:
                row = {
                    'Datum': time_step_utc,
                    'Stationsnamn': station.get_name(),
                    'Latitud': station.get_latitude(),
                    'Longitud': station.get_longitude(),
                    'Regnvärde [mm]': rain_value
                }
                data_rows.append(row)

    map_view_df = pd.DataFrame(data_rows)

    return map_view_df
  

def collect_station_data(input_data, rain_station_list, start_stop_list, gui=None):
    """
    For each station in station list, collect station data and return it.

    Parameters
    ----------
    input_data : UserInputData object
        An object of class UserInputData containing the users input data.
    rain_station_list : list
        List of RainStation objects.
    start_stop_list : list
        List of 2x1 matricies of start, stop value pairs for partitioning data.
    gui : gui object, optional
        A gui object to update gui elements. The default is None.

    Raises
    ------
    NoApiCallsLeftError
        If amount of api calls is exceeded raise error.

    Returns
    -------
    rain_data_list : list
        A list of data from stations in rain_station_list.

    """
    rain_data_list = []
    for i, station in enumerate(rain_station_list):
        if gui is not None:
            gui.event_queue.put((
                "message", f"Hämtar stationsdata: {station.get_name()}"))
            gui.event_queue.put(("progress", np.ceil(
                100 / (len(rain_station_list) + 1))))

        try:
            station_data = rain_data.get_measure(
                input_data,
                station,
                start_stop_list,
                save_calls=True,
                gui=gui
            )

            rain_data_list.append(station_data)

        except NoApiCallsLeftError as exc:
            if i > 0:
                if gui is not None:
                    gui.event_queue.put((
                        "message", "För många förfrågningar till Netatmo,"
                        "sparar fil med redan hämtad data..."))
                return rain_data_list

            raise NoApiCallsLeftError from exc

    return rain_data_list


def create_data_views_for_excel(input_data, rain_station_list, start_stop_list,
                                reference_coordinate, gui=None):
    """
    Create three separate data views of the data using pandas dataframes.

    Parameters
    ----------
    input_data : UserInputData object
        An object of class UserInputData containing the users input data.
    rain_station_list : list
        List of RainStation objects.
    start_stop_list : List
        List of 2x1 matricies of start, stop value pairs for partitioning data.
    reference_coordinate : str
        String that specifies the reference coordinate, used in header.
    gui : gui object, optional
        A gui object to update gui elements. The default is None.

    Returns
    -------
    standard_view_df : pandas dataframe
        Standard data view with names as headers and timesteps as rows.
    median_df : pandas dataframe
        Data frame that shows median values of stations for each timestep.
    map_view_df : pandas dataframe
        Data frame with format for easy manipulation with map function in excel.

    """

    rain_data_list = collect_station_data(
        input_data,
        rain_station_list,
        start_stop_list,
        gui=gui
    )
  
    time_step_list = np.arange(
        start_stop_list[0][0], start_stop_list[-1][1], 900, dtype=int
    )

    rain_station_list = rain_station_list[0:len(rain_data_list)]

    indices_to_delete = []
    for i, value in enumerate(rain_data_list):
        if not np.any(value):
            indices_to_delete.append(i)

    for index in reversed(indices_to_delete):
        del rain_data_list[index]
        del rain_station_list[index]

    # print(rain_data_list)
    unix_from_stations = convert_to_unix_from_stations(rain_data_list)

    data_time_step_dict = find_what_data_each_time_step(
        rain_data_list,
        rain_station_list,
        unix_from_stations,
        time_step_list
    )
    # print(data_time_step_dict)
    if gui is not None:
        gui.event_queue.put(("progress", 100 // (len(rain_station_list) + 1)))
        gui.event_queue.put(("message", "Räknar ut median från stationer"))

    standard_view_df = format_standard_data_view(data_time_step_dict)
    median_df = format_median_data_view(
        data_time_step_dict, reference_coordinate)
    map_view_df = format_data_map_view(input_data, data_time_step_dict)

    return standard_view_df, median_df, map_view_df
