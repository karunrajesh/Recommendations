#!/usr/bin/env python
# coding: utf-8


# Import Packages
from googleapiclient.discovery import build
import datetime as dt
from bs4 import BeautifulSoup
import requests
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import pickle
import difflib
import pandas as pd
import re
import random
import time


# The flow should work like this:
# 
# 1) Anime is google scraped since MAL seems to put some random number in the url
# 
# 2) Get MAL link, scrape everything from this page that is of interest (name, categories, episode count?)
# 
# 3) Add /userrecs to the MAL url and scrape the user recommendations
# 
# anime --> google_search --> get_name --> get_description --> episode_count --> get_cat --> MAL score --> get_stream --> get_recs 
# 
# How should it be stored?
# 
# - Dictionary of list of lists: {Anime: [description, episode count, year, [categories], MAL Score,[streaming platforms], [recommended anime]]}
# 
# Questions
# 
# - Should I just use the streaming anime list (~1200 anime) to build my network? It'll be extremely large, maybe too large?
# 
# - Maybe start small and go from there for proof of concept
# 
# Batch Processing:
# 
# - First, get the MAL urls from google searches through 100 per batch processing, then urls with names in dictionary, pickle full dictionary to have at hand
# 
# - Second, go through MAL urls in 100 per batch and scrape MAL site for information and recommendations now that all anime should be key in dictionary (avoid double counting anime from recommendations that are already in anime list)


def time_log(func):
    def wrapper(*args, **kwargs):
        time_start = dt.datetime.now()
        result = func(*args, **kwargs)
        time_end = dt.datetime.now()
        print(f"Function Took: {time_end - time_start}")
        return result
    return wrapper

# Gets google search page, given search term (CHANGED 01/17)
# Example of google_search usage
#results = google_search("Attack on Titan MAL", my_api_key, my_cse_id)
@time_log
def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    url = res["items"][0]["link"]
    #url = url + "/userrecs"
    return url
        

# Scrapes the description page from the MAL Details page for the given anime
# Example: 
"""
link = "https://myanimelist.net/anime/40834/Ousama_Ranking"
resp = requests.get(link)
parser = 'html.parser'
soup = BeautifulSoup(resp.content, parser)
description = soup.select(".pb16~ p")
print(description[0].text)
"""
@time_log
def check_if_anime(link):
    #check_list = ["myanimelist.net/anime"]
    if("myanimelist.net/anime" in link):
        return True
    else:
        return False

@time_log
def get_description(link):
    resp = requests.get(link)
    parser = 'html.parser'
    soup = BeautifulSoup(resp.content, parser)
    description = soup.select(".pb16~ p")
    text_description = description[0].text
    #print(text_description)
    return text_description


# Scrapes the recommendation page from the MAL User Recommendation page for the given anime (CHANGED 01/17/21)
#@time_log
def get_name(link):
    resp = requests.get(link)
    parser = 'html.parser'  # or 'lxml' (preferred) or 'html5lib', if installed
    soup = BeautifulSoup(resp.content, parser)
    if(soup.select(".title-inherit")):
        name = soup.select(".title-inherit")
    else:
        name = soup.select(".h1_bold_none strong")
    
    nm = name[0].text
    #print(nm)
    return nm


# Gets the number of episodes for the anime
@time_log
def get_anime_details(link):
    resp = requests.get(link)
    parser = 'html.parser'  # or 'lxml' (preferred) or 'html5lib', if installed
    soup = BeautifulSoup(resp.content, parser)
    # get everything from information section
    info = [".spaceit_pad:nth-child({})".format(i) for i in range(6, 30)]
    cat = [soup.select(d) for d in info]
    #ct = cat[0].text
    episodes = ''
    genres = ''
    season = ''
    for item in cat:
        if(item):
            print(item[0].text)
            if("Episode" in item[0].text):
                sentence = ' '.join(item[0].text.split())
                episodes = extract_info(sentence, "Episodes")
            if("Genre" in item[0].text):
                sentence = ' '.join(item[0].text.split())
                genres = extract_info(sentence, "Genre")
            if("Premiered" in item[0].text):
                sentence = ' '.join(item[0].text.split())
                season = extract_info(sentence, "Premiered")
            # Store theme for case when genre isn't available
            if("Theme" in item[0].text):
                sentence = ' '.join(item[0].text.split())
                themes = extract_info(sentence, "Theme")
    # check if anime has genre listed on MAL, if not use themes instead
    if(genres == ''):
        genres = themes
    return [episodes, genres, season]


def extract_info(sidebar_str, info_type):
    if(info_type == "Episodes"):
        cleaned_str = re.findall(r"Episodes: (.*)$", sidebar_str)[0]
        return cleaned_str
    if(info_type == "Genre"):
        if("Genres:" in sidebar_str):
            cleaned_str = re.findall(r"Genres: (.*)$", sidebar_str)[0]
            genre_list = cleaned_str.split(",")
            updated_list = [re.findall(r"([A-Z].*)[A-Z]", genre)[0] for genre in genre_list]
            return updated_list
        elif("Genre:" in sidebar_str):
            cleaned_str = re.findall(r"Genre: (.*)$", sidebar_str)[0]
            updated_list = [re.findall(r"([A-Z].*)[A-Z]", cleaned_str)[0]]
            return updated_list
        else:
            return ""
    if(info_type == "Theme"):
        if("Themes:" in sidebar_str):
            cleaned_str = re.findall(r"Themes: (.*)$", sidebar_str)[0]
            genre_list = cleaned_str.split(",")
            updated_list = [re.findall(r"([A-Z].*)[A-Z]", genre)[0] for genre in genre_list]
            return updated_list
        elif("Theme:" in sidebar_str):
            cleaned_str = re.findall(r"Theme: (.*)$", sidebar_str)[0]
            updated_list = [re.findall(r"([A-Z].*)[A-Z]", cleaned_str)[0]]
            return updated_list
        else:
            return ""
    if(info_type == "Premiered"):
        cleaned_str = re.findall(r"Premiered: (.*)$", sidebar_str)[0]
        return cleaned_str
    return "Nothing Found"
    

# Gets Anime List for Given Service
#@time_log
def get_stream(anime_name):
    if(difflib.get_close_matches(anime_name, stream.keys(), n = 1, cutoff = 0.8)):
        anime_match = difflib.get_close_matches(anime_name, stream.keys(), n = 1, cutoff = 0.8)[0]
        stream_services = stream[anime_match]
    else:
        stream_services = []
    #print(stream_services)
    return stream_services

                
# Gets the recommendations from other MAL users, needs to be >threshold to add recommendation
# Total_votes is the votes for those that have >= threshold, and then rec_links just takes up to the len of total_votes
@time_log
def get_rec_links(rec_url, threshold):
    resp = requests.get(rec_url)
    parser = 'html.parser'  # or 'lxml' (preferred) or 'html5lib', if installed
    soup = BeautifulSoup(resp.content, parser)
    votes = soup.select(".js-similar-recommendations-button strong")
    total_votes = [int(i.text) for i in votes if int(i.text)>=threshold]
    l = list()
    check = 0
    for link in soup.find_all('a', href=True):
        if(str(link['href']).startswith("/myrecommendations")):
            check = 1
            #print("I work")
        if(check == 1):
            if(link['href'] == "https://myanimelist.net/topanime.php"):
                break
            z = re.search("https://myanimelist\.net/anime/\d*/(.*)$", link['href'])
            if(z):
                if(link["href"] not in l):
                    l.append(link["href"])
    rec_links = l[0:len(total_votes)]
    rec_names = [[get_name(a), a] for a in rec_links]
    return rec_names


# Cleans url if it has any mistakes in it
#@time_log
def clean_url(url):
    if "?" in url:
        cleaned_url = re.findall(r"(.*)\?", url)
        return cleaned_url
    return url

def get_mal_sites(anime_list):
    ani_number = 0
    # Change save_state to save_state google api stopped at
    save_state = 8
    i_start = (save_state - 1) * 50
    for i in range(i_start, len(anime_list), 50):
        if(i == range(0, len(anime_list), 50)[-1]):
            short_anime_list = anime_list[i:len(anime_list)]
        else:
            short_anime_list = anime_list[i: i + 50]
        print(short_anime_list)
        for anime in short_anime_list:
            ani_recs = {}
            #if(ani_number % 50 == 0):
            #    print("Going to sleep")
            #    time.sleep(3600 - time.time() % 3600)
            anime_search = anime + " MyAnimeList"
            url = google_search(anime_search, my_api_key, my_cse_id)
            url = clean_url(url)
            if(check_if_anime(url)):
                #print(url)
                anime_name = get_name(url)
                anime_stream = get_stream(anime)
                ani_recs[anime_name] = [url,anime_stream]
                ani_number += 1
                print(anime_name, ani_number, save_state)
        pickle_list(ani_recs, "anime_mal_sites_{}.pickle".format(save_state))
        save_state += 1
    #return ani_recs

# Runner function
@time_log
def anime_runner(anime_list, ani_recs):
    full_recs = []
    for anime in anime_list:
        anime_search = anime + " MyAnimeList"
        url = google_search(anime_search, my_api_key, my_cse_id)
        #print(url)
        url = clean_url(url)
        #print(url)
        anime_name = get_name(url)
        anime_description = get_description(url)
        anime_episodes, anime_genres, anime_season = get_anime_details(url)
        #print(anime_episodes, anime_genres, anime_season)
        anime_stream = get_stream(anime)
        #Create separate list for the recommended list and then go through same process without get_recs to create profile for 
        recs_url = url + "/userrecs"
        anime_recs_url = get_rec_links(recs_url, 10)
        anime_recs = [name for name,url in anime_recs_url]
        #print(anime_recs)
        #break
        full_recs.extend(anime_recs_url)
        ani_recs[anime_name] = [anime_description, anime_episodes, anime_genres, anime_season, anime_stream, anime_recs]
    print(full_recs)
    for anime,url in full_recs:
        if anime not in ani_recs.keys():
            #print(anime)
            anime_description = get_description(url)
            anime_episodes, anime_genres, anime_season = get_anime_details(url)
            anime_stream = get_stream(anime)
            recs_url = url + "/userrecs"
            anime_recs_url = get_rec_links(recs_url, 10)
            anime_recs = [name for name,url in anime_recs_url]
            ani_recs[anime] = [anime_description, anime_episodes, anime_genres, anime_season, anime_stream, anime_recs]
    return ani_recs



# Pickle and store object
@time_log
def pickle_list(df, file_name):
    with open(file_name, 'wb') as handle:
        pickle.dump(df, handle, protocol=pickle.HIGHEST_PROTOCOL)


# ### NetworkX Function

# In[3]:


# Create anime networkx object 
@time_log
def create_ani_network(ani_recs):
    nx_obj = nx.Graph(ani_recs)
    #print("Fate Zero" in list(nx_obj.nodes()))
    #nx_obj.edges()
    #for edge in nx_obj.edges():
        #print(edge[0], edge[1])
        #print(ani_recs[edge[0]][edge[1]])
    #nx_obj.nodes['title'] = list(nx_obj.nodes())
    g = Network(height = 800, width = 800, notebook = True)
    #g.toggle_hide_edges_on_drag(False)
    #g.barnes_hut()
    g.from_nx(nx.Graph(ani_recs))
    g.set_options("""
    var options = {
      "nodes": {
        "font": {
          "size": 17,
          "background": "rgba(255,255,255,1)"
        }
      },
      "edges": {
        "color": {
          "inherit": true
        },
        "smooth": false
      },
      "interaction": {
        "hover": true,
        "keyboard": {
          "enabled": true
        },
        "navigationButtons": true
      },
      "physics": {
        "forceAtlas2Based": {
          "springLength": 100
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based"
      }
    }
    """)

    return g

# API and Search Keys
my_api_key = "AIzaSyBRvu5CNwemS1HV3IcQ1bcCnfS30yUaiEM"
my_cse_id = "7191dc5676ef525ac"

#ani_recs = dict()
### Reading in streaming list and creating anime_names list from that, decided to pickle to make process easier.
stream_list = pd.read_pickle(r'anime_streaming.pickle')
stream = {re.sub('\*|!|:|-|\+|\.|\?|\^|\$|\(|\)|\[|\]|\{|\}', '', x): v
     for x, v in stream_list.items()}

#ani_list = list(stream.keys())
#pickle_list(ani_list, 'anime_names.pickle')
ani_list = pd.read_pickle(r'anime_names.pickle')


get_mal_sites(ani_list)

#pickle_list(ani_recs, "anime_mal_sites.pickle")


# In[31]:


# Problem Children: My Hero Academia, Jojos
# My hero academia search term only pulls up season 3 result first for some reason, so manually input it
# For some reason, jojo's adds ?suggestion= into the url, manually input it
#url = google_search("Jojo's Bizzare Adventure MAL", my_api_key, my_cse_id)
#print(url)


# ## Anime Network Example 

# In[20]:


#g = create_ani_network(ani_recs)
#g.show("ex.html")


# ##  Pickling Objects

# In[ ]:


#pickle_list(ani_recs, "anime_recs.pickle")
#pickle_list(watch_on, "stream_service.pickle")


# In[ ]:


"""
Unused Function: 01/16/22

@time_log
def get_stream_service(url, offset):
    resp = requests.get(url)
    #search_term = ".css-1u7zfla a"
    search_term = ".e1qyeclq4 p"
    # get BeautifulSoup object
    soup = BeautifulSoup(resp.content, 'html.parser')
    # Get the titles of the user recommended animes
    links = soup.select(search_term)
    recs = [title.text for title in links]
    for i in range(50,offset+1,50):
        url = url + "?offset=" + str(i)
        resp = requests.get(url)
        # get BeautifulSoup object
        soup = BeautifulSoup(resp.content, 'html.parser')
        # Get the titles of the user recommended animes
        links = soup.select(search_term)
        recs.extend([title.text for title in links])
    return recs

# Creates anime recommendation list with given anime list
@time_log
def add_anime(anime_list, ani_recs):
    for anime in anime_list:
        anime_search = anime + " MAL"
        if(anime == "Boku no Hero Academia"):
            url = "https://myanimelist.net/anime/31964/Boku_no_Hero_Academia/userrecs"
        elif(anime == "JoJo no Kimyou na Bouken TV"):
            url = "https://myanimelist.net/anime/14719/JoJo_no_Kimyou_na_Bouken_TV/userrecs"
        else:
            url = google_search(anime_search, my_api_key, my_cse_id)
        rec_names = searchRecs(url, anime)
        ani_recs[anime] = rec_names
        print(anime, "Done")


# Gets categories (sports, slice of life, etc) of anime
@time_log
def get_category(link):
    resp = requests.get(link)
    parser = 'html.parser'  # or 'lxml' (preferred) or 'html5lib', if installed
    soup = BeautifulSoup(resp.content, parser)
    cat = soup.select("span+ a:nth-child(3)")
    ct = cat[0].text
    print(ct)
    return ct

@time_log
def searchRecs(res, anime):
    if(anime == "Boku no Hero Academia"):
        url = "https://myanimelist.net/anime/31964/Boku_no_Hero_Academia/userrecs"
    elif(anime == "JoJo no Kimyou na Bouken TV"):
        url = "https://myanimelist.net/anime/14719/JoJo_no_Kimyou_na_Bouken_TV/userrecs"
    else:
        url = res["items"][0]["link"]
        url = url + "/userrecs"
    #print("Step 0")
    rec_links = get_rec_links(url, 10)
    #print("Step 1")
    #print(rec_links)
    anime_name = get_name(url)
    
    # connect to webpage
    resp = requests.get(url)
    # get BeautifulSoup object
    soup = BeautifulSoup(resp.content, 'html.parser')
    # Get the titles of the user recommended animes
    #links = soup.select("#content div:nth-child(2) strong")
    #recs = [title.text for title in links]
    # Get the upvotes for the given recommendations
    #votes = soup.select(".js-similar-recommendations-button strong")
    # Only keep those that were upvoted at least 5 times
    #total_votes = [int(i.text) for i in votes if int(i.text)>=10]
    rec_names = [[get_name(a), a] for a in rec_links]
    #print("Step 2")
    #total_recs = rec_names[0:len(total_votes)]
    #ani_recs[anime_name] = rec_names
    return(rec_names)
    
    
crunch_list = get_stream_service("https://reelgood.com/source/crunchyroll", 600)
netflix_list = get_stream_service("https://reelgood.com/genre/anime/on-netflix", 100)
prime_list = get_stream_service("https://reelgood.com/genre/anime/on-amazon", 50)
funimation_list = get_stream_service("https://reelgood.com/source/funimation", 550)
hbo_list = get_stream_service("https://reelgood.com/genre/anime/on-hbo_max", 50)
hulu_list = get_stream_service("https://reelgood.com/genre/anime/on-hulu", 150)

url = "https://reelgood.com/source/crunchyroll"
resp = requests.get(url) 
offset = 600
#search_term = ".css-1u7zfla a"
#search_term = "p"
search_term = ".e1qyeclq4 p"
# get BeautifulSoup object
soup = BeautifulSoup(resp.content, 'html.parser')
# Get the titles of the user recommended animes
links = soup.select(search_term)
#print(links)
#print([title.text for title in links])
recs = [title.text for title in links]
for i in range(50,offset+1,50):
    url = url + "?offset=" + str(i)
    resp = requests.get(url)
    # get BeautifulSoup object
    soup = BeautifulSoup(resp.content, 'html.parser')
    # Get the titles of the user recommended animes
    links = soup.select(search_term)
    recs.extend([title.text for title in links])
    
print(recs)
#return recs
watch_on = dict()
streaming_list = [[crunch_list, "crunchyroll"],[netflix_list, "netflix"], [prime_list, "amazon prime"], [funimation_list, "funimation"], [hbo_list, "HBO"], [hulu_list, "hulu"]]
for stream_service in streaming_list:
    create_stream_list(g, watch_on, stream_service[0], stream_service[1])
    
watch_on
#reel good doesn't have a lot of anime on it, 
#so get more comprehensive lists (probably just for netflix, crunchyroll, and funimation)
"""

