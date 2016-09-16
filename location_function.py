# -*- coding: utf-8 -*-
"""
Created on Mon Aug  1 14:11:10 2016

@author: zbook
"""



import networkx as nx
import matplotlib.pyplot as plt
import requests
import json
from urllib.parse import urlparse, quote
from pprint import pprint
from geopy import geocoders
from operator import itemgetter



def is_coord(s):
    if ',' not in s:
        s = s.replace(' ', ',')
    splitted = s.split(',')

    for coord in splitted:
        try:
            float(coord)
        except:
            return False

    return True


'''
This is the location function used to transform a location string to distinct location entities of city, state
and country.    
'''

def location(given_location):
    
    given_location = given_location.lower().replace('area','')
    given_location = given_location.lower().replace('district','')
    given_location = given_location.lower().replace('uk','united kingdom')
        
    
    # GeocoderTimedOut('Service timed out')
    while True:
        try:
            gn = geocoders.GeoNames(username='skiasdim')
            total_population = 0.0
            location_population = 0

            extracted_location = {'city': '',
                                  'state': '',
                                  'country': '',
                                  'probability': 0.0}

            if is_coord(given_location):
                if ',' not in given_location:
                    given_location = given_location.replace(' ', ',')
                list_of_locations = gn.reverse(given_location, exactly_one=False)
            else:
                list_of_locations = gn.geocode(given_location, exactly_one=False)

            # get the first no matter what
            try:
                location = list_of_locations[0].raw
                location_population = location['population']
                name = location['name']
            except:
                return extracted_location

            if location['fclName'] == 'city, village,...':
                extracted_location['city'] = location['name']
                extracted_location['state'] = location['adminName1']
                extracted_location['country'] = location['countryName']

            elif location['fclName'] == 'country, state, region,...':
                extracted_location['city'] = ''
                extracted_location['state'] = location['adminName1']
                extracted_location['country'] = location['countryName']

            location_temp_list = []
            for location in list_of_locations:
                try:
                    if location.raw['name'].lower() == name.lower():
                        if (location.raw['name'], location.raw['countryName']) not in location_temp_list:
                            # for debugging purposes
                            ##print (location.raw['name'],location.raw['countryName'])
                            total_population += location.raw['population']
                            location_temp_list.append((location.raw['name'], location.raw['countryName']))
                except:
                    continue

            try:
                extracted_location['probability'] = location_population / total_population
            except:
                # check if population of a found location is 0 (database? mistake?)
                if extracted_location['probability'] == 0 and (
                        (extracted_location['city'] != '') or (extracted_location['state'] != '') or (
                    extracted_location['country'] != '')):
                    extracted_location['probability'] = 0.99
                else:
                    return extracted_location

            return extracted_location

        except:
            continue


# return extracted_location

def nameFunction():
    pass

