import aiofiles
import httpx
from fastapi import HTTPException
from openai import OpenAI

from app.core.config import settings
from app.core.logger import logger


class LLMService:
    @staticmethod
    async def find_similar_embeddings(collection, embedding, excludes):
        pipeline = [
            {
                "$vectorSearch": {
                    "queryVector": embedding,
                    "path": "embedding",
                    "numCandidates": 100,
                    "limit": 1,
                    "index": "vector_index",
                }
            },
            {"$project": {"score": {"$meta": "vectorSearchScore"},
                          **{field: 0 for field in excludes}}},
        ]

        documents = collection.aggregate(pipeline)
        return list(documents)

    @staticmethod
    async def create_embedding(query):
        url = 'https://api.openai.com/v1/embeddings'
        openai_key = settings.OPENAI_API_KEY
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers={
                'Authorization': f'Bearer {openai_key}',
                'Content-Type': 'application/json'
            }, json={
                'input': query,
                'model': 'text-embedding-ada-002'
            })

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Error from OpenAI API")

            response_data = response.json()
            embedding = response_data['data'][0]['embedding']
            return embedding

    @staticmethod
    async def generate_product_review(product):
        try:
            # Read the prompt asynchronously
            # check the length of the product review array
            promptFile = "prompts/reviews_prompt.txt"
            if len(product["reviews"]) == 0:
                promptFile = "prompts/no_reviews_prompt.txt"
            async with aiofiles.open(promptFile, mode='r') as file:
                prompt = await file.read()

            product.pop("embedding", None)
            # Configure your OpenAI client properly here
            client = OpenAI()

            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user",
                     "content": f"{product}"}
                ]
            )
            message = completion.choices[0].message.model_dump()
            return message["content"]

        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail="Error in generate_product_review")

    @staticmethod
    async def generate_embedding_text(product):
        try:
            # Read the prompt asynchronously
            async with aiofiles.open('prompts/embedding_text_prompt.txt', mode='r') as file:
                prompt = await file.read()

            # Configure your OpenAI client properly here
            client = OpenAI()
            product.pop("embedding", None)
            product.pop("reviews", None)

            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user",
                     "content": f"{product}"}
                ]
            )
            message = completion.choices[0].message.model_dump()
            return message["content"]
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail="Error in generate_embedding_text")

    @staticmethod
    async def product_chat(product, query):
        async with aiofiles.open('prompts/product_chat_prompt.txt', mode='r') as file:
            prompt = await file.read()
            # Configure your OpenAI client properly here
        client = OpenAI()
        product.pop("embedding", None)
        # product.pop("reviews", None)

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user",
                 "content": f"{product}"},
                {"role": "user", "content": query}
            ]
        )
        message = completion.choices[0].message.model_dump()
        return message["content"]

