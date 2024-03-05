import unittest
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scraper.spiders.amazon import AmazonSpider
from dotenv import load_dotenv
load_dotenv()


class AmazonSpiderTest(unittest.TestCase):
    def setUp(self):
        self.crawler_process = CrawlerProcess(get_project_settings())

    def test_spider(self):
        self.crawler_process.crawl(AmazonSpider,
                                   url='https://www.amazon.com/Apple-iPhone-11-64GB-Unlocked/dp/B07ZPKZSSC',
                                   job_id='123')
        
        self.crawler_process.start()  # The script will block here until the crawling is finished


if __name__ == '__main__':
    unittest.main()
