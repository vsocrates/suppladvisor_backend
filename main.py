from flask import request, url_for
from flask_api import FlaskAPI, status, exceptions

from scrape_webmd.scrape_webmd.spiders.vitamin_details_spider import VitaminDetailsSpider
import scrapyscript

import pandas as pd
# from sodapy import Socrata
import nltk
import re

import requests
import json


app = FlaskAPI(__name__)
app.config["webmd_vitamin_index"] = json.load(open("scrape_webmd/webmd_vitamin_index.json", 'r'))

#TODO: Write tests

@app.route("/", methods=['GET', 'POST'])
def notes_list():
    """
    List or create notes.
    """
    if request.method == 'POST':
        note = str(request.data.get('text', ''))
        idx = max(notes.keys()) + 1
        notes[idx] = note
        return note_repr(idx), status.HTTP_201_CREATED

    # request.method == 'GET'
    return [note_repr(idx) for idx in sorted(notes.keys())]




def matches(text):
    """
    Helper function to calculate number of words from a list that match words in a sentence.
    """    
    return sum(word in text.lower() for word in keywords)


def get_dsldID(name, brand):
    """
    Gets DSLD ID from the DSLD database using info from amazon product page
    
    Input: 
        name of the product (e.g., "Professional Botanicals Cal/Mg + Boron - Vegan Formulated to Support Bone Health and Healthy Skin, Teeth and Nails Calcium Magnesium and Boron 90 Vegetarian Capsules")
        brand (e.g., "Professional Botanicals")
    Reference: https://www.amazon.com/Professional-Botanicals-Cal-Boron-Formulated/dp/B00512IDV0
    Output: DSLD ID string
    """   
    #Search DSLD for all supplements made by the provided brand
    query = '"' + brand + '"'
    response = requests.get("https://datadiscovery.nlm.nih.gov/resource/wp6t-qxsk.json?$where=brand_name LIKE"+query).json()

    dsld_id = []
    brand_name = []
    product_name = []

    for x in response:
        dsld_id.append(x['dsld_id'])
        brand_name.append(x['brand_name'])
        product_name.append(x['product_name'])

    dsld_lbl_df = pd.DataFrame() # create empty dataframe 
    dsld_lbl_df['dsld_id'] = dsld_id 
    dsld_lbl_df['brand_name'] = brand_name
    dsld_lbl_df['product_name'] = product_name ###add new columns based off lists

    tokens = nltk.word_tokenize(name)
    texts = [str(i) for i in dsld_lbl_df.product_name.tolist()]

    keywords = [i.lower() for i in tokens]

    regex_name = max(texts, key=matches)

    #here, if I have several matches, I just take the one on the top of the list
    dsld_id = dsld_lbl_df[(dsld_lbl_df["product_name"] == regex_name)].head(n=1).dsld_id.values[0]

    return dsld_id


def get_ingredients(dsld_id):
    """
    Gets ingredients using DSLD ID
    
    Input: dsld_id string
    Output: list of ingredients
    """
    query = '"' + '%' + dsld_id + '%' + '"'

    response = requests.get("https://datadiscovery.nlm.nih.gov/resource/btg5-fr69.json?$where=sample_dsld_ids LIKE "+query).json()
    response2 = requests.get("https://datadiscovery.nlm.nih.gov/resource/btg5-fr69.json?$where=sample_dsld_ids_in_nhanes LIKE "+query).json()
    
    ingredients = []

    for product in response:
        ingredients.append(product['ingredient_name'])
    for product in response2:
        ingredients.append(product['ingredient_name'])

    return ingredients




# This is more of a test endpoint for getting single vitamins/supplements.
@app.route("/scrape_webmd/<vitamin>", methods=['GET'])
def scrape_webmd(vitamin):
    """
    Input: vitamin name as string
    Output: scraped output from webmd (if match is found), formatted as JSON
    """
    # get webmd url for vitamin
    vitamin_index = app.config["webmd_vitamin_index"]
    url = get_webmd_url(vitamin, vitamin_index)

    # assemble into lists to pass into get_vitamin_details
    vitamins = [vitamin,]
    urls = [url,]

    vitamin_details = get_vitamin_details(vitamins, urls)
    return vitamin_details


# Use this endpoint.
@app.route("/bulk_scrape_webmd/", methods=['POST'])
def bulk_scrape_webmd():
    """
    Input: JSON containing list of vitamins.
    Output: scraped output from webmd (if match is found), formatted as JSON

    Example post input:
    {"vitamins": ["abuta", "fake-stuff", "beer", "cod-liver-oil"]}
    """
    # parse input json
    try:
        json_data = request.get_json()
        vitamins = json_data.get('vitamins')
    except:
        return {"error": "Could not read input data as JSON."}
    if not vitamins:
        return {"error": "Improperly formatted input JSON. Please make sure input json has a 'vitamins' key."}

    # get webmd url for vitamin
    vitamin_index = app.config["webmd_vitamin_index"]
    urls = [get_webmd_url(vitamin, vitamin_index) for vitamin in vitamins]

    vitamin_details = get_vitamin_details(vitamins, urls)
    return vitamin_details


def get_webmd_url(vitamin, vitamin_index):
    """
    Input: vitamin name as string
    Output: webmd url for vitamin
    """
    # TODO: Make this matching a bit more sophisticated than just cleaning and looking for a direct match.
    cleaned_vitamin = vitamin.lower().replace(' ', '-')
    url = vitamin_index.get(cleaned_vitamin, None)
    return url


def get_vitamin_details(vitamins, urls):
    """
    Input: two lists of strings
    Output: dictionary
    """
    # TODO: Potentially cache or save some of this data to a db because making calls on the fly can be slow.

    # TODO: Handle lookups of vitamins/supplements that don't appear to be in webMD.

    # TODO: Add aliases for vitamins/supplements (Ex. Other names, generic names, brand names, etc.).
    # Not sure how necessary this is because we're processing ingredients through NIH DSLD database/API first.

    # any vitamins without links are filtered out before scraping call.
    error_vitamin_details = {}
    remove_list = []

    for idx, url in enumerate(urls):
        if not url:
            error_vitamin_details[vitamins[idx]] = {"error": "That supplement or vitamin was not found in WebMD."}
            remove_list.append(url)

    for url in remove_list:
        urls.remove(url)

    # create scraping job, pass in scrape_urls via kwargs
    # run job using processor
    vitamin_details_job = scrapyscript.Job(VitaminDetailsSpider, scrape_urls=urls)
    processor = scrapyscript.Processor(settings=None)
    vitamin_details_list = processor.run([vitamin_details_job])

    # merge vitamin details list and errors vitamin details
    vitamin_details_list.append(error_vitamin_details)
    vitamin_details = {k: v for vitamin_dict in vitamin_details_list for k, v in vitamin_dict.items()}
    return vitamin_details

if __name__ == "__main__":
    app.run(debug=True)
