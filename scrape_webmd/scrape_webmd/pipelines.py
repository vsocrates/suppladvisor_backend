# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
import logging



class ScrapeWebmdPipeline:
    def open_spider(self, spider):
        # create "master" dictionary of all vitamin index urls.
        self.vitamin_index_url_dict = {}

    def close_spider(self, spider):
        # dump the "master" dictionary of all webmd vitamin index urls to json file
        with open('webmd_vitamin_index.json', 'w') as f:
            json.dump(self.vitamin_index_url_dict, f, sort_keys=True, indent=4)
            logging.log(logging.DEBUG, f'Saved all WebMD vitamin index urls to json file {f.name}')

        # TODO: potentially dump this in a database in the future instead of saving it to json file.

    def process_item(self, item, spider):
        # merge in url dict for the parsed item into the "master dictionary"
        url_dict = item['url_dict']
        merged_url_dict = {**url_dict, **self.vitamin_index_url_dict}
        self.vitamin_index_url_dict = merged_url_dict

        logging.log(logging.DEBUG, 'Saving all WebMD vitamin index urls for letter: {}'.format(item['index_letter']))
        return item
