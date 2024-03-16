import unittest
from pprint import pprint

import pytest
from openai import OpenAI

from app.routes.route import generate_review, generate_product_review
from dotenv import load_dotenv


@pytest.mark.asyncio
async def test_generate_review():
    load_dotenv()
    # Assuming your OpenAI class initialization handles API keys and other configurations
    client = OpenAI()

    # Mock product data
    product = {
        "_id": "B07ZPKZSSC",
        "id": "B07ZPKZSSC",
        "job_id": "65f4c3684cc0f6448ca0cca4",
        "domain": "www.amazon.com",
        "title": "Apple iPhone 11 Pro, 64GB, Space Gray - Unlocked (Renewed)",
        "description": "Shoot amazing videos and photos with the Ultra Wide, Wide, and Telephoto cameras. Capture your best low-light photos with Night mode. Watch HDR movies and shows on the Super Retina XDR display—the brightest iPhone display yet. Experience unprecedented performance with A13 Bionic for gaming, augmented reality (AR), and photography. All in the first iPhone powerful enough to be called Pro.",
        "price": 268,
        "image_url": "https://m.media-amazon.com/images/I/81LmL94PUvS.__AC_SX300_SY300_QL70_FMwebp_.jpg",
        "specs": {
            "Product Dimensions": "7 x 5 x 4 inches",
            "Item Weight": "10.5 ounces",
            "ASIN": "B07ZPKZSSC",
            "Item model number": "A2160",
            "Batteries": "1 Lithium Ion batteries required. (included)",
            "Customer Reviews": "",
            "Best Sellers Rank": "",
            "OS": "iOS",
            "RAM": "64 GB",
            "Wireless communication technologies": "Cellular",
            "Connectivity technologies": "Bluetooth, Wi-Fi, USB, NFC",
            "Other display features": "Wireless",
            "Human Interface Input": "Touchscreen",
            "Form Factor": "Smartphone",
            "Color": "Space Gray",
            "Battery Power Rating": "10 Watts",
            "Whats in the box": "Adapter, USB Cable",
            "Manufacturer": "Apple Computer",
            "Date First Available": "October 28, 2019",
            "Memory Storage Capacity": "64 GB",
            "Standing screen display size": "5.8 Inches",
            "Ram Memory Installed Size": "4 GB"
        },
        "features": [
            "This phone is unlocked and compatible with any carrier of choice on GSM and CDMA networks (e.g. "
            "AT&T, T-Mobile, Sprint, Verizon, US Cellular, Cricket, Metro, Tracfone, Mint Mobile, etc.).",
            "Tested for battery health and guaranteed to have a minimum battery capacity of 80%.",
            "Successfully passed a full diagnostic test which ensures like-new functionality and removal of "
            "any prior-user personal information.",
            "The device does not come with headphones or a SIM card. It does include a generic (Mfi "
            "certified) charger and charging cable.",
            "Inspected and guaranteed to have minimal cosmetic damage, which is not noticeable when the "
            "device is held at arm's length."
        ],
        "rating": 4.2,

    }

    # Call the function under test
    review = await generate_product_review(product)
    pprint(review)
