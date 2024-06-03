# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 13:07:49 2023

@author: tagtyk0616
"""


class NetatmoApiError(Exception):
    """
    Error when error is recieved from Netatmo Api
    """


class NoApiCallsLeftError(Exception):
    pass


class NoDataInStationError(Exception):
    pass


class NetatmoGeneralError(Exception):
    pass


class NoActiveTokenError(Exception):
    pass


class InternalServerError(Exception):
    pass


class InvalidInputError(Exception):
    pass


class MaxApiCallReachedError(Exception):
    pass


class ApiCounter:
    def __init__(self, max_calls):
        self.call_count = 0
        self.max_calls = max_calls

    def increment(self):
        self.call_count += 1
        if self.call_count > self.max_calls:
            raise MaxApiCallReachedError("Maximum API calls exceeded")

    def add(self, amount):
        self.call_count += amount

    def get_count(self):
        return self.call_count

    def reset_count(self):
        self.call_count = 0


api_counter = ApiCounter(max_calls=499)
