import scrapy
import json

from w3lib.html import remove_tags


class VitaminDetailsSpider(scrapy.Spider):
    """
    Scrapes out details from webMD on vitamin.
    """
    name = "vitamin_details"

    def __init__(self, *args, **kwargs):
        # take custom set of scrape_urls as input
        super(VitaminDetailsSpider, self).__init__(*args, **kwargs)
        self.scrape_urls = kwargs.get('scrape_urls')

    def start_requests(self):
        # pass in list of all "vitamin information" urls to scrape from webmd.
        for url in self.scrape_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # parse out all relevant info.
        vitamin = response.url.split('/')[-1]

        # TODO: Potentially try and add in more sophisticated parsing.
        # Currently difficult because the webMD lacks consistent structure in its html in these tags.
        side_effects = self.clean_html(response.css('div#tab-3 div.tab-text div.inner-content').get())
        interactions = self.clean_html(response.css('div#tab-4 div.tab-text div.inner-content').get())
        dosing = self.clean_html(response.css('div#tab-5 div.tab-text div.inner-content').get())
        references = response.css("div.references-content ul li::text").getall()

        vitamin_details = dict()
        vitamin_details[vitamin]= {
            "side_effects": side_effects,
            "interactions": interactions,
            "dosing": dosing,
            "references": references
        }

        # return dictionary
        return vitamin_details

    def clean_html(self, html_str):
        """
        removes tags, strips text, rstrips text,
        replace or strip certain special characters
        """

        # TODO: add in more sophisticated cleaning.
        cleaned_html = remove_tags(html_str).strip().rstrip()
        cleaned_html = cleaned_html.replace('?\r\n', '')
        cleaned_html = cleaned_html.replace('\r', '')
        cleaned_html = cleaned_html.replace('\n', '')
        cleaned_html = cleaned_html.replace('&amp;', '& ')
        return cleaned_html
