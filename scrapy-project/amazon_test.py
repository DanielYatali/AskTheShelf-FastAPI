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
                                   url='https://www.amazon.com/Control-360-degree-Rotating-Rechargeable-Birthday/dp/B0C8TJQ18N/ref=sr_1_1_sspa?crid=3ODKFAFPHMBQK&dib=eyJ2IjoiMSJ9.D4RBeq_isG1bEPjxsftQVeBCbj_hjrVg9npYwM-bi3R3hsbf-L2sIHEJz3K6KPjWmdTgWKXWW0ZoYVWTYTsGf3V3p0CNCgbXqE3uqDwfYYUR2HojID0agwkPtBkOJ8PF7NCNwZd3tqhcBDiF39lVoBEqKF6nmaBBu2oO1bEJulA4EQZDSyh76UA5jJViPO1Tk1wBJUA2tRZCRu_MAbFCnw3HI2xdSv2jPoRMAiNj44l4E0zN08qCCkscEiFzSK6wgaKa7fzlXlp6djToTsqxT4g6V9sDCEvUTdN2lJ5wZaA.9zBnBr4ypugW3gFcns4nYLqJI8YaFAjoZlF2MTcPoRs&dib_tag=se&keywords=toys&qid=1710606080&sprefix=%2Caps%2C134&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1"',
                                   job_id='123')
        
        self.crawler_process.start()


if __name__ == '__main__':
    unittest.main()
