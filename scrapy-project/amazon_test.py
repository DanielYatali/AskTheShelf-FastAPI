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
                                   url='https://www.amazon.com/SAMSUNG-Smartphone-Unlocked-Android-Titanium/dp/B0CMDL3H3P/ref=sr_1_1_sspa?crid=2GVX8BGXGSZVO&dib=eyJ2IjoiMSJ9.RB1RrI06z1GAWv1PYg4d8FpoKxBz0OtVatXoltQWfdtypiGihKGjTGAAE7m6Gum4i_RNdMaQZQLBAg_YumkB78_U1o4pyqD3GU13f42l936LiuKUXpeTnZpuHOj7KHmATBurKY6oxrxhjVGc5b06A1ZYc7Za8NX-Jw8gXJmpurlD8spT6Iq1kREKayNnb-Ij7ob0T9E5V3Q5gUgKrvTTSeuHVcmRLo0lYatiW7HUJww.JpEENS8qB5OgYywPmVHPTRzXUKFfAnziHbogLVI8WgU&dib_tag=se&keywords=samsung%2Bphone&qid=1710473090&sprefix=samsung%2Bphone%2Caps%2C179&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1',
                                   job_id='123')
        
        self.crawler_process.start()


if __name__ == '__main__':
    unittest.main()
