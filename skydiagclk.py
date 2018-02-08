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

    total = office_day * working_days
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
    """
    change appropriately: 
    if assignee contains these keywords, the assigned company will be assumed to be skyline
    """
    skyline_assignee_keywords = ["lodefier","annys","cools","skyline"]
    
    parser = argparse.ArgumentParser(description='script to get start/stop clock data for SKYDIAG jira issues')
    
    parser.add_argument('-u','--user', help='jira user name', required=True)
    parser.add_argument('-p','--password', help='jira password', required=True)
    parser.add_argument('-a','--url', help='url, defaults to https://issues.newtec.eu/ (mind the end / !)', required=False)
    
    args = vars(parser.parse_args())
    
    user = args['user']    
    password = args['password']
    url = args['url']
   
    
    
     
    # the dataframe column headers
    columns = ['dateTime', 'issue','status','severity','from','assignee','assigned_company','delta_calendar_time','office_delta_time(h)','delta_time_spent_in_company']
    df = pd.DataFrame(columns=columns)
    
    summary_columns = ['issue','status','severity','current_assignee','current_assigned_company','total_office_delta_time_spent_in_newtec(h)','total_office_delta_time_spent_in_skyline(h)']
    df_summary = pd.DataFrame(columns=summary_columns)
    

    if url is None:
        url= 'https://issues.newtec.eu/'
        
    
    # query all SKYDIAG issues
    # use maxResult=-1 to get all issues
    urlstr = url + 'rest/api/2/search?jql=project="SKYDIAG"&expand=changelog&maxResults=-1'
    print(urlstr)
    r = requests.get(urlstr, auth=(user, password))    
    rjson = r.json()  
    
    nr_issue = len(rjson["issues"])
    
    print(nr_issue)
    
    for i in range(nr_issue):
        #print(rjson["issues"][i])
        issue_key = rjson["issues"][i]["key"]
        print(issue_key)
        
        issue_status = rjson["issues"][i]["fields"]["status"]["name"]
        print(issue_status)
    
        
        
        issue_severity = rjson["issues"][i]["fields"]["customfield_10072"]["value"]
        print(issue_severity)
        
        nr_histories = int(rjson["issues"][i]["changelog"]["total"])
        print(nr_histories)
        
        
        row_index_in_issue = 0
        prev_dateTime = 0
        prev_company = "newtec"
        total_office_delta_time_spent_in_newtec = 0
        total_office_delta_time_spent_in_skyline = 0
        for j in range(nr_histories): # each element is a dict(ionary)        
            #print(rjson["issues"][i]["changelog"]["histories"][j]["created"])
            
            dateTime = parse(rjson["issues"][i]["changelog"]["histories"][j]["created"])
            
            if rjson["issues"][i]["changelog"]["histories"][j]["items"][0]["field"]=="assignee":            
                to_mail = rjson["issues"][i]["changelog"]["histories"][j]["items"][0]["to"]
                from_str = rjson["issues"][i]["changelog"]["histories"][j]["items"][0]["from"]
                
                print(dateTime)
                #print(type(dateTime))
                print(to_mail)
                
                if to_mail is None:
                    print('to: null')
                else:
                    # it is an assign action, with filled in 'to' field
                    assigned_company = "newtec" #default assumption
                    for key in skyline_assignee_keywords:
                        if key in to_mail:
                            assigned_company = "skyline"
                    print(assigned_company)
                    
                    if row_index_in_issue > 0:
                        delta_time = dateTime - prev_dateTime
                        office_delta_time = office_time_between(prev_dateTime,dateTime)
                        print(delta_time)
                        print(office_delta_time)
                        hours, remainder = divmod(office_delta_time.total_seconds(), 3600)
                        
                        if prev_company=="skyline":
                            if total_office_delta_time_spent_in_skyline==0:
                                total_office_delta_time_spent_in_skyline = office_delta_time
                            else:
                                total_office_delta_time_spent_in_skyline = total_office_delta_time_spent_in_skyline + office_delta_time
                        else:
                            if total_office_delta_time_spent_in_newtec==0:
                                total_office_delta_time_spent_in_newtec = office_delta_time
                            else:
                                total_office_delta_time_spent_in_newtec = total_office_delta_time_spent_in_newtec + office_delta_time
                            
                    else:
                        delta_time = 0
                        office_delta_time = 0
                        hours = 0
                        
                    prev_dateTime = dateTime
                        
                    
                            
                    row=pd.Series([str(dateTime),str(issue_key),str(issue_status),
                                   str(issue_severity),str(from_str),str(to_mail),str(assigned_company),
                                   str(delta_time),hours,prev_company],columns)        
                    
                    
                    df = df.append([row],ignore_index=True)
                    row_index_in_issue = row_index_in_issue +1
                    prev_company = assigned_company
                    
        # for still ongoing tickets add a final row that has the date set to "now"
        if issue_status=="Open" or issue_status=="In Progress" or issue_status=="Accepted":
            now = datetime.now(pytz.utc)
            delta_time = now - prev_dateTime
            office_delta_time = office_time_between(prev_dateTime,now)
            hours, remainder = divmod(office_delta_time.total_seconds(), 3600)
            
            
            row=pd.Series([str(now),str(issue_key),str(issue_status),
                           str(issue_severity),"dummy",str(to_mail),str(assigned_company),
                           str(delta_time),hours,prev_company],columns)        
                        
                        
            df = df.append([row],ignore_index=True)
            
            if prev_company=="skyline":
                if total_office_delta_time_spent_in_skyline==0:
                    total_office_delta_time_spent_in_skyline = office_delta_time
                else:
                    total_office_delta_time_spent_in_skyline = total_office_delta_time_spent_in_skyline + office_delta_time
            else:
                if total_office_delta_time_spent_in_newtec==0:
                    total_office_delta_time_spent_in_newtec = office_delta_time
                else:
                    total_office_delta_time_spent_in_newtec = total_office_delta_time_spent_in_newtec + office_delta_time
        
        if  total_office_delta_time_spent_in_newtec==0:
            newtec_hours = 0
        else:
            newtec_hours, remainder = divmod(total_office_delta_time_spent_in_newtec.total_seconds(), 3600)
            
        if  total_office_delta_time_spent_in_skyline==0:
            skyline_hours = 0
        else:            
            skyline_hours, remainder = divmod(total_office_delta_time_spent_in_skyline.total_seconds(), 3600)
                    
        summary_row = pd.Series([str(issue_key),str(issue_status),
                                 str(issue_severity),str(to_mail),str(assigned_company),
                                 newtec_hours,skyline_hours],summary_columns)
        df_summary = df_summary.append([summary_row],ignore_index=True)

    print(df.head())  
    df.to_csv('skydiagclk_detailed_report.csv')
    
    print(df_summary.head())
    df_summary.to_csv('skydiagclk_summary.csv')
        

    
       
    
if __name__ == "__main__":
    main(sys.argv)