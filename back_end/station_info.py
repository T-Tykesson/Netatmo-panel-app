# -*- coding: utf-8 -*-
"""
Created on Tue Jul 11 15:56:55 2023

@author: tagtyk0616
"""

import requests
import numpy as np
from back_end.api_counter import (InternalServerError,
                                  NetatmoGeneralError, NoActiveTokenError,
                                  NoApiCallsLeftError, InvalidInputError)


class RainStation:
    """
    Represents a rain station.

    Parameters
    ----------
        name : str
            The name of the rain station.
        device_id : str, optional
            The device ID of the rain station.
        module_id : str, optional
            The module ID of the rain station.
        latitude : float, optional
            The latitude coordinate of the rain station.
        longitude : float, optional
            The longitude coordinate of the rain station.

    Attributes
    ----------
        name : str
            The name of the rain station.
        device_id :str
            The device ID of the rain station.
        module_id : str
            The module ID of the rain station.
        latitude : float
            The latitude coordinate of the rain station.
        longitude : float
            The longitude coordinate of the rain station.
        data : list
            A list of data associated with the rain station.
        distance_from : float
            The distance from a reference point.

    Methods
    -------
        update_name(name):
            Updates the name of the rain station.
        update_device_id(device_id):
            Updates the device ID of the rain station.
        update_module_id(module_id):
            Updates the module ID of the rain station.
        update_latitude(latitude):
            Updates the latitude coordinate of the rain station.
        update_longitude(longitude):
            Updates the longitude coordinate of the rain station.
        update_data(data):
            Updates the data associated with the rain station.
        save_distance_from(ref_latitude, ref_longitude):
            Calculates and saves the distance from a reference point.
        get_name():
            Returns the name of the rain station.
        get_device_id():
            Returns the device ID of the rain station.
        get_module_id():
            Returns the module ID of the rain station.
        get_latitude():
            Returns the latitude coordinate of the rain station.
        get_longitude():
            Returns the longitude coordinate of the rain station.
        get_data():
            Returns the data associated with the rain station.
        get_distance():
            Returns the distance from the reference point.
        calculate_distance_from_point(ref_latitude, ref_longitude):
            Calculates the distance from a given point.

    """

    def __init__(self, name, device_id="", module_id="", coordinates=(0, 0)):
        """
        Initialize a RainStation object.

        Parameters
        ----------
            name : str
                The name of the rain station.
            device_id : str, optional
                The device ID of the rain station.
            module_id : str, optional
                The module ID of the rain station.
            coorinates : tuple of float, optional
                Fist value is the latitude coordinate of the rain station.
                Second value is the longitude coordinate of the rain station.

        """
        self.name = name
        self.device_id = device_id
        self.module_id = module_id
        self.latitude = coordinates[0]
        self.longitude = coordinates[1]
        self.data = []
        self.distance_from = None

    def update_name(self, name):
        """
        Update the name of the rain station.

        Parameters
        ----------
            name : str
                The new name of the rain station.

        """
        self.name = name

    def update_device_id(self, device_id):
        """
        Update the device ID of the rain station.

        Parameters
        ----------
            device_id : str
                The new device ID of the rain station.

        """
        self.device_id = device_id

    def update_module_id(self, module_id):
        """
        Update the module ID of the rain station.

        Parameters
        ----------
            module_id : str
                The new module ID of the rain station.

        """
        self.module_id = module_id

    def update_latitude(self, latitude):
        """
        Update the latitude coordinate of the rain station.

        Parameters
        ----------
            latitude : float
                The new latitude coordinate of the rain station.

        """
        self.latitude = latitude

    def update_longitude(self, longitude):
        """
        Update the longitude coordinate of the rain station.

        Parameters
        ----------
            longitude : float
                The new longitude coordinate of the rain station.

        """
        self.longitude = longitude

    def update_data(self, data):
        """
        Update the data associated with the rain station.

        Parameters
        ----------
            data : list
                The new data associated with the rain station.

        """
        self.data = data

    def find_scale_factor_to_km(self, latitude):
        """


        Parameters
        ----------
        latitude : TYPE
            DESCRIPTION.

        Returns
        -------
        latitude_to_km : TYPE
            DESCRIPTION.
        longitude_to_km : TYPE
            DESCRIPTION.

        """
        longitude_to_km = 40075 * np.cos(latitude) / 360
        latitude_to_km = 111.32
        return latitude_to_km, longitude_to_km

    def save_distance_from(self, ref_latitude, ref_longitude):
        """
        Calculate and save the distance from a reference point.

        Parameters
        ----------
            ref_latitude : float
                The latitude coordinate of the reference point.
            ref_longitude : float
                The longitude coordinate of the reference point.

        """
        mid_latitude = (self.latitude + ref_latitude)/2
        latidue_to_km, longitude_to_km = self.find_scale_factor_to_km(
            mid_latitude)

        self.distance_from = np.sqrt((latidue_to_km*(self.latitude - ref_latitude))**2 +
                                     (longitude_to_km*(self.longitude - ref_longitude))**2)

    def get_name(self):
        """
        Get the name of the rain station.

        Returns
        -------
            str: The name of the rain station.

        """
        return self.name

    def get_device_id(self):
        """
        Get the device ID of the rain station.

        Returns
        -------
            str: The device ID of the rain station.

        """
        return self.device_id

    def get_module_id(self):
        """
        Get the module ID of the rain station.

        Returns
        -------
            str: The module ID of the rain station.

        """
        return self.module_id

    def get_latitude(self):
        """
        Get the latitude coordinate of the rain station.

        Returns
        -------
            float: The latitude coordinate of the rain station.

        """
        return self.latitude

    def get_longitude(self):
        """
        Get the longitude coordinate of the rain station.

        Returns
        -------
            float: The longitude coordinate of the rain station.

        """
        return self.longitude

    def get_data(self):
        """
        Get the data associated with the rain station.

        Returns
        -------
            list: The data associated with the rain station.

        """
        return self.data

    def get_distance(self):
        """
        Get the distance from the reference point.

        Returns
        -------
            float: The distance from the reference point.

        """
        return self.distance_from

    def calculate_distance_from_point(self, ref_latitude, ref_longitude):
        """
        Calculate the distance from a given point.

        Parameters
        ----------
            ref_latitude (float):
                The latitude coordinate of the reference point.
            ref_longitude (float):
                The longitude coordinate of the reference point.

        Returns
        -------
            float: The distance from the given point.

        """
        return np.sqrt((self.latitude - ref_latitude)**2 +
                       (self.longitude - ref_longitude)**2)


def calculate_corner_coorinates(latitude, longitude, radius):
    """
    Calculate corners of a square centered around a given coordinate pair.

    Parameters
    ----------
        latitude : float
            The latitude of the center point.
        longitude : float
            The longitude of the center point.
        radius : float
            The radius of the square.

    Returns
    -------
    tuple of floats
        A tuple containing the latitude and longitude coordinates of
        the northeast (NE) and southwest (SW) corners of the square.
        The tuple is in the following order:
            (latitude_ne, longitude_ne, latitude_sw, longitude_sw).

    """
    latitude_ne = latitude + radius * np.sin(np.pi / 4)
    longitude_ne = longitude + radius * np.cos(np.pi / 4)
    latitude_sw = latitude - radius * np.sin(np.pi / 4)
    longitude_sw = longitude - radius * np.cos(np.pi / 4)
    return latitude_ne, longitude_ne, latitude_sw, longitude_sw


def quicksort_rain_station_list(rain_station_list, test=False):
    """
    Quicksort the station list based on distance from point.

    Parameters
    ----------
        rain_station_list : list
            The rain station list that should be sorted based on distance
        test : Bool
            optional parameter, used for testing that the list is correctly sorted
        Returns
    -------
    Sorted rain_staion_list in accending order

    """

    def partition(rain_station_list, low, high):
        pivot = rain_station_list[high].get_distance()
        i = low - 1

        for j in range(low, high):
            if rain_station_list[j].get_distance() <= pivot:
                i += 1
                (rain_station_list[i], rain_station_list[j]) = \
                    (rain_station_list[j], rain_station_list[i])

        (rain_station_list[i + 1], rain_station_list[high]) = \
            (rain_station_list[high], rain_station_list[i + 1])

        return i + 1

    def quicksort(rain_station_list, low, high):
        if low < high:
            part = partition(rain_station_list, low, high)
            quicksort(rain_station_list, low, part - 1)
            quicksort(rain_station_list, part + 1, high)

    quicksort(rain_station_list, 0, len(rain_station_list) - 1)
    if test:
        k = 0
        for station in rain_station_list:
            print(f"{k} ", station.get_distance())
            k += 1

    return rain_station_list


def get_station_from_coords(auth_token, latitude_ne, longitude_ne, latitude_sw,
                            longitude_sw, required_data="rain", gui=None):
    """
    Get rain station information from Netatmo using their Api.

    Args
    ----
        auth_token : string
            Users Authorization token, recieved previously
        latitude_ne : float
            North East corner of area, latitude
        longitude_ne : float
            North East corner of area, longitude
        latitude_sw : float
            South west corner of area, latitude
        longitude_sw : float
            South west corner of area, longitude
        required_data : string, optional
            Set to rain, application currently only addapted for rain data

    Returns
    -------
        Returns a list of Rain_station objects containing name, device_id,
        module_id, latitude, longitude, and distance from center of longitude
        and latitude input parameters of the rain station,
        found within the range.

    Raises
    ------
        ValueError: If the rain module NAModule3 is not present
        in one of the stations.
        KeyError: If there is no body present in the response,
        returns the error presented by Netatmo.

    """

    def update_gui(message):
        if gui is not None:
            gui.event_queue.put(("message", message))

    url = "https://api.netatmo.com/api/getpublicdata"
    header = {
        "Authorization": "Bearer " + auth_token
    }
    params = {"lat_ne": latitude_ne,
              "lon_ne": longitude_ne,
              "lat_sw": latitude_sw,
              "lon_sw": longitude_sw,
              "required_data": required_data
              }

    response = requests.get(url, headers=header, params=params, timeout=25)
    stations_in_area = response.json()

    try:
        body = stations_in_area["body"]
    except KeyError as exc:
        error_message = stations_in_area.get("error")
        if error_message == {'code': 500, 'message': 'Internal Server Error'}:
            raise InternalServerError from exc
        if error_message == {'code': 2, 'message': 'Invalid access_token'}:
            raise NoActiveTokenError
        if error_message == {'code': 26, 'message': 'User usage reached'}:
            raise NoApiCallsLeftError from exc

        raise NetatmoGeneralError(stations_in_area.get("error")) from exc

    rain_station_list = []
    for device in body:
        device_id = device["_id"]
        location = device["place"]["location"]
        longitude, latitude = location

        try:
            name = f"{str(device['place']['street'])}, " \
                f"{str(device['place']['city'])}, ({str(location)[1:-1]}), " \
                f"{device_id}"
        except KeyError:
            try:
                name = f"{str(device['place']['city'])}, " \
                    f"({str(location)[1:-1]}), {device_id}"
            except KeyError:
                name = f"({str(location)[1:-1]}), {device_id}"

        found = False
        for module in device["module_types"]:
            if device["module_types"].get(module) == "NAModule3":
                module_id = module
                found = True
                break

        if not found:
            update_gui("could not find NAMoudule3")
            raise ValueError("could not find NAMoudule3")

        station = RainStation(name, device_id, module_id,
                              (latitude, longitude))
        station.save_distance_from(
            (latitude_ne + latitude_sw) / 2, (longitude_ne + longitude_sw) / 2)
        rain_station_list.append(station)

    return rain_station_list
