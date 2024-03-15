import os
import httpx
from fastapi import HTTPException


async def find_similar_embeddings(collection, embedding: list, excludes: list):
    documents = collection.aggregate([
        {"$vectorSearch": {
            "queryVector": embedding,
            "path": "embedding",
            "numCandidates": 100,
            "limit": 5,
            "index": "vector_index",
        }},
        {"$project": {field: 0 for field in excludes}}
    ])
    return list(documents)


async def create_embedding(query: str):
    url = 'https://api.openai.com/v1/embeddings'
    openai_key = os.getenv("OPENAI_API_KEY")

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
        # embedding_document = {
        #     'embedding': response_data['data'][0]['embedding'],
        #     ** data
        # }
        # result = test_collection.insert_one(embedding_document)
        # print(f'Document inserted with id: {result.inserted_id}')

        # return result
