from aiohttp import ClientSession

from app.core.config import settings
from app.core.logger import logger


class BestBuyService:
    session = None  # Class variable to hold a persistent ClientSession

    @classmethod
    async def make_bestbuy_request(cls, url):
        if cls.session is None:  # Initialize session if it's not already done
            cls.session = ClientSession()

        api_key = settings.BESTBUY_API_KEY
        url = f"{url}&apiKey={api_key}"
        try:
            async with cls.session.get(url) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Failed to make request to BestBuy API: {str(e)}")
            return None

    @staticmethod
    async def get_products_by_name(name):
        simple_name = " ".join(name.split()[:3])  # Extract the first three words from the product name
        name = simple_name
        url = f"https://api.bestbuy.com/v1/products(name={name}*)?format=json&show=sku,name,salePrice,url"
        response = await BestBuyService.make_bestbuy_request(url)
        if response and 'products' in response:
            products = response['products']
            if len(products) > 0:
                return products[0]
        return None

    @staticmethod
    async def batch_get_products(product_names):
        products = []
        for name in product_names:
            product = await BestBuyService.get_products_by_name(name)
            products.append(product)
        return products
        # tasks = [BestBuyService.get_products_by_name(name) for name in product_names]
        # return await asyncio.gather(*tasks)

    @classmethod
    async def close_session(cls):
        if cls.session:
            await cls.session.close()
