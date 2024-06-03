import logging

import scrapy
from scrapy.http import HtmlResponse, Request
from pushing.items import PushingItem


class PushSpider(scrapy.Spider):
    name = "push"
    allowed_domains = ["book.douban.com"]
    start_urls = ["https://book.douban.com/tag/?view=type&icn=index-sorttags-all"]
    base_url = "https://book.douban.com"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Cookie": 'bid=McvS1WhXwpM; _pk_id.100001.3ac3=b78b95d4902b9673.1717198454.; __utmc=30149280; __utmz=30149280.1717198454.1.1.utmcsr=cn.bing.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utmc=81379588; __utmz=81379588.1717198454.1.1.utmcsr=cn.bing.com|utmccn=(referral)|utmcmd=referral|utmcct=/; _vwo_uuid_v2=D93CC7778B9358D3134BF96E75DCEF268|f19a958d8512e501c35ca3cce7774def; push_noty_num=0; push_doumail_num=0; __utmv=30149280.28088; ct=y; viewed="4913064_36328704_35031587_34432750_20421947_36457094"; dbcl2="280881279:180b7JRfJpI"; ck=pu_0; ap_v=0,6.0; frodotk_db="066a8a71663e79ee133f9f5432bb6dca"; __utma=30149280.980919312.1717198454.1717234634.1717247773.5; __utmt_douban=1; __utmb=30149280.1.10.1717247773; __utma=81379588.900987245.1717198454.1717234634.1717247773.5; __utmt=1; __utmb=81379588.1.10.1717247773; _pk_ref.100001.3ac3=%5B%22%22%2C%22%22%2C1717247773%2C%22https%3A%2F%2Fcn.bing.com%2F%22%5D; _pk_ses.100001.3ac3=1'
    }
    logger = logging.getLogger()

    def parse(self, response: HtmlResponse, **kwargs):
        # a_tag = response.xpath("//div[@class='article']//table[@class='tagCol']//a/@href").extract()
        index = 0
        a_tag = [f"/tag/小说", f"/tag/余华"]
        for a_tag_href in a_tag:
            tag_url = f"{self.base_url}{a_tag_href}"
            logging.debug(f"###第{index + 1}个 tag url {tag_url} ###")
            item = PushingItem()
            item["tag_url"] = tag_url
            item["tag_index"] = index
            item["tag"] = a_tag_href
            yield Request(url=tag_url, callback=self.__parse_tag, dont_filter=True, cb_kwargs={'item': item})
            index += 1

    def __parse_tag(self, res: HtmlResponse, **kwargs):
        item = kwargs['item']
        tag_url = item['tag_url']
        logging.debug(f"#### page: {res.url} ####")
        page = 0
        start = page * 20
        url = f"{tag_url}?start={start}&type=T"
        yield Request(url=url, callback=self.__find, meta={'page': 0}, dont_filter=True, cb_kwargs={"item": item})

    def __find(self, res: HtmlResponse, **kwargs):
        item = kwargs["item"]
        current_page = int(res.url.split("=")[1].split("&")[0])
        next_page = current_page + 20
        page_index = int(next_page / 20) - 1
        item["page_index"] = page_index
        not_found = res.xpath("//div[@id='subject_list']//p/text()").extract()
        if len(not_found) > 0 and not_found[0] == "没有找到符合条件的图书":
            self.logger.info(f"### Found url {res.url}")
            return
        else:
            self.logger.info(f"# Did not find, keep generating url -> {item['tag_url']}?start={next_page}&type=T")
            yield Request(url=f"{item['tag_url']}?start={next_page}&type=T", callback=self.__find, dont_filter=True,
                          cb_kwargs={"item": item})
        item["page_url"] = res.url
        yield Request(url=res.url, callback=self.__parse_every_page, dont_filter=True, cb_kwargs={"item": item})
        self.logger.info(f"### res.url {res.url}")

    def __parse_every_page(self, res: HtmlResponse, **kwargs):
        item = kwargs['item']
        final_href = res.xpath("//div[@class='article']//ul//div[@class='info']/h2/a/@href").extract()
        for i in final_href:
            item["pushing_url"] = i
            logging.debug(f"### tag: {item['tag_url']}, page: {item['page_url']}, pushing: {i}")
            yield item
