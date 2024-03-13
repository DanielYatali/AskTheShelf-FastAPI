import datetime
import logging
import os
import re
from random import randint
from app.models.job import Job
from app.models.product import Product
from app.schemas.schemas import job_serializer, product_serializer
import json
import scrapy

# import the env variables
from dotenv import load_dotenv

load_dotenv()


def safe_extract(response_or_selector, query, query_type='css', extract_first=True, default_value=None):
    """
    Safely extract data from a given query on a response or selector.
    :param response_or_selector: Scrapy Response or Selector object.
    :param query: String representing the CSS or XPath query.
    :param query_type: 'css' for CSS queries, 'xpath' for XPath queries.
    :param extract_first: True to extract the first result, False to extract all results.
    :param default_value: Default value to return if no data is found. Can be of any type.
    :return: Extracted data or default value.
    """
    if query_type == 'css':
        data = response_or_selector.css(query)
    elif query_type == 'xpath':
        data = response_or_selector.xpath(query)
    else:
        raise ValueError("Invalid query_type. Use 'css' or 'xpath'.")

    if extract_first:
        return data.get(default=default_value).strip() if data and data.get() is not None else default_value
    else:
        return [element.strip() for element in data.getall()] if data else default_value if isinstance(default_value,
                                                                                                       list) else [
            default_value]


def get_product_specs(response):
    product_specs = {}
    specs_table = response.xpath("//table[@id='productDetails_detailBullets_sections1']")

    for spec in specs_table.xpath(".//tr"):
        spec_name = safe_extract(spec, ".//th/text()", query_type='xpath', extract_first=True,
                                 default_value='Unknown Spec')
        spec_value = safe_extract(spec, ".//td/text()", query_type='xpath', extract_first=True,
                                  default_value='Not Available')

        if spec_name != 'Unknown Spec':
            product_specs[spec_name] = spec_value

    return product_specs


def get_rating(response):
    rating_selector = 'a.a-popover-trigger.a-declarative span.a-size-base.a-color-base::text'
    rating = safe_extract(response, rating_selector, query_type='css', extract_first=True, default_value=0.0)
    try:
        return float(rating)
    except ValueError:
        logging.error(f"Failed to convert rating '{rating}' to float.")
        return 0.0


def get_image_url(response):
    image_url_selector = "//div[@id='imgTagWrapperId']/img/@src"
    return safe_extract(response, image_url_selector, query_type='xpath', extract_first=True, default_value='')


def get_product_description(response):
    description_selector = "//div[@id='productDescription']/p/span/text()"
    return safe_extract(response, description_selector, query_type='xpath', extract_first=True, default_value='')


def get_product_title(response):
    title_selector = 'span#productTitle::text'
    return safe_extract(response, title_selector, query_type='css', extract_first=True, default_value='')


def get_price(response):
    price_selector = 'span.a-price span[aria-hidden="true"]::text'
    price_str = safe_extract(response, price_selector, query_type='css', extract_first=True, default_value='0')
    try:
        return float(price_str.replace('$', '').replace(',', '').strip())
    except ValueError:
        logging.error(f"Failed to convert price '{price_str}' to float.")
        return 0.0


def get_features(response):
    features_selector = "//div[@id='feature-bullets']//li/span[@class='a-list-item']/text()"
    features = safe_extract(response, features_selector, query_type='xpath', extract_first=False, default_value=[])
    return [feature for feature in features if feature.strip()]


def get_reviews(response, product_reviews):
    reviews_selector = 'div[data-hook="review"]'
    reviews = response.css(reviews_selector)
    for review in reviews:
        review_data = {
            'rating': safe_extract(review, 'i[data-hook="review-star-rating"] > span::text', query_type='css',
                                   default_value='0'),
            'date': safe_extract(review, 'span[data-hook="review-date"]::text', query_type='css',
                                 default_value='No Date'),
            'text': safe_extract(review, 'string(.//span[@data-hook="review-body"]//span)', query_type='xpath',
                                 default_value='No Review Text'),
            'author': safe_extract(review, 'span.a-profile-name::text', query_type='css', default_value='Anonymous'),
        }
        if review_data['text'] == 'No Review Text':
            review_data['text'] = safe_extract(review, 'div[data-hook="review-collapsed"] > span::text',
                                               query_type='css',
                                               default_value='No Review Text'),
        # Convert rating to float and handle conversion failure
        try:
            review_data['rating'] = float(review_data['rating'].split(' out of')[0].strip())
        except ValueError:
            review_data['rating'] = 0.0
        # check if the author already exists in the list of reviews
        if review_data['author'] not in [review['author'] for review in product_reviews]:
            product_reviews.append(review_data)
        else:
            continue
    return product_reviews


def extract_asin_from_url(url):
    # Define the regular expression pattern to match an ASIN in the Amazon product URL
    pattern = r'/dp/([A-Z0-9]{10})'

    # Use the re.search() method to find the first occurrence of the pattern
    match = re.search(pattern, url)

    # If a match is found, return the first capturing group (ASIN), otherwise return None
    return match.group(1) if match else None


# def get_reviews_on_review_page(response):

class AmazonSpider(scrapy.Spider):
    name = 'amazon'

    def __init__(self, url=None, job_id=None, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        if not url or not job_id:
            raise ValueError("URL and Job ID are required")
        self.start_urls = [url]  # This should be the URL you intend to scrape
        self.job_id = job_id
        self.critical_reviews = []
        self.positive_reviews = []
        self.default_reviews = []
        self.requests_completed = 0
        self.requests_needed = 3
        self.product = {}
        username = os.getenv("BRIGHT_DATA_USERNAME")
        password = os.getenv("BRIGHT_DATA_PASSWORD")
        host = os.getenv("BRIGHT_DATA_HOST")
        if not all([username, password, host]):
            logging.error("Missing proxy configuration")
            return
        session_id = randint(0, 1000000)
        proxy_user_pass = f"{username}-session-{session_id}:{password}"
        proxy_url = f"http://{proxy_user_pass}@{host}:22225"
        self.proxy = proxy_url

    def start_requests(self):
        for url in self.start_urls:
            domain = url.split('/')[2]
            product_id = extract_asin_from_url(url)
            critical_reviews_url = f"https://{domain}/product-reviews/{product_id}/?filterByStar=critical&reviewerType=avp_only_reviews"
            positive_reviews_url = f"https://{domain}/product-reviews/{product_id}/?filterByStar=positive&reviewerType=avp_only_reviews"
            yield scrapy.Request(url, callback=self.parse, meta={'proxy': self.proxy})
            yield scrapy.Request(critical_reviews_url, callback=self.parse_critical_reviews,
                                 meta={'proxy': self.proxy})
            yield scrapy.Request(positive_reviews_url, callback=self.parse_positive_reviews,
                                 meta={'proxy': self.proxy})

    def generate_job(self):
        if self.requests_completed != self.requests_needed:
            return
        reviews = self.critical_reviews
        for review in self.positive_reviews:
            if review['author'] not in [r['author'] for r in reviews]:
                reviews.append(review)
        for review in self.default_reviews:
            if review['author'] not in [r['author'] for r in reviews]:
                reviews.append(review)
        product = Product(
            id=self.product['id'],
            job_id=self.job_id,
            product_id=self.product['id'],
            domain=self.product['domain'],
            title=self.product['title'],
            description=self.product['description'],
            price=self.product['price'],
            image_url=self.product['image_url'],
            specs=self.product['specs'],
            features=self.product['features'],
            rating=self.product['rating'],
            reviews=reviews,
            created_at=self.product['created_at'],
            updated_at=self.product['updated_at'],
            generated_review='',
        )

        # merge all the reviews check the author to avoid duplicates

        job = Job(
            id=self.job_id,
            status="completed",
            end_time=datetime.datetime.utcnow().isoformat(),
            start_time=datetime.datetime.utcnow().isoformat(),
            result=product.model_dump(),
            url=self.start_urls[0],
            error={}
        )
        return job.model_dump()
        # post request to update the job



    def parse(self, response):
        self.product = {
            "id": extract_asin_from_url(response.url),
            "job_id": self.job_id,
            "product_id": extract_asin_from_url(response.url),
            "domain": response.url.split('/')[2],
            "title": get_product_title(response),
            "description": get_product_description(response),
            "price": get_price(response),
            "image_url": get_image_url(response),
            "specs": get_product_specs(response),
            "features": get_features(response),
            "rating": get_rating(response),
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
            "generated_review": '',
        }
        self.default_reviews = get_reviews(response, [])
        self.requests_completed += 1
        if self.requests_completed == self.requests_needed:
            job = self.generate_job()
            yield scrapy.Request(
                url=f"http://localhost:8000/jobs/{self.job_id}",
                method='PUT',
                body=json.dumps(job),
                headers={'Content-Type': 'application/json'},
            )
        # product = Product(
        #     id=extract_asin_from_url(response.url),
        #     job_id=self.job_id,
        #     product_id=extract_asin_from_url(response.url),
        #     domain=response.url.split('/')[2],
        #     title=get_product_title(response),
        #     description=get_product_description(response),
        #     price=get_price(response),
        #     image_url=get_image_url(response),
        #     specs=get_product_specs(response),
        #     features=get_features(response),
        #     rating=get_rating(response),
        #     reviews=get_reviews(response, []),
        #     created_at=datetime.datetime.utcnow().isoformat(),
        #     updated_at=datetime.datetime.utcnow().isoformat(),
        #     generated_review='',
        # )
        # query param for crictical reviews ?filterByStar=critical&reviewerType=avp_only_reviews
        # get the critical reviews

        # critical_reviews_url = f"https://{product.domain}/product-reviews/{product.product_id}/?filterByStar=critical&reviewerType=avp_only_reviews"
        #
        # yield scrapy.Request(critical_reviews_url, callback=self.parse_critical_reviews,
        #                      meta={'product': product, 'proxy': self.proxy})

    def parse_critical_reviews(self, response):
        critical_reviews = get_reviews(response, [])
        self.critical_reviews = critical_reviews
        self.requests_completed += 1
        if self.requests_completed == self.requests_needed:
            job = self.generate_job()
            yield scrapy.Request(
                url=f"http://localhost:8000/jobs/{self.job_id}",
                method='PUT',
                body=json.dumps(job),
                headers={'Content-Type': 'application/json'},
            )

    def parse_positive_reviews(self, response):
        positive_reviews = get_reviews(response, [])
        self.positive_reviews = positive_reviews
        self.requests_completed += 1
        if self.requests_completed == self.requests_needed:
            job = self.generate_job()
            yield scrapy.Request(
                url=f"http://localhost:8000/jobs/{self.job_id}",
                method='PUT',
                body=json.dumps(job),
                headers={'Content-Type': 'application/json'},
            )

