import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class FLSpider(scrapy.Spider):
    name = 'fl'
    allowed_domains = ['fl.ru']
    start_urls = ['https://www.fl.ru/rss/all.xml']

    def parse(self, response):
        for item in response.xpath('//item'):
            data = {
                'title': item.xpath('title/text()').get(),
                'link': item.xpath('link/text()').get(),
                'description': item.xpath('description/text()').get(),
                'guid': item.xpath('guid/text()').get(),
                'category': item.xpath('category/text()').get(),
                'pubDate': item.xpath('pubDate/text()').get()
            }
            yield data


def start_crawl():
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(FLSpider)
    process.start()


if __name__ == "__main__":
    start_crawl()
