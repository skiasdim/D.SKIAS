# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 14:38:46 2016

@author: zbook
"""



import os
import networkx as nx
import matplotlib.pyplot as plt
import requests
import json
from urllib.parse import urlparse, quote
from pprint import pprint
from geopy import geocoders
from geopy.geocoders import Nominatim
from operator import itemgetter

try:
    from graph.graph_fuctions.location_function import *
except:
    from location_function import *

#
# try:
#     from graph.graph_fuctions.load_functions import *
# except:
#     from load_functions import *

from networkx.readwrite import json_graph
from email_validator import validate_email, EmailNotValidError

headers = {'Authorization': 'token 3d6cad891ff555124101ef9fc29d73f3393a12ec'}


# Graph initialization
SSG = nx.Graph()
GG = nx.Graph()
GG2 = nx.Graph()
test_paths = {}

myedgelist = []

# are used  with github linkedin combination function
oldgraphcolors = []
newgraphcolors = []
oldgraphcolorroot = []

full_contact_list = []
link_scan_list = []
profile_list = []
redirected_list = []

searched_github_profiles = []

'''
Function that accesses Github directly and retrieves profile data
'''
def loadGithubProfiles(fullname, original_location):
    gh_dict = {}
    gh_list = []

    # dim_token = token 480ff006ea02f16cbec3a2ec2e5c027d44e0985e
    headers = {'Authorization': 'token 204ae56642a0cf1ce58a44399b8648461c52ba83'}
    url = 'https://api.github.com/search/users?q=%s' % fullname
    r = requests.get(url, headers=headers, timeout=5)
    data = json.loads(r.text)

    records_fount = 0
    exit_counter = 0

    total_profiles = data['total_count']
    for profile in data['items']:
        if exit_counter < 20:
            exit_counter += 1
            # print (item['login']) myedgelist = []

            url2 = profile['url']
            r2 = requests.get(url2, headers=headers, timeout=5)
            data_profile = json.loads(r2.text)

            skills_list = []

            loc = location(str(data_profile['location']))
            
            try:
                '''=========================================================================================
                 checks if the location of each github account found is "similar" to the original one (the one that we are looking for)
                 also, if the location field of the github account is empty (null) then it collects it as well
                 output file contains up to 5 github accounts.
                 ===========================================================================================
                '''
                if  (loc['country'] == original_location['country'] and loc['country'] != '') or  (loc['state'] == original_location['state'] and loc['state'] != '') or (loc['city'] == original_location['city'] and loc['city'] != ''):
                    gh_dict = {
                        'url': data_profile['url'],
                        'name': data_profile['name'],
                        'blog': data_profile['blog'],
                        'country': loc['country'],
                        'state': loc['state'],
                        'city': loc['city'],
                        'email': data_profile['email'],
                        'url': data_profile['url'],
                        'gh_skills': skills_list,
                        'total_profiles': total_profiles,
                        'loc_probability': loc['probability'],
                        'repos_url': data_profile['repos_url']
                    }

                    gh_list.append(gh_dict.copy())
                    gh_dict.clear()

                    records_fount += 1
                    if records_fount > 5:
                        break
            except:
                print ('except')
                continue
        else:
            writeToFile('gh_profiles/%s' % fullname, gh_list)
            return gh_list

    writeToFile('gh_profiles/%s' % fullname, gh_list)
    return gh_list


'''
adds skills to the graph of the relevant github profile that has been identified
'''
def add_skills(G,data_profile):

    headers = {'Authorization': 'token 204ae56642a0cf1ce58a44399b8648461c52ba83'}

    ######################### FOR SKILLS and REPOSITORIES gathered data ##############
    url = data_profile['repos_url']
    r=requests.get(url, headers=headers,timeout=5)
    data_repos = json.loads(r.text)

    skills_list = []

    for repo in data_repos:

        if repo['language'] == 'null':
            continue
        else:
            if repo['language'] not in skills_list:
                if repo['language']:
                    skills_list.append(repo['language'])



    ########adding skills to the graph###############
    url = data_profile['url'].replace('api.', '')
    url = urlSplitter(url)['value']

    for skill in skills_list:
        G.add_edge(url, url + "/" + skill, weight=1, edge_type='entity')
        G.add_node(url + "/" + skill, value=skill, label=skill, node_type='skill', root=url)

    return



def email_validator(email):
    try:
        mx = validate_email(email)['mx']
        mx = mx[0][1].replace('.', '')
        try:
            if float(mx):
                return False
            else:
                return True
        except:
            return True
    except:
        return False

def splitname(name):
    
    name = name.split(' ')
    
    return {'firstName': name[0], 'secondName':name[1]}

def writeToFile(name, data):
    try:
        f_name = os.path.join(os.path.realpath(os.path.dirname(__file__)), '..','json',name+'.json')
    except:
        f_name = '../json/'+name+'.json'
    with open(f_name, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=True)


def openfile(file):
    try:
        f_name = os.path.join(os.path.realpath(os.path.dirname(__file__)), '..','json',file+'.json')
    except:
        f_name = '../json/'+file+'.json'
    with open(f_name, 'r') as f:
        data = json.load(f)

    return data


def redirectedUrl(url):
    try:
        r = requests.get(url)
        if (r.status_code != 200) and (r.status_code != 999):
            return 'spam'
        return r.history[-1].url
    except:
        return url


def urlSplitter(url):
    profile_links = ["facebook", "twitter", "github", "linkedin", "stackoverflow", "klout", "glassdoor", "crunchbase",
                     "lanyrd"]

    url = cutLastSlash(url)
    url = url.lower()

    parsed_url = urlparse(url)
    value = "flag"

    for profile in profile_links:
        if profile in url:
            value = profile

    if value == "flag":
        value = parsed_url.netloc

    alias = parsed_url.path.split('/')[-1]
    value = value + "/" + alias

    return {
        'value': value,
        'alias': alias}


def cutLastSlash(website):
    if website[-1] == "/":
        website = website[:-1]

    return website

'''
checks the redirection of a webiste's URL
'''
def websiteRedirected(website):
    if website in redirected_list:
        return website

    url = redirectedUrl(website)

    value = cutLastSlash(url)
    value = value.lower()

    value = value.replace('https://', 'http://')

    redirected_list.append(value)

    return value


def isItProfile(website):
    profile_links = ["facebook", "twitter", "github", "linkedin", "stackoverflow", "klout", "glassdoor", "crunchbase",
                     "lanyrd"]
    blog_links = ['github.io']

    if any(word in website for word in profile_links):
        if any(word in website for word in blog_links):
            return False
        else:
            return True
    else:
        return False


def isItSourceProfile(website):
    profile_links = ["twitter", "github"]

    if any(word in website for word in profile_links):
        return True
    else:
        return False


'''
The following two functions are responsible for growing the graoh the graph.

      graphGeneration() applies the DFS recursion algorithm which parses the nodes of our graph. If it finds
      a suitable entity for making api calls, it generates its graph. 
      match() applies entity matching and subsequently addToGraph() appends the new graph(local one) to the 
      original one(global)
      
'''

def addToGraph(G, New):
    try:
        G.add_edges_from(match(G, New))

        G.add_nodes_from(New.nodes(data=True))
        G.add_edges_from(New.edges(data=True))
    except:
        pass

    New.clear()


def graphGeneration(G, New):
    # Temp = nx.Graph()

    Temp = New.copy()
    addToGraph(G, New)

    New.clear()
    
    ######debuging####################
#    print (link_scan_list,full_contact_list,profile_list)
#    print (searched_github_profiles)
    ##################################
    
    for Temp_index in Temp.nodes():
        if Temp.node[Temp_index]['node_type'] == 'email' and (Temp.node[Temp_index]['value'] not in full_contact_list):
            full_contact_list.append(Temp.node[Temp_index]['value'])
            if len(full_contact_list) > 3:
                return
            fullContact(Temp.node[Temp_index]['value'], New)
            graphGeneration(G, New)
        elif Temp.node[Temp_index]['node_type'] == 'website':
            url = Temp.node[Temp_index]['value']
            # url = urlparse(url).netloc
            if url not in link_scan_list:
                if not isItProfile(url):
                    link_scan_list.append(url)
                    if len(link_scan_list) > 3:
                        return
                    linkScan(Temp.node[Temp_index]['value'], New)
                    graphGeneration(G, New)                   
        elif (Temp.node[Temp_index]['node_type'] == 'profile' and (Temp.node[Temp_index]['value'] not in profile_list)):
            if isItSourceProfile(Temp.node[Temp_index]['value']):
                profile_list.append(Temp.node[Temp_index]['value'])
                if len(profile_list) > 3:
                    return
                value = Temp.node[Temp_index]['value'].split('/')
                profile = value[0]
                alias = value[1]
                if profile == 'twitter':
                    twitter(alias, New)
                    graphGeneration(G, New)
                elif profile == 'github':
                    if searched_github_profiles == []:
                        searched_github_profiles.append('github'+alias)
                        ghuser(alias, New)
                        graphGeneration(G, New)




def match(G, New):
    myedge = []
    #    mynode = []

    for New_index in New.nodes():
        for G_index in G.nodes():
            if ((G.node[G_index]['value'].lower() == New.node[New_index]['value'].lower()) and (
                G.node[G_index]['node_type'] == New.node[New_index]['node_type']) and (
                G.node[G_index]['root'] != New.node[New_index]['root'])):
                if New.node[New_index]['node_type'] == 'firstName':
                    myedge.append((New_index, G_index, {'weight': 0.05, 'edge_type': New.node[New_index]['node_type']}))
                elif New.node[New_index]['node_type'] == 'country':
                    myedge.append((New_index, G_index, {'weight': 0.05, 'edge_type': New.node[New_index]['node_type']}))
                elif New.node[New_index]['node_type'] == 'secondName':
                    myedge.append((New_index, G_index, {'weight': 0.1, 'edge_type': New.node[New_index]['node_type']}))
                elif New.node[New_index]['node_type'] == 'state':
                    myedge.append((New_index, G_index, {'weight': 0.1, 'edge_type': New.node[New_index]['node_type']}))
                elif New.node[New_index]['node_type'] == 'fullName':
                    try:
                        enhancedProbability = 0.1 * (1 / int(New.node[New_index]['total_profiles']))
                        myedge.append((New_index, G_index, {'weight': 0.30 + enhancedProbability, 'edge_type': New.node[New_index]['node_type']}))
                    except:
                        myedge.append(
                            (New_index, G_index, {'weight': 0.30, 'edge_type': New.node[New_index]['node_type']}))
                elif New.node[New_index]['node_type'] == 'city':
                    myedge.append((New_index, G_index, {'weight': 0.30, 'edge_type': New.node[New_index]['node_type']}))
                elif New.node[New_index]['node_type'] == 'alias' or New.node[New_index]['node_type'] == 'topic' or \
                                New.node[New_index]['node_type'] == 'skill':
                    myedge.append((New_index, G_index, {'weight': 0.05, 'edge_type': New.node[New_index]['node_type']}))
                else:  # website or email or profile or url
                    myedge.append((New_index, G_index, {'weight': 1, 'edge_type': New.node[New_index]['node_type']}))
            else:
                continue

    global myedgelist

    for edge in myedge:
        myedgelist.append((edge[0], edge[1]))

    return myedge


                        

'''
Is the function that retreives data from Linkedin and then it creates a local graph which consists of 
LinkedIn's source node and all the extracted entities nodes attached to it.
'''

def linkedIn(alias, G):
    location_name_bool = False

    url = 'http://46.101.78.187:8000/contextapi/api/get_linkedin_info/%s' % alias
    r = requests.get(url, headers=headers, timeout=5)
    data = json.loads(r.text)

    # simplified to make it easier to use its index
    url = urlSplitter(data['url'])['value']
    
    #switched to using the given alias instead of the one that is fount in the data. Because sometimes are different 
    url = 'linkedin/'+alias

    G.add_node(url, value=url, label='LinkedIn', node_type='linkedin', root="/", alias=data['alias'])
    # create alias node
    G.add_edge(url, url + "/" + data['alias'], weight=1, edge_type='entity')
    G.add_node(url + "/" + data['alias'], value=data['alias'], label=data['alias'], node_type='alias', root=url)
    # Create a node -> the url used by linkedIn
    G.add_edge(url, url + "/" + url, weight=1, edge_type='entity')
    G.add_node(url + "/" + url, value=url, label=data['url'], alias=alias, node_type='profile', root=url)

    # add location and name data about this profile from a json file (if exists).


    for field in data:
        if field == 'websites':
            for i in range(int(len(data[field]))):
                entity = data[field][i]
                if 'linkedin' not in entity:
                    value = websiteRedirected(entity)
                    if value != 'spam':
                        if not isItProfile(value):
                            G.add_edge(url, url + "/" + entity, weight=1, edge_type='entity')
                            G.add_node(url + "/" + entity, label=entity, value=value, node_type='website', root=url)
                        else:
                            G.add_edge(url, url + "/" + entity, weight=1, edge_type='entity')
                            G.add_node(url + "/" + entity, label=entity, value=urlSplitter(entity)['value'], alias=urlSplitter(entity)['alias'], node_type='profile', root=url)
        elif field == 'emails':
            for entity in data[field]:

                if email_validator(entity) is True:
                    G.add_edge(url, url + "/" + entity, weight=1, edge_type='entity')
                    G.add_node(url + "/" + entity, label=entity, value=entity, node_type='email', root=url)
        elif field == 'name':
            location_name_bool = True
            G.add_edge(url, url + "/" + data[field], weight=1, edge_type='entity')
            G.add_node(url + "/" + data[field], label=data[field], value=data[field], node_type='fullName', root=url)

            name = splitname(data[field])            
            
            G.add_edge(url, url + "/" + name['firstName'], weight=1, edge_type='entity')
            G.add_node(url + "/" + name['firstName'], label=name['firstName'], value=name['firstName'], node_type='firstName', root=url)
            
            G.add_edge(url, url + "/" + name['secondName'], weight=1, edge_type='entity')
            G.add_node(url + "/" + name['secondName'], label=name['secondName'], value=name['secondName'], node_type='secondName', root=url)
            
        elif field == 'location':
            location_name_bool = True
            loc = location(str(data['location']))
            for key in loc.keys():
                if key == 'probability':
                    continue
                if bool(loc[key]):
                    G.add_edge(url, url + "/" + key, weight=loc['probability'], edge_type='entity')
                    G.add_node(url + "/" + key, value=loc[key], label=loc[key], node_type=key, root=url)

    if location_name_bool == False:
        try:
            addLinkedinLocationName(alias, G, url)
        except:
            pass


'''
Is the function that retreives data from Full contact and then it creates a local graph which consists of 
full contact's source node and all the extracted entities nodes attached to it.
'''

def fullContact(email, G):
    url = 'http://46.101.78.187:8000/contextapi/api/full_contact/%s' % email
    r = requests.get(url, headers=headers,timeout= 5)
    data = json.loads(r.text)

    if data == {}:
        return

    G.add_node(email, value=email, label='FullContact', node_type='fullcontant', root="/")
    # Create a node -> the email used by FC

    G.add_edge(email, email + "/" + email, weight=data['likelihood'], edge_type='entity')
    G.add_node(email + "/" + email, value=email, label=email, node_type='email', root=email)

    for field in data:
        if field == 'likelihood' or field == 'organizations':
            continue
        elif field == 'profiles' and bool(data[field]):
            for profile in data[field]:
                G.add_edge(email, email + "/" + profile['Name'], weight=1, edge_type='entity')
                G.add_node(email + "/" + profile['Name'], value=urlSplitter(profile['url'])['value'],
                           label=profile['url'], alias=urlSplitter(profile['url'])['alias'], node_type='profile',
                           root=email)
        elif field == 'websites' and bool(data[field]):
            for website in data[field]:
                value = websiteRedirected(website)
                if value != 'spam':
                    G.add_edge(email, email + "/" + website, weight=1, edge_type='entity')
                    G.add_node(email + "/" + website, value=value, label=website, node_type='website', root=email)
        elif (field == 'country' or field == 'city' or field == 'state') and bool(
                data[field]):  # location and name fields
            G.add_edge(email, email + "/" + field, weight=1, edge_type='entity')
            G.add_node(email + "/" + field, value=data[field], label=data[field], node_type=field, root=email)
        elif (field == 'firstName' or 'secondName' or 'fullName') and bool(data[field]):  # location and name fields
            G.add_edge(email, email + "/" + field, weight=1, edge_type='entity')
            G.add_node(email + "/" + field, value=data[field], label=data[field], node_type=field, root=email)


'''
Is the function that retreives data from Link Scan and then it creates a local graph which consists of 
Link Scan's source node and all the extracted entities nodes attached to it.
'''

def linkScan(website, G):
    link_scan_profile_dict = {
        'github': 'https://github.com/',
        'twitter': 'http://twitter.com/',
        'stackoverflow': 'http://stackoverflow.com/users/'
    }

    url = 'http://46.101.78.187:8000/contextapi/api/link_scan/%s' % website
    r = requests.get(url, headers=headers,timeout= 5)  
    data = json.loads(r.text)

    G.add_node(website, value=website, label='link_scan', node_type='linkscan', root="/")

    # Create a node -> the website used by LinkScan
    G.add_edge(website, website + "/" + website, weight=1, edge_type='entity')
    G.add_node(website + "/" + website, value=websiteRedirected(website), label=website, node_type='website',
               root=website)

    for field in data:
        if field == 'links':
            continue
        elif field == 'emails' and bool(data[field]):
            list_keys = list(data[field].keys())
            for key in list_keys:
                if email_validator(key) is True:
                    G.add_edge(website, website + "/" + key, weight=data[field][key],edge_type='entity')
                    G.add_node(website + "/" + key, value=key, label=key, node_type='email', root=website)
        elif field == 'topics' and bool(data[field]):
            for topic in data[field]:
                if data[field][topic] > 0.8:
                    G.add_edge(website, website + "/" + topic, weight=data[field][topic], edge_type='entity')
                    G.add_node(website + "/" + topic, value=topic, label=topic, node_type='topic', root=website)
        elif field =='twitter' and bool(data[field]):  
            list_keys = list(data[field].keys())
            if list_keys:
                for key in list_keys:
                    G.add_edge(website, website + "/" +field+'/'+key, weight= data[field][key], edge_type='entity')
                    G.add_node(website + "/" +field+ '/' +key , value=field + "/" + key, label=link_scan_profile_dict[field] + key, alias=key, node_type='profile', root=website)
        elif field =='stackoverflow' and bool(data[field]):  
            list_keys = list(data[field].keys())
            if list_keys:
                for key in list_keys:
                    G.add_edge(website, website + "/" +field+'/'+key, weight= data[field][key], edge_type='entity')
                    G.add_node(website + "/" +field+ '/' +key , value=field + "/" + key, label=link_scan_profile_dict[field] + key, alias=key, node_type='profile', root=website)
        elif field =='github' and bool(data[field]):  
            list_keys = list(data[field].keys())
            if list_keys:
                for key in list_keys:
                    G.add_edge(website, website + "/" +field+'/'+key, weight= data[field][key], edge_type='entity')
                    G.add_node(website + "/" +field+ '/' +key , value=field + "/" + key, label=link_scan_profile_dict[field] + key, alias=key, node_type='profile', root=website)
        elif field == 'cvs' and bool(data[field]):  
            for cv in data[field]:
                G.add_edge(website, website + "/" + cv, weight=1, edge_type='entity')
                G.add_node(website + "/" + cv, value=cv, label='cv', node_type='cv', root=website)


'''
Is the function that  retreives data from githib (using contextScout's api) and then it creates a local graph which consists of 
Github's source node and all the extracted entities nodes attached to it.
'''

def ghuser(alias, G):
    url = 'http://46.101.78.187:8000/contextapi/api/ghuser/?alias=%s' % alias
    r = requests.get(url, headers=headers,timeout=5)
    # data = json.loads(r.text)
    #########################
    try:
        data = json.loads(r.text)
    except:
        data = {}

    if data == {}:
        alias = alias.replace(' ', '+')
        url = 'http://46.101.78.187:8000/contextapi/api/ghuser/%s' % alias
        r = requests.get(url, headers=headers,timeout=5)
        try:
            data = json.loads(r.text)
        except:
            data = {}

    if data == {}:
        return
    ###########################
    data = data['gh_user']
    url = urlSplitter(data['url'])['value']

    G.add_node(url, value=url, label='ghuser', node_type='github', root="/")
    # Create a node -> the url used by ghuser
    G.add_edge(url, url + "/" + url, weight=1, edge_type='entity')
    G.add_node(url + "/" + url, value=url, label=data['url'], alias=alias, node_type='profile', root=url)

    for field in data:
        if field == 'id' or field == 'url':
            continue
        elif field == 'email' and bool(data[field]):
            G.add_edge(url, url + "/" + data[field], weight=1, edge_type='entity')
            G.add_node(url + "/" + data[field], value=data[field], label=data[field], node_type='email', root=url)
        elif field == 'gh_skills' and bool(data[field]):
            list_keys = list(data[field].keys())
            if list_keys:
                for key in list_keys:
                    G.add_edge(url, url + "/" + key, weight=1, edge_type='entity')
                    G.add_node(url + "/" + key, value=key, label=key, node_type='skill', root=url)
        else:  # bio / location / blog
            if data[field]:
                if field == 'location':
                    loc = location(str(data['location']))
                    for key in loc.keys():
                        if key == 'probability':
                            continue
                        if bool(loc[key]):
                            G.add_edge(url, url + "/" + key, weight=loc['probability'], edge_type='entity')
                            G.add_node(url + "/" + key, value=loc[key], label=loc[key], node_type=key, root=url)
                elif field == 'bio':
                    G.add_edge(url, url + "/" + field, weight=1, edge_type='entity')
                    G.add_node(url + "/" + field, value=data[field], label=data[field], node_type='cv', root=url)
                else:  # blog
                    value = websiteRedirected(data[field])
                    if value != 'spam':
                        G.add_edge(url, url + "/" + field, weight=1, edge_type='entity')
                        G.add_node(url + "/" + field, value=value, label=data[field], node_type='website', root=url)



'''
Is the function that retreives data from Twitter and then it creates a local graph which consists of 
Twitter's source node and all the extracted entities nodes attached to it.
'''

def twitter(alias, G):
    url = 'http://46.101.78.187:8000/contextapi/api/twitter_topics/%s' % alias
    r = requests.get(url, headers=headers,timeout=5)
    data = json.loads(r.text)

    G.add_node(url, value=url, label='Twitter', node_type='twitter', root="/", alias=alias)
    # Create a node -> the url used by twitter
    G.add_edge(url, url + "/" + url, weight=1, edge_type='entity')
    G.add_node(url + "/" + url, value="twitter/" + alias, label="http://twitter.com/" + alias, alias=alias,
               node_type='profile', root=url)
                              
    total_score = 0.0
    for field in data:
        total_score = total_score + data[field]['score']
           
    for field in data:
        if total_score != 0:
            topic_score = (data[field]['score'] / total_score)
        else:
            topic_score = 0
        if topic_score > 0.5:
            G.add_edge(url, url + "/" + field, weight = topic_score, edge_type='entity')
            G.add_node(url + "/" + field, value=field, label=field, node_type='topic', root=url)




'''
Is the function that creates a local graph which consists of 
github's source node and all the extracted entities nodes attached to it. The data that uses as inout 
has been retrieved directly from github
'''

def ghuserLoad(data, G):
    url = data['url'].replace('api.', '')
    alias = url.split('/')[-1]

    url = urlSplitter(url)['value']

    G.add_node(url, value=url, label='ghuser', node_type='github', root="/")
    # Create a node -> the url used by ghuser
    G.add_edge(url, url + "/" + url, weight=1, edge_type='entity')
    G.add_node(url + "/" + url, value=url, label=data['url'].replace('api.', ''), alias=alias, node_type='profile',
               root=url)

    for field in data:
        if field == 'url' or field == 'total_profiles':
            continue
        elif field == 'email' and bool(data[field]):
            G.add_edge(url, url + "/" + data[field], weight=1, edge_type='entity')
            G.add_node(url + "/" + data[field], value=data[field], label=data[field], node_type='email', root=url)
        elif field == 'gh_skills' and bool(data[field]):
            continue
            for key in data[field]:
                G.add_edge(url, url + "/" + key, weight=1, edge_type='entity')
                G.add_node(url + "/" + key, value=key, label=key, node_type='skill', root=url)
        elif field == 'name':
            
            G.add_edge(url, url + "/" + data[field], weight=1, edge_type='entity')
            G.add_node(url + "/" + data[field], value=data[field], label=data[field], node_type='fullName', root=url, total_profiles=data['total_profiles'])
            
            name = splitname(data[field])   
            
            G.add_edge(url, url + "/" + name['firstName'], weight=1, edge_type='entity')
            G.add_node(url + "/" + name['firstName'], label=name['firstName'], value=name['firstName'], node_type='firstName', root=url, total_profiles=data['total_profiles'])
            
            G.add_edge(url, url + "/" + name['secondName'], weight=1, edge_type='entity')
            G.add_node(url + "/" + name['secondName'], label=name['secondName'], value=name['secondName'], node_type='secondName', root=url, total_profiles=data['total_profiles'])
            
        elif field == 'country':
            if bool(data[field]):
                G.add_edge(url, url + "/" + data[field], weight=data['loc_probability'], edge_type='entity')
                G.add_node(url + "/" + data[field], value=data[field], label=data[field], node_type='country', root=url)
        elif field == 'state':
            if bool(data[field]):
                G.add_edge(url, url + "/" + data[field], weight=data['loc_probability'], edge_type='entity')
                G.add_node(url + "/" + data[field], value=data[field], label=data[field], node_type='state', root=url)
        elif field == 'city':
            if bool(data[field]):
                G.add_edge(url, url + "/" + data[field], weight=data['loc_probability'], edge_type='entity')
                G.add_node(url + "/" + data[field], value=data[field], label=data[field], node_type='city', root=url)
        elif field == 'blog':
            if bool(data[field]):
                value = websiteRedirected(data[field])
                if value != 'spam':
                    G.add_edge(url, url + "/" + field, weight=1, edge_type='entity')
                    G.add_node(url + "/" + field, value=value, label=data[field], node_type='website', root=url)
        else:
            continue


'''
function that draws the graph, using matplotlib and networkX's draw function.
In order to work it needs an environment with ipython console. 
For this study Spyder was selected as the main editor for that reason.
'''
def printit(G):
    my_label = {}
    mycolorlist = []

    global myedgelist
    if myedgelist == []:
        myedgelist = G.edges()[:]

    plt.figure(3, figsize=(38, 32))
    pos = nx.fruchterman_reingold_layout(G)
    # Add custom labels
    for node in G.nodes():
        if 'label' in G.node[node].keys():
            my_label[node] = G.node[node]['label']

    nx.draw_networkx(G, pos=pos, labels=my_label, node_size=3000, with_labels=True, node_color='r', alpha=0.5)

    # colors = [color.get(node, 0.25) for node in G.nodes()]
    #
    # nx.draw_networkx(G, pos=pos, node_size=3000, with_labels=True, node_color=colors, alpha=0.3)
    # nx.draw_networkx_nodes(G, pos=pos, nodelist=li_fields, node_size=3000, with_labels=True, node_color = 'r',  alpha=0.5,)

    for node in G.nodes():
        try:
            if G.node[node]['root'] == "/":mycolorlist.append(node)
        except:
            continue

    nx.draw_networkx_nodes(G, pos=pos, nodelist=mycolorlist, node_size=3000, node_color='r', with_labels=True,
                           alpha=0.7)
    #try:
    nx.draw_networkx_edges(G, pos=pos, edgelist=myedgelist, edge_color='g', with_labels=True, alpha=0.5, width=5)
    #except:
        #pass

    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)

    nx.draw_networkx_nodes(G, pos=pos, nodelist=oldgraphcolors, node_size=3000, node_color='b', with_labels=True,
                           alpha=0.3)
    nx.draw_networkx_nodes(G, pos=pos, nodelist=oldgraphcolorroot, node_size=3000, node_color='b', with_labels=True,
                           alpha=0.7)



'''
#the rest of the functions are used to produce the entities scores of relatedness.
'''

'''
Source_graph() creates the graph with cosists of source nodes. This function creates a hyper-graph. 
Also it calculates the score (relatedness) of two source nodes.
'''

def source_graph(G, SG):
    SG.clear()

    for node_a, node_b, data in G.edges(data=True):
        score = 1
        if data['edge_type'] != 'entity':

            score = score * data['weight']
            score = score * G[G.node[node_a]['root']][node_a]['weight']
            score = score * G[G.node[node_b]['root']][node_b]['weight']

            try:
                SG[G.node[node_a]['root']][G.node[node_b]['root']]
                SG[G.node[node_a]['root']][G.node[node_b]['root']]['weight'] += score

                if SG[G.node[node_a]['root']][G.node[node_b]['root']]['weight'] >= 1:
                    SG[G.node[node_a]['root']][G.node[node_b]['root']]['weight'] = 1

            except:
                SG.add_edge(G.node[node_a]['root'], G.node[node_b]['root'], weight=score, edge_type='source_graph_edge')
                SG.add_node(G.node[node_a]['root'], label=G.node[node_a]['root'])
                SG.add_node(G.node[node_b]['root'], label=G.node[node_b]['root'])


'''
The rest are scoring functions used to compute the entity scores of relatedness
'''

def source_node_score(G, SG, source, target):
    linkedin_to_source = source_graph_score(G, SG, source.split('/')[-1])

    score = linkedin_to_source[target]

    return score


def source_graph_score(G, SG, alias):
    linkedin_to_source = {'linkedin/%s' % alias: 1}

    # first compute all scores between source node(Linkedin) and all other nodes:
    for node in SG.nodes():
        score = 0
        if (node != 'linkedin/%s' % alias):
            mypaths = nx.all_simple_paths(SG, 'linkedin/%s' % alias, node)
            
            for path in mypaths:
                score = score + simple_path_probability(path, SG)
            #normalize the score to a probability range?    
            linkedin_to_source[node] = score
    
    return linkedin_to_source


def full_score(G, SG, alias):
    results_dict = {}
    results = []
    linkedin_to_source = source_graph_score(G, SG, alias)

    # for each entity(node) that is not a source node calculate the score:
    for node in G.nodes():
        score = 0
        if G.node[node]['root'] != '/':
            # score = linkedin_to_source[G.node[node]['root']] * G.get_edge_data( G.node[node]['root'], node)['weight']
            score = linkedin_to_source.get(G.node[node]['root'], 0) * G.get_edge_data(G.node[node]['root'], node)[
                'weight']
           
            results.append((G.node[node]['value'], G.node[node]['node_type'], score))
            ######################
            #####add_score value to the node#####
            G.node[node]['score'] = score
            #####################################
            #    keep only the unique results:
    for result in results:
        if result[0] not in results_dict.keys():
            results_dict[result[0]] = {'node_type': result[1], 'score': result[2]}
        else:
            if result[2] > results_dict[result[0]]['score']:
                results_dict[result[0]]['node_type'] = result[1]
                results_dict[result[0]]['score'] = result[2]

    # turn it to tuple:
    results = [(k, v) for k, v in results_dict.items()]

    # sort
    results.sort(key=lambda result: result[1]['score'], reverse=True)

    return results


def simple_path_probability(path, SG):
    # probability rule: first step * (1), second step * (1/4), third step * (1/9)....
    path_probability = 0.0

    for n in range(len(path) - 1):

        if n == 0:
            path_probability = SG.get_edge_data(path[n], path[n + 1])['weight']
        else:
            path_probability = path_probability * (SG.get_edge_data(path[n], path[n + 1])['weight'] / (n + 1) ** 2)

    return path_probability



'''
This function isn't used, was implemented to add location entities to a linkedin retrieved profile because 
contextScouts api initially didn't retrieve location entities
'''
def addLinkedinLocationName(alias, G, url):
    with open('json/name and location.json', 'r') as f:
        data = json.load(f)

    if bool(data[alias]):
        for field in data[alias]:
            if field == 'location':
                loc = location(str(data[alias]['location']))
                for key in loc.keys():
                    if key == 'probability':
                        continue
                    if bool(loc[key]):
                        G.add_edge(url, url + "/" + key, weight=loc['probability'], edge_type='entity')
                        G.add_node(url + "/" + key, value=loc[key], label=loc[key], node_type=key, root=url)
            elif field == 'firstName':
                G.add_edge(url, url + "/" + field, weight=1, edge_type='entity')
                G.add_node(url + "/" + field, value=data[alias][field], label=data[alias][field], node_type='firstName',
                           root=url)
            elif field == 'secondName':
                G.add_edge(url, url + "/" + field, weight=1, edge_type='entity')
                G.add_node(url + "/" + field, value=data[alias][field], label=data[alias][field],
                           node_type='secondName', root=url)
            elif field == 'fullName':
                G.add_edge(url, url + "/" + field, weight=1, edge_type='entity')
                G.add_node(url + "/" + field, value=data[alias][field], label=data[alias][field], node_type='fullName',
                           root=url)
            else:
                continue


'''
Similarly to printit, draw a graph. Colour notation is different and was preffered for debugging purposes
'''
def testprintit(G):
    my_label = {}
    mycolorlist = []
    
    myedgelist = G.edges()[:]

    plt.figure(3, figsize=(38, 32))

    # we can use the same pos for printing subgraphs
    pos = nx.fruchterman_reingold_layout(G)
    # pos=nx.shell_layout(G)
    # Add custom labels
    for node in G.nodes():
        if 'label' in G.node[node].keys():
            my_label[node] = G.node[node]['label']

    nx.draw_networkx(G, pos=pos, labels=my_label, node_size=3000, with_labels=True, node_color='r', alpha=0.5)

    for node in G.nodes():
        try:
            if G.node[node]['root'] == "/":
                mycolorlist.append(node)
        except:
            continue

    nx.draw_networkx_nodes(G, pos=pos, nodelist=mycolorlist, node_size=3000, node_color='r', with_labels=True,
                           alpha=0.7)
    nx.draw_networkx_edges(G, pos=pos, edgelist=myedgelist, edge_color='g', with_labels=True, alpha=0.5, width=5)

    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)



# inkedIn('david-jones-86471684',New)
'''
The following two function aren't used. They were implemented in order to prune the graph from the not relevanet
entities, mainly for visualization purposes.
'''
def cut_not_relevant_nodes_dammy(G,results):

    keep_these_nodes = {}
    for result in results:
        if result[1]['score'] > 0.2:
            keep_these_nodes[result[0]]=False
    for node in G.nodes(data=True):
        if G.node[node[0]]['value'] in keep_these_nodes.keys():
                keep_these_nodes[G.node[node[0]]['value']]=True
        else:
            G.remove_node(node[0])
            

def cut_not_relevant_nodes(G,results):

    keep_these_nodes = {}
    for result in results:
        if result[1]['score'] > 0.5:
            keep_these_nodes[result[0]]=False
    for node in G.nodes(data=True):
        if G.node[node[0]]['value'] in keep_these_nodes.keys():
            if (G.node[node[0]]['root'] != '/') and (keep_these_nodes[G.node[node[0]]['value']]==False) :
                keep_these_nodes[G.node[node[0]]['value']]=True
            elif (G.node[node[0]]['root'] != '/') and (keep_these_nodes[G.node[node[0]]['value']]==True):
                G.remove_node(node[0])    
        else:
            G.remove_node(node[0])


''' 
refreshes the lists that are used to store temporary information during the graph generation process
'''      
def refresh_lists():
    global full_contact_list, link_scan_list, profile_list, redirected_list,myedgelist,searched_github_profiles
    full_contact_list.clear()
    link_scan_list.clear()
    profile_list.clear()
    redirected_list.clear()
    myedgelist.clear()
    searched_github_profiles.clear()


def grow_linkedin_graph(alias, G, SG, New):
    linkedIn(alias, New)
    graphGeneration(G, New)
    source_graph(G, SG)

    return full_score(G, SG, alias)


'''
THIS is the main calling function for creating the graph and exporting the scores. It makes a sequence of 
function calls for that reason. It exports the scores of relatedness for every entity (entity node) in the graph.
Scores are sorted and duplicates has been removed
'''

def final_graph(alias, path=None):
    G = nx.Graph()
    G2 = nx.Graph()
    SG = nx.Graph()
    New = nx.Graph()
    #####add 'score' attribute to all graphs#############
    nx.set_node_attributes(G,'score',0.0)  
    nx.set_node_attributes(G2,'score',0.0)  
    nx.set_node_attributes(SG,'score',0.0)  
    nx.set_node_attributes(New,'score',0.0)  
    
    refresh_lists()
    edgelist = []    
    
    fullname = ''
    gh_exists = False
    gh_score = 0.0

    results = []
    gh_graph_list = []

    original_location = {'country': '',
                         'state': '',
                         'city': ''}

    results = grow_linkedin_graph(alias, G, SG, New)


    for entity in results:
        if 'github' in entity[0]:
            if gh_score < entity[1]['score']:
                gh_score = entity[1]['score']
                gh_exists = True
        elif entity[1]['node_type'] == 'fullName':
            fullname = entity[0]
        elif entity[1]['node_type'] == 'country':
            original_location['country'] = entity[0]
        elif entity[1]['node_type'] == 'state':
            original_location['state'] = entity[0]
        elif entity[1]['node_type'] == 'city':
            original_location['city'] = entity[0]

    if ((gh_exists == False) or (gh_score < 0.5)):

        try:
            data = openfile('gh_profiles/%s' %fullname)
        except:
            loadGithubProfiles(fullname, original_location)
            data = openfile('gh_profiles/%s' %fullname)
            
        if data:
            
            #adding a dammy github profile in searched_gh_profile list in order to stop 
            #the algorithm to grow more github profiles that it can possibly find
            searched_github_profiles.append('dammy')
            
            global myedgelist    
            edgelist = list(myedgelist)
            gh_edge_list = []
            max_gh_graph_score = 0
            
            for profile in data:
                myedgelist = []
                
                G2.clear()
                New.clear()
                SG.clear()
                G_copy = nx.Graph()
                G_copy =  G.copy()
                SG_copy = nx.Graph()
    
                ghuserLoad(profile,New)
                graphGeneration(G2,New)
                New = G2.copy()
    
                addToGraph(G_copy,New)
                source_graph(G_copy,SG)
                SG_copy = SG.copy()
                source_nodes_score = source_graph_score(G,SG,alias)
    
                gh_alias = profile['url'].split('/')[-1]
                gh_graph_score = source_nodes_score['github/'+gh_alias.lower()]
                
    
                gh_graph_list.append((G_copy, SG_copy, gh_graph_score,profile))
                
                
                
                if max_gh_graph_score < gh_graph_score:
                    max_gh_graph_score = gh_graph_score
                    #gh_edge_list = []
                    gh_edge_list = list(myedgelist)
                        
                            
            for edge in gh_edge_list:
                edgelist.append(edge)
                
            #myedgelist = []
            myedgelist = list(edgelist)
            
            best_gh = max(gh_graph_list, key=itemgetter(2))
            
         
            
            ###if the gh_score is high enough, append the relevant skills
            if best_gh[2] > 0.5:
                ###passing to add_skills the graph and the data corresponding to the relevant github profile###            
                add_skills(best_gh[0],best_gh[3])
            
            G.clear()
            SG.clear()
            # G = G.copy (best_gh[0] corresponds to G.copy)
            # SG = SG.copy (best_gh[1] corresponds to SG.copy())
            G = best_gh[0]
            SG = best_gh[1]
            
            results = full_score(best_gh[0],best_gh[1],alias)
                
    #####debugging#####    
    global SSG,GG
    SSG = SG.copy()
    GG = G.copy()
    ###################

    #uncomment the following line if you're using an iPython console in order to see the visualization of the graph
    #printit(G)
   

    if path != None:
        data = json_graph.node_link_data(G)
        with open(path, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=True)

    return results



