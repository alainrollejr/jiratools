# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 15:34:42 2018

@author: aro
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import argparse
import pandas as pd
from dateutil.parser import parse

from datetime import datetime
from datetime import timedelta
import pytz

def adjust_hour_delta(t, start, stop):

    start_hour = start.seconds//3600
    end_hour = stop.seconds//3600
    zero = timedelta(0)

    if t - t.replace(hour = start_hour, minute = 0, second = 0) < zero:
        t = t.replace(hour = start_hour, minute = 0, second = 0)
    elif t - t.replace(hour = end_hour, minute = 0, second = 0) > zero:
        t = t.replace(hour = end_hour, minute = 0, second = 0)
    # Now get the delta
    delta = timedelta(hours=t.hour, minutes=t.minute, seconds = t.second)

    return delta    

def full_in_between_working_days(a, b):
    working = 0
    b = b - timedelta(days=1)
    while b.date() > a.date():
        if b.weekday() < 5:
            working += 1
        b = b - timedelta(days=1)
    return working

def office_time_between(a, b, start = timedelta(hours = 8),
                        stop = timedelta(hours = 17)):
    """
    Return the total office time between `a` and `b` as a timedelta
    object. Office time consists of weekdays from `start` to `stop`
    (default: 08:00 to 17:00).
    """
    zero = timedelta(0)
    assert(zero <= start <= stop <= timedelta(1))
    office_day = stop - start
    working_days = full_in_between_working_days(a, b) 
    
    print(working_days)

    total = office_day * working_days
    print(total)
    # Calculate the time adusted deltas for the the start and end days
    a_delta = adjust_hour_delta(a, start, stop)
    b_delta = adjust_hour_delta(b, start, stop)


    if a.date() == b.date():
        # If this was a weekend, ignore
        if a.weekday() < 5:
            total = total + b_delta - a_delta
    else:
        # We now consider if the start day was a weekend
        if a.weekday() > 4:
            a_worked = zero
        else:
            a_worked = stop - a_delta
        # And if the end day was a weekend
        if b.weekday() > 4:
            b_worked = zero
        else:
            b_worked = b_delta - start
        total = total + a_worked + b_worked

    return total

def main(argv):   
    
    b = parse("2018-02-07 22:09:02.379500+00:00")
    a = parse("2018-01-24 18:15:40+01:00")
    
    total = office_time_between(a, b)
    print(total)
    
    hours, remainder = divmod(total.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    print(hours)
    print(minutes)
        

    
       
    
if __name__ == "__main__":
    main(sys.argv)