# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 15:22:25 2023

@author: tagtyk0616
"""
from datetime import datetime
import tempfile
import os
import pandas as pd
from back_end import (station_info, rain_data, data_processing)
from back_end.api_counter import (InternalServerError,
                                  NetatmoGeneralError, NoActiveTokenError,
                                  NoApiCallsLeftError, InvalidInputError)

RADIUS = 0.25  # How big area to check, in lat/long
STRING_FORMAT = "%Y-%m-%d"


class UserInputData:
    def __init__(self, auth_token, latitude, longitude, date_begin,
                 date_end, scale, station_amount, path):
        self._auth_token = auth_token
        self._latitude = latitude
        self._longitude = longitude
        self._date_begin = date_begin

        self._date_end = date_end
        self._scale = scale
        self._station_amount = station_amount
        self._path = path

        formated_date_begin = datetime.strptime(
            self._date_begin, STRING_FORMAT)
        self._date_begin_unix = datetime.timestamp(formated_date_begin)

        formated_date_end = datetime.strptime(self._date_end, STRING_FORMAT)
        self._date_end_unix = datetime.timestamp(formated_date_end)

    @property
    def auth_token(self):
        return self._auth_token

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    @property
    def date_begin(self):
        return self._date_begin

    @property
    def date_end(self):
        return self._date_end

    @property
    def scale(self):
        return self._scale

    @property
    def station_amount(self):
        return self._station_amount

    @property
    def path(self):
        return self._path

    @property
    def date_begin_unix(self):
        return self._date_begin_unix

    @property
    def date_end_unix(self):
        return self._date_end_unix

    def convert_scale_to_api_format(self):
        scale_convertion = {"30 min": "30min",
                            "1 timme": "1hour",
                            "3 timmar": "3hours",
                            "1 dag": "1day",
                            "1 vecka": "1week",
                            "1 månad": "1month",
                            }

        if self._scale in scale_convertion:
            self._scale = scale_convertion[self._scale]
        else:
            raise InvalidInputError


def run_program(input_data, gui=None):
    """


    Parameters
    ----------
    auth_token : TYPE
        DESCRIPTION.
    input_data : TYPE
        DESCRIPTION.
    gui : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    None.

    """

    name = f"Regnvärden kring ({input_data.latitude}, {input_data.longitude}), " \
        f"{input_data.date_begin} - {input_data.date_end}, upplösning {input_data.scale}, " \
        f"{input_data.station_amount} stationer"
    print("got here?")
    input_data.convert_scale_to_api_format()
    print("got here!")
    latitude_ne, longitude_ne, latitude_sw, longitude_sw = (
        station_info.calculate_corner_coorinates(
            input_data.latitude, input_data.longitude, RADIUS)
    )

    rain_station_list = station_info.get_station_from_coords(
        input_data.auth_token,
        latitude_ne,
        longitude_ne,
        latitude_sw,
        longitude_sw
    )

    relevant_station_list = station_info.quicksort_rain_station_list(
        rain_station_list)[0:input_data.station_amount]

    start_stop_list = rain_data.divide_time(
        input_data.date_begin_unix, input_data.date_end_unix, input_data.scale, gui=gui)

    df1, df2, df3 = data_processing.create_data_views_for_excel(
        input_data,
        relevant_station_list,
        start_stop_list,
        f"({input_data.latitude}, {input_data.longitude})",
        gui=gui
    )
    
    temp_dir = tempfile.mkdtemp()
    # Full path for the Excel file in the temporary directory
    temp_file_path = os.path.join(temp_dir, f"{name}.xlsx")
    
    with pd.ExcelWriter(temp_file_path) as writer:
        df1.to_excel(writer, sheet_name='Allmän vy')
        df2.to_excel(writer, sheet_name="Median", index=False)
        df3.to_excel(writer, sheet_name='Kartfunktion',
                     index=False, header=True)

    if gui is not None:
        gui.event_queue.put(("progress", 100 // (len(rain_station_list) + 1)))
        gui.event_queue.put((
            "message", f"Programmet är klart \n Fil sparad: \n {name}"))

    print(name)
    print(str(name))
    return temp_file_path
