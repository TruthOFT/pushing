# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
import logging

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import redis


class PushingPipeline:

    def __init__(self):
        self.__r = redis.Redis(
            host="127.0.0.1",
            port=6379
        )

    def process_item(self, item, spider):
        url = item["pushing_url"]
        tag_url = item["tag_url"]
        tag_index = str(tag_url).find("tag")
        tag = tag_url[tag_index::]
        logging.debug(f"lpushing---->第{item['tag_index']}个{item['tag_url']} 下的 第{item['page_index']}下的{url}")
        self.__r.lpush("books:start_urls", json.dumps({'tag': tag, 'url': url}, ensure_ascii=False))
        return item

    def close_spider(self, spider):
        self.__r.close()
