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
                                   url='https://www.amazon.com/Lenovo-IdeaPad-Display-Processor-82K20015US/dp/B08YKHGKTV/ref=cm_cr_arp_d_product_top?ie=UTF8&th=1',
                                   job_id='123')
        
        self.crawler_process.start()


if __name__ == '__main__':
    unittest.main()
