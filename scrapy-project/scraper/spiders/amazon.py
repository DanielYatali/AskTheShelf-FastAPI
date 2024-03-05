import datetime
import logging
import os
from random import randint
import json
import scrapy
from urllib.parse import urljoin
import re

from app.schemas import schemas


def get_image_url(response):
    image_url = response.xpath("//div[@id='imgTagWrapperId']/img/@src").get()
    return image_url


def get_product_description(response):
    product_description = response.xpath("//div[@id='productDescription']/p/span/text()").get()
    if product_description:
        product_description = product_description.strip()
    return product_description


def get_product_title(response):
    title = response.css('span#productTitle::text').get().strip()
    return title


def get_product_specs(response):
    specs_table = response.xpath("//table[@id='productDetails_detailBullets_sections1']")
    product_specs = {}
    for spec in specs_table.xpath(".//tr"):
        spec_name = spec.xpath(".//th/text()").get().strip()
        spec_value = spec.xpath(".//td/text()").get().strip()
        product_specs[spec_name] = spec_value
    return product_specs


def get_price(response):
    price = response.css('span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen::text').get()
    if not price:
        price = response.css(
            'span.a-price.a-text-price.a-size-medium.apexPriceToPay span[aria-hidden="true"]::text').get()
    if price:
        price = price.strip()
    return price


def get_features(response):
    features_section = response.xpath("//div[@id='feature-bullets']")
    features = features_section.xpath(".//li/span[@class='a-list-item']/text()").getall()
    features = [feature.strip() for feature in features if feature.strip()]
    return features


def get_reviews(response):
    product_reviews = []
    reviews = response.css('div[data-hook="review"]')
    for review in reviews:
        try:
            # Extract data using CSS selectors
            review_title = review.css('a[data-hook="review-title"]::text').get(default='No Title')
            review_rating = review.css('i[data-hook="review-star-rating"] > span::text').get(default='No Rating')
            review_date = review.css('span[data-hook="review-date"]::text').get(default='No Date')
            review_text = review.css('div[data-hook="review-collapsed"] > span::text').get(default='No Review Text')

            # Populate review data
            review_data = {
                'title': review_title.strip() if review_title else 'No Title',
                'rating': review_rating.strip() if review_rating else 'No Rating',
                'date': review_date.strip() if review_date else 'No Date',
                'text': review_text.strip() if review_text else 'No Review Text'
            }
            product_reviews.append(review_data)
        except Exception as e:
            # Log the error and the review causing it for debugging
            logging.error(f"Error processing review: {e}, Review: {review.get()}")
    return product_reviews


class AmazonSpider(scrapy.Spider):
    name = 'amazon'

    def __init__(self, url=None, job_id=None, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        if not url or not job_id:
            url = "https://www.amazon.com/Apple-iPhone-11-64GB-Unlocked/dp/B07ZPKZSSC"
            job_id = "12345"
            # raise CloseSpider('Missing url or job_id')
        self.start_urls = [url]  # This should be the URL you intend to scrape
        self.job_id = job_id

    def start_requests(self):
        for url in self.start_urls:  # Iterate over start_urls in case you have multiple
            username = os.getenv("BRIGHT_DATA_USERNAME")
            password = os.getenv("BRIGHT_DATA_PASSWORD")
            host = os.getenv("BRIGHT_DATA_HOST")
            session_id = randint(0, 1000000)
            proxy_user_pass = f"{username}-session-{session_id}:{password}"
            proxy_url = f"http://{proxy_user_pass}@{host}:22225"
            yield scrapy.Request(url, callback=self.parse, meta={'proxy': proxy_url})

    def parse(self, response):
        # Create a Scrapy item or a simple dictionary to hold the extracted data
        image_url = get_image_url(response)
        description = get_product_description(response)
        title = get_product_title(response)
        specs = get_product_specs(response)
        price = get_price(response)
        features = get_features(response)
        reviews = get_reviews(response)

        product_data = schemas.Product(
            id=self.job_id,
            title=title,
            image_url=image_url,
            url=response.url,
            description=description,
            specs=specs,
            price=price,
            features=features,
            reviews=reviews
        )
        # make a post request to the api with the product data

        # Update the job status to completed
        job = schemas.JobUpdate(
            id=self.job_id,
            status="completed",
            end_time=datetime.datetime.utcnow(),
            result=product_data,
            error=""
        )
        body = job.json()

        request = scrapy.Request(
            url="http://localhost:8000/job/" + self.job_id,
            method="PUT",
            headers={"Content-Type": "application/json"},
            body=body
        )
        yield request

        # product_data_json = json.dumps(product_data, ensure_ascii=False)
        # print(product_data_json.encode('utf-8', errors='ignore').decode('utf-8'))

        # product_data['reviews'] = []
        # reviews = response.css('div[data-hook="review"]')
        #
        # for review in reviews:
        #     # Extracting data using CSS selectors
        #     review_title = review.css('a[data-hook="review-title"]::text').get()
        #     review_rating = review.css('i[data-hook="review-star-rating"] > span::text').get()
        #     review_date = review.css('span[data-hook="review-date"]::text').get()
        #     review_text = review.css('div[data-hook="review-collapsed"] > span::text').get()
        #     review_data = {
        #         'title': review_title,
        #         'rating': review_rating,
        #         'date': review_date,
        #         'text': review_text
        #     }
        #     product_data['reviews'].append(review_data)
        #
        #
        #
        # # Extract the product title
        # image_url = response.xpath("//div[@id='imgTagWrapperId']/img/@src").get()
        # product_data['image_url'] = image_url
        # product_description = response.xpath("//div[@id='productDescription']/p/span/text()").get()
        # if product_description:
        #     product_description = product_description.strip()
        # product_data['product_description'] = product_description
        # product_data['title'] = response.css('span#productTitle::text').get().strip()
        # # Locate the specifications table by its ID
        # specs_table = response.xpath("//table[@id='productDetails_detailBullets_sections1']")
        #
        # # Initialize a dictionary to hold the specifications
        # product_specs = {}
        #
        # # Iterate through each row in the table to extract the specs
        # for spec in specs_table.xpath(".//tr"):
        #     # Extract the specification name and value
        #     spec_name = spec.xpath(".//th/text()").get().strip()
        #     spec_value = spec.xpath(".//td/text()").get().strip()
        #
        #     # Add the spec name and value to the dictionary
        #     product_specs[spec_name] = spec_value
        #
        # product_data['specs'] = product_specs
        # price = response.css('span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen::text').get()
        # # Locate the 'About this item' section by its surrounding div's id
        # features_section = response.xpath("//div[@id='feature-bullets']")
        #
        # # Extract the features listed in the 'ul' element
        # features = features_section.xpath(".//li/span[@class='a-list-item']/text()").getall()
        #
        # # Clean up the features by stripping unnecessary whitespace
        # features = [feature.strip() for feature in features if feature.strip()]
        # product_data['features'] = features
        # # If not found, fall back to the price with 'aria-hidden="true"'
        # if not price:
        #     price = response.css('span.a-price.a-text-price.a-size-medium.apexPriceToPay span[aria-hidden="true"]::text').get()
        # # Clean the price and print or yield it
        # if price:
        #     price = price.strip()
        #     product_data['price'] = price

        # # Extract the product description
        # # Note: Amazon's product descriptions can be complex and might require more sophisticated extraction logic
        # product_data['description'] = response.css('#productDescription p::text').get().strip()
        #
        # # Extract customer reviews
        # # This is typically more involved and might require following links or handling dynamic content
        # product_data['reviews'] = response.css('div#customerReviews div.review::text').getall()

        # Yield or return the extracted data
        # yield product_data
