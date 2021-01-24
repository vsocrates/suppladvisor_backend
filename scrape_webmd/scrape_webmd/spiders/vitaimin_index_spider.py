import scrapy
import json

from scrape_webmd.items import VitaminIndexItem


class VitaminIndexSpider(scrapy.Spider):
    """
    Scrapes out all the vitamins/supplements that WebMD has info on.
    Generates series of json files containing all the links.
    """
    name = "vitamin_index"

    custom_settings = {
        'ITEM_PIPELINES': {
            'scrape_webmd.pipelines.ScrapeWebmdPipeline': 300
        }
    }

    def start_requests(self):
        # generates list of all "vitamin index" urls to scrape from webmd
        base_url = 'https://www.webmd.com/vitamins/alpha/'
        alphabet = 'abcdefghijklmnopqrstuvwxyz0'
        urls = [base_url+letter for letter in alphabet]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        index_letter = response.url.split("/")[-1]

        # parse out all webmd vitamin index urls from the response.
        urls = response.css('ul.vitamins-list li a::attr(href)').getall()

        url_dict = {}
        for url in urls:
            vitamin = url.split("/")[-1]
            url_dict[vitamin] = url

        # yield the VitaminIndexItem
        yield VitaminIndexItem(index_letter=index_letter, url_dict=url_dict)
