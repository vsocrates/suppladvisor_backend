# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapeWebmdItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class VitaminIndexItem(scrapy.Item):
    index_letter = scrapy.Field()
    url_dict = scrapy.Field()

    def __repr__(self):
        """
        Clip the url dictionary to first 500 characters
        """
        clipped_dictionary_str = str(self['url_dict'])[:300] + " ... }"
        return repr({"clipped_dict": clipped_dictionary_str })
