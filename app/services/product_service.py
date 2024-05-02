from typing import Optional

from app.models.product_model import Product
from app.models.product_error_model import ProductError


class ProductService:
    @staticmethod
    async def validate_product(product: Product) -> [str]:
        errorMessages = []
        if product.price <= 0:
            errorMessages.append("Price must be greater than 0")
        if product.rating < 0 or product.rating > 5:
            errorMessages.append("Rating must be between 0 and 5")
        if not product.title or product.title == "":
            errorMessages.append("Title is required")
        if not product.domain or product.domain == "":
            errorMessages.append("Domain is required")
        if not product.image_url or product.image_url == "":
            errorMessages.append("Image URL is required")
        if not product.features or len(product.features) == 0:
            errorMessages.append("Features are required")
        if not product.specs or len(product.specs) == 0:
            errorMessages.append("Specs are required")
        return errorMessages

    @staticmethod
    async def create_product(product: Product) -> Optional[Product]:
        await product.save()
        return product

    @staticmethod
    async def get_product_by_id(product_id: str) -> Optional[Product]:
        product = await Product.find_one(Product.product_id == product_id)
        if not product:
            return None
        return product

    @staticmethod
    async def get_products():
        products = await Product.all().to_list()
        return products

    @staticmethod
    async def get_products_by_job(job_id: str):
        products = await Product.find(Product.job_id == job_id).to_list()
        return products

    @staticmethod
    async def get_products_by_domain(domain: str):
        products = await Product.find(Product.domain == domain).to_list()
        return products

    @staticmethod
    async def get_products_by_rating(rating: float):
        products = await Product.find(Product.rating == rating).to_list()
        return products

    @staticmethod
    async def get_products_by_title(title: str):
        products = await Product.find(Product.title == title).to_list()
        return products

    @staticmethod
    async def update_product(product_id: str, product: Product) -> Optional[Product]:
        existing_product = await Product.find_one(Product.product_id == product_id)
        if not existing_product:
            return None
        existing_product.job_id = product.job_id
        existing_product.domain = product.domain
        existing_product.title = product.title
        existing_product.description = product.description
        existing_product.price = product.price
        existing_product.image_url = product.image_url
        existing_product.specs = product.specs
        existing_product.features = product.features
        existing_product.reviews = product.reviews
        existing_product.rating = product.rating
        existing_product.embedding = product.embedding
        existing_product.embedding_text = product.embedding_text
        existing_product.updated_at = product.updated_at
        existing_product.similar_products = product.similar_products
        existing_product.variants = product.variants
        existing_product.number_of_reviews = product.number_of_reviews
        existing_product.qa = product.qa
        existing_product.generated_review = product.generated_review
        existing_product.affiliate_url = product.affiliate_url
        await existing_product.save()
        return existing_product

    @staticmethod
    async def delete_product(product_id: str) -> Optional[Product]:
        product = await Product.find_one(Product.id == product_id)
        if not product:
            return None
        await product.delete()
        return product


class ProductErrorService:
    @staticmethod
    async def create_product_error(product_error: ProductError) -> Optional[ProductError]:
        await product_error.save()
        return product_error

    @staticmethod
    async def get_product_error_by_id(product_id: str) -> Optional[ProductError]:
        product_error = await ProductError.find_one(ProductError.product_id == product_id)
        if not product_error:
            return None
        return product_error

    @staticmethod
    async def get_product_errors():
        product_errors = await ProductError.all().to_list()
        return product_errors

    @staticmethod
    async def get_product_error_by_job(job_id: str):
        product_errors = await ProductError.find(ProductError.job_id == job_id).to_list()
        return product_errors

    @staticmethod
    async def get_product_error_by_domain(domain: str):
        product_errors = await ProductError.find(ProductError.domain == domain).to_list()
        return product_errors

    @staticmethod
    async def get_product_error_by_rating(rating: float):
        product_errors = await ProductError.find(ProductError.rating == rating).to_list()
        return product_errors

    @staticmethod
    async def get_product_error_by_title(title: str):
        product_errors = await ProductError.find(ProductError.title == title).to_list()
        return product_errors
