import unittest
from scrapy.http import HtmlResponse
from scraper.spiders.amazon import AmazonSpider


class MySpiderTest(unittest.TestCase):
    def setUp(self):
        self.spider = AmazonSpider

    def test_parse_method(self):
        html = ''
        with open('test.html', 'r') as file:
            html = file.read()
        html = bytes(html, 'utf-8')
        fake_response = HtmlResponse(url='http://example.com', body=html, encoding='utf-8')

        # Call the 'parse' method of your spider and pass the fake response object
        result = list(self.spider.parse(self.spider, fake_response))

        # Assertions to check if the parse method behaves as expected
        self.assertEqual(len(result), 1)  # Replace with your expected conditions
        # ... more assertions ...


if __name__ == '__main__':
    unittest.main()
