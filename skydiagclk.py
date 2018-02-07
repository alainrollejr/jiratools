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



def main(argv):   
    """
    change appropriately: 
    if assignee contains these keywords, the assigned company will be assumed to be skyline
    """
    skyline_assignee_keywords = ["lodefier","annys","cools","skyline"]
    
    parser = argparse.ArgumentParser(description='script to get start/stop clock data for SKYDIAG jira issues')
    
    parser.add_argument('-u','--user', help='jira user name', required=True)
    parser.add_argument('-p','--password', help='jira password', required=True)
    parser.add_argument('-i','--issue', help='issue eg SKYDIAG-618', required=False)
    parser.add_argument('-a','--url', help='url, defaults to https://issues.newtec.eu/ (mind the end / !)', required=False)
    
    args = vars(parser.parse_args())
    
    user = args['user']    
    password = args['password']
    url = args['url']
    issue = args['issue']
    
    
     
    # the dataframe column headers
    columns = ['dateTime', 'issue','status','severity','assignee','assigned_company','delta_time']
    df = pd.DataFrame(columns=columns)
    

    if url is None:
        url= 'https://issues.newtec.eu/'
        
    if issue is None:
        # query all SKYDIAG issues
        # use maxResult=-1 to get all issues
        urlstr = url + 'rest/api/2/search?jql=project="SKYDIAG"&expand=changelog&maxResults=100'
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
            for j in range(nr_histories): # each element is a dict(ionary)        
                #print(rjson["issues"][i]["changelog"]["histories"][j]["created"])
                
                dateTime = parse(rjson["issues"][i]["changelog"]["histories"][j]["created"])
                
                if rjson["issues"][i]["changelog"]["histories"][j]["items"][0]["field"]=="assignee":            
                    to_mail = rjson["issues"][i]["changelog"]["histories"][j]["items"][0]["to"]
                    
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
                            print(delta_time)
                        else:
                            delta_time = 0
                        prev_dateTime = dateTime
                            
                        
                                
                        row=pd.Series([str(dateTime),str(issue_key),str(issue_status),
                                       str(issue_severity),str(to_mail),str(assigned_company),
                                       str(delta_time)],columns)        
                        
                        
                        df = df.append([row],ignore_index=True)
                        row_index_in_issue = row_index_in_issue +1
            
    else:
        # only one issue 
        urlstr = url + 'rest/api/2/issue/'+str(issue)+'?expand=changelog' 
        print(urlstr)        
        r = requests.get(urlstr, auth=(user, password))    
        rjson = r.json()        
        
     
        
        
        issue_status = rjson["fields"]["status"]["name"]
        print(issue_status)
        

        
        issue_severity = rjson["fields"]["customfield_10072"]["value"]
        print(issue_severity)
        
        nr_histories = int(rjson["changelog"]["total"])
        #print(nr_histories)
        for i in range(nr_histories): # each element is a dict(ionary)        
            print(rjson["changelog"]["histories"][i]["created"])
            dateTime = parse(rjson["changelog"]["histories"][i]["created"])
            
            
            if rjson["changelog"]["histories"][i]["items"][0]["field"]=="assignee":            
                to_mail = rjson["changelog"]["histories"][i]["items"][0]["to"]
                print(dateTime)
                print(type(dateTime))
                print(to_mail)
                assigned_company = "newtec"
                for key in skyline_assignee_keywords:
                    if key in to_mail:
                        assigned_company = "skyline"
                print(assigned_company)
                        
                row=pd.Series([str(dateTime),str(issue),str(issue_status),
                               str(issue_severity),str(to_mail),str(assigned_company)],columns)        
                
                
                df = df.append([row],ignore_index=True)   
    
    
    print(df.head())  
    df.to_csv('skydiagclk_report.csv')
        

    
       
    
if __name__ == "__main__":
    main(sys.argv)