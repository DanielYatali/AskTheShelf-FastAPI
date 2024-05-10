import json

import pytest
import asyncio

from app.services.bestbuy_service import BestBuyService


@pytest.mark.asyncio
async def test_get_products_by_name():
    # This assumes you have the BESTBUY_API_KEY environment variable set for testing
    # You might want to skip this test if the API key is not set
    product_name = "Samsung Galaxy S24 Plus 5g SM-S926B/DS 256GB 12GB RAM, 50 MP Camera, AI Smartphone, Unlocked Android International Model 2024 Onyx Gray"  # Example product name, change based on your test requirements
    response = await BestBuyService.get_products_by_name(product_name)
    print(json.dumps(response, indent=4))
    assert response is not None


@pytest.mark.asyncio
async def test_batch_get_products():
    # This assumes you have the BESTBUY_API_KEY environment variable set for testing
    # You might want to skip this test if the API key is not set
    product_names = ["Acer - Nitro 5 15.6", "Lenovo - IdeaPad 3 15"]
    responses = await BestBuyService.batch_get_products(product_names)
    print(json.dumps(responses, indent=4))
