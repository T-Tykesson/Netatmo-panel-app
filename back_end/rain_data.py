



# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 11:54:07 2023

@author: tagtyk0616
"""

from datetime import datetime
import numpy as np
import requests
from tqdm import tqdm
from back_end.api_counter import api_counter
from back_end.api_counter import (InternalServerError,
                                  NetatmoGeneralError, NoActiveTokenError,
                                  NoApiCallsLeftError, InvalidInputError)

#from backend_handeler import MaxApiCallReachedError


def is_closest_date_in_list(input_list, input_value, mode):
    """
    Check if there is data in input_list for the value in input_value.

    Args
    ----
        input_list: numpy array
            List of dates written in UNIX format on dimention 0
            and list of booleans corresponding to the dates on dimention 1.
        input_value : float or int
            Date written in UNIX format to be compared to an input list of
            time_stamps written in UNIX.
        mode : string
            Has two modes "begining", "ending" to check if the input value
            has true or false counterparts in input_list either based on
            if it is the begingin or the ending of the period.

    Returns
    -------
        A boolean True or False based on if the values closest to input_value
        are True or False.

    """
    arr = np.asarray(input_list[0, :])
    i = (np.abs(arr - input_value)).argmin()

    if mode == "begining":
        if i < len(arr) - 1:
            if input_value < arr[i] \
                    and (input_list[1, i - 1] or input_list[1, i]):
                return True
            if input_value > arr[i] \
                    and (input_list[1, i + 1] or input_list[1, i]):
                return True
            if input_value == arr[i] and input_list[1, i]:
                return True
            return False

        if input_list[1, i]:
            return True
        return False

    if mode == "ending":
        if input_value < arr[i] and input_list[1, i - 1]:
            return True
        if input_value > arr[i] and input_list[1, i]:
            return True
        if input_value == arr[i] and input_list[1, i - 1]:
            return True
        return False

    raise ValueError("No correct mode chosen")


def check_if_rain_data_each_timestep(rain_date_array, time_step_list):
    """
    Create an array with dates and bool values based on data with other timesteps.

    Args
    ----
        rain_date_array: numpy array
            A numpy array with dates on dimention 0, data values on dimention 1
            and dates in UNIX format on dimention 2.
        time_step_list : list
            List of unix dates with time steps that is used to check if there is
            data near those values.

    Returns
    -------
        A numpy array with time steps on dimention 0 and  boolean values on
        dimention 1 corresponding to each time steps. An array that can
        later be used in is_closest_data_in_list function.

    """
    period_exists_list = []

    if len(time_step_list) == 1:
        value_for_time_step_array = np.array(
            [[time_step_list], [True]], dtype=object)
        return value_for_time_step_array

    for time_step in time_step_list:

        exists_in_rain_date_array = any(
            np.abs(time_step - int(time_stamp)) < (30.44 * 24 * 60 * 60)
            for time_stamp in rain_date_array[2, :])
        period_exists_list.append(exists_in_rain_date_array)

    value_for_time_step_array = np.array(
        [time_step_list, period_exists_list], dtype=object)
    return value_for_time_step_array


def divide_time(date_begin, date_end, scale, limit=1024, gui=None):
    """
    Divide time period in equal chunks of 1024 entries based on time interval.

    Args
    ----
        date_begin : float or int
            The start date from where time will be divided, UNIX format.
        date_end : float or int
            The last date from where time will be divided, UNIX format.
        scale : string
            Resolution or the time interval, how big the time step will be.
            Valid inputs are "30min", "1hour", "3hours", "1day", "1week",
            "1month".
        limit : int, optional
            The size of each chunk, standard is 1024 based on the API of
            Netatmo's max resolution. The function has not been adapted to
            values other than 1024.

    Returns
    -------
        A list of 2x1 matricies of calculated start ands stop values to be
        handled by get_data function

    Raises
    ------
        KeyError: Raises an exception if scale is not a valid input
        ValueError: Raises a value error if end date is bigger than start date
        or the same date.
    """
    def update_gui(message):
        if gui is not None:
            gui.event_queue.put(("message", message))
            # gui.progress_window.update_text_box(message)

    start_stop_list = []
    span = date_end - date_begin

    if span < 0:
        update_gui("Fel: Slutdatum senare än startdatum")
        raise ValueError("Slutdatum senare än startdatum")
    if span == 0:
        update_gui("Fel: Samma start och slutdatum")
        raise ValueError("Samma start och slutdatum")

    time_options = {"30min": 1800,
                    "1hour": 3600,
                    "3hours": 3 * 3600,
                    "1day": 86400,
                    "1week": 604800,
                    "1month": 2629743}

    if scale not in time_options:
        raise KeyError("Invalid scale. Expected one of '30min', '1hour',"
                       "'3hours', '1day', '1week', '1month'.")

    time_step = time_options[scale]
    whole_number = int(np.floor(span / (time_step * limit)))
    remainder = span % (time_step * limit)  # (i tid)

    start = date_begin
    for _ in range(whole_number):
        end = start + limit * time_step
        start_stop_list.append([start, end])
        start = end

    if remainder != 0:
        start_stop_list.append([start, date_end])

    return start_stop_list


def get_values_from_individual_station(rain_data, gui=None):
    """
    Get out organized values from a rain_data response from the Netatmo api.

    Args
    ----
        rain_data : dict
            A dictionary containing information created from calling the
            Netatmo api for rain_data.

    Returns
    -------
        A tuple of lists (date_list, rain_value_list, date_list_unix_full)
        where the first list contains date_information formated as strings,
        the second list contains the rain data for the time step,
        the third list contains the same date information but in UNIX format.

    Raises
    ------
        ValueError: Raises value error if encountering an error with Netatmo
        api.
    """
    date_list_unix_full = []
    rain_value_list = []

    def update_gui(message):
        if gui is not None:
            gui.event_queue.put(("message", message))
            # gui.progress_window.update_text_box(message)

    try:
        for item in rain_data["body"]:
            rain_values = np.hstack(item["value"])
            rain_start_value = item["beg_time"]

            if "step_time" in item:
                step_value = item["step_time"]
                date_list_unix = np.arange(
                    rain_start_value,
                    rain_start_value + step_value * len(rain_values),
                    step_value
                )
            else:
                date_list_unix = rain_start_value

            date_list_unix_full.append(date_list_unix)
            rain_value_list.append(rain_values)

        rain_value_list = np.hstack(rain_value_list)
        date_list_unix_full = np.hstack(date_list_unix_full)

    except (KeyError, ValueError) as exc:
        error_message = str(exc)
        if "body" in rain_data and len(rain_data["body"]) == 0:
            error_message = "No data"
            raise KeyError("N/A", error_message) from exc

        if "error" in rain_data:
            error_message = rain_data["error"]
            if error_message == {'code': 500, 'message': 'Internal Server Error'}:
                raise InternalServerError from exc
            if error_message == {'code': 2, 'message': 'Invalid access_token'}:
                raise NoActiveTokenError from exc

            if error_message == {'code': 26, 'message': 'User usage reached'}:
                raise NoApiCallsLeftError from exc

            raise NetatmoGeneralError(rain_data["error"]) from exc

    date_list = np.array(
        [datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
         for ts in date_list_unix_full])

    rain_value_list = np.array(rain_value_list).astype(float)
    date_list_unix_full = np.array(date_list_unix_full).astype(int)

    return date_list, rain_value_list, date_list_unix_full


def get_all_rain_data(input_data, station, scale, start_stop_list,
                      period_exists_list=None, gui=None):
    """


    Parameters
    ----------
    auth_token : TYPE
        DESCRIPTION.
    station_name : TYPE
        DESCRIPTION.
    device_id : TYPE
        DESCRIPTION.
    module_id : TYPE
        DESCRIPTION.
    date_begin : TYPE
        DESCRIPTION.
    date_end : TYPE
        DESCRIPTION.
    scale : TYPE
        DESCRIPTION.
    start_stop_list : TYPE
        DESCRIPTION.
    period_exists_list : TYPE, optional
        DESCRIPTION. The default is None.
    gui : TYPE, optional
        DESCRIPTION. The default is None.

    Raises
    ------
    ValueError
        DESCRIPTION.

    Returns
    -------
    final_data : TYPE
        DESCRIPTION.

    """
    def update_gui(message):
        if gui is not None:
            gui.event_queue.put(("message", message))
            # gui.progress_window.update_text_box(message)

    url_2 = "https://api.netatmo.com/api/getmeasure"
    header = {
        "Authorization": "Bearer " + input_data.auth_token
    }
    limit = 1024
    j = 0
    station_data_array = []
    station_data_array = np.array([], dtype=object)
    interupted_calls = 0
    for date in tqdm(start_stop_list):
        if period_exists_list is not None:
            start_has_values = is_closest_date_in_list(
                period_exists_list, date[0], "begining"
            )
            stop_has_values = is_closest_date_in_list(
                period_exists_list, date[1], "ending"
            )

            if not start_has_values and not stop_has_values:
                interupted_calls += 1
                continue

        params = {"device_id": station.get_device_id(),
                  "module_id": station.get_module_id(),
                  "scale": scale,
                  "type": {"sum_rain"},
                  "date_begin": date[0],
                  "date_end": date[1],
                  "limit": limit,
                  }

        """
        if api_counter.get_count() > 498:
            print("User usage reached")
        """
        response_rain_data = requests.get(
            url_2, headers=header, params=params, timeout=25)
        rain_data = response_rain_data.json()
        # api_counter.increment()

        try:
            date_list, rain_values, date_list_unix_full = \
                get_values_from_individual_station(rain_data)

        except ValueError as exc:
            update_gui(f"{exc}")
            raise ValueError(exc) from exc

        except KeyError as exc:
            print("Warning key error", exc)
            continue

        if j == 0:
            station_data_array = np.array(
                [date_list, rain_values, date_list_unix_full], dtype=object)
        else:
            station_data_array2 = np.array(
                [date_list, rain_values, date_list_unix_full], dtype=object)
            station_data_array = np.hstack(
                (station_data_array, station_data_array2))
        j += 1

    print("Interupted calls:", interupted_calls, "\n")
    return station_data_array


def get_measure(input_data, station, start_stop_list, save_calls=False, gui=None):
    """


    Parameters
    ----------
    auth_token : TYPE
        DESCRIPTION.
    station_name : TYPE
        DESCRIPTION.
    device_id : TYPE
        DESCRIPTION.
    module_id : TYPE
        DESCRIPTION.
    date_begin : TYPE
        DESCRIPTION.
    date_end : TYPE
        DESCRIPTION.
    scale : TYPE
        DESCRIPTION.
    start_stop_list : TYPE
        DESCRIPTION.
    save_calls : TYPE, optional
        DESCRIPTION. The default is False.
    gui : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    station_data : TYPE
        DESCRIPTION.

    """

    if save_calls:

        time_step_month = 2629743

        start_stop_list_month = divide_time(
            input_data.date_begin_unix, input_data.date_end_unix, "1month", gui=gui)

        station_data_month = get_all_rain_data(
            input_data, station, "1month",
            start_stop_list_month, gui=gui
        )
        print("station_data_month", station_data_month)
        time_step_list = np.arange(
            start_stop_list_month[0][0],
            start_stop_list_month[0][1],
            time_step_month, dtype=int
        )

        if station_data_month.size != 0:
            period_exists_list = check_if_rain_data_each_timestep(
                station_data_month, time_step_list
            )
            print("period_exists_list", period_exists_list)
            station_data = get_all_rain_data(
                input_data, station, input_data.scale, start_stop_list,
                period_exists_list=period_exists_list,
                gui=gui
            )
            return station_data
        else:
            return []

    station_data = get_all_rain_data(
        input_data, station, input_data.scale, start_stop_list, gui=gui
    )

    return station_data
