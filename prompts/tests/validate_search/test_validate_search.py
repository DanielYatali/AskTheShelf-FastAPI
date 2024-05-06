import json
import os
import pytest
from groq import Groq
from openai import OpenAI
import google.generativeai as genai
import pandas as pd

from app.core.config import settings

GPT3 = "gpt-3.5-turbo"
GEMINI = "gemini-pro"
Llama = "llama3-70b-8192"
Mixtral = "mixtral-8x7b-32768"
Gemma = "gemma-7b-it"


def get_all_json_files(directory):
    json_files = []
    # read all files in the directory
    for file in os.listdir(directory):
        if file.endswith('.json'):
            json_files.append(os.path.join(directory, file))
    return json_files


def make_groq_request(conversation, model=Llama):
    # try:
    client = Groq(
        api_key=settings.GROQ_API_KEY,
    )
    chat_completion = client.chat.completions.create(
        messages=conversation,
        model=model,
        temperature=0
    )
    return chat_completion.choices[0].message.content


def make_openai_request(conversation, model=GPT3):
    # try:
    client = OpenAI()
    completion = client.chat.completions.create(
        model=model,
        messages=conversation,
        temperature=0
    )
    message = completion.choices[0].message.model_dump()
    return message["content"]


def make_gemini_request(conversation, model=GEMINI):
    # try:
    generation_config = genai.GenerationConfig(
        candidate_count=1,
        temperature=0,
    )
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(model, generation_config=generation_config)
    response = model.generate_content(json.dumps(conversation))
    return response.text


@pytest.mark.parametrize('json_file', get_all_json_files('fixtures'))
def test_validate_search(json_file):
    """
    Tests that the manager can handle requests from both OpenAI and Gemini.
    """
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    query = json_data["query"]
    products = json_data["products"]
    with open("validate_embedding_search_prompt.txt", "r") as f:
        prompt = f.read()
    conversation = [
        {"role": "system", "content": prompt},
        {"role": "user",
         "content": f"{products}"},
        {"role": "user", "content": query}
    ]
    openai_response = json.loads(make_openai_request(conversation))
    gemini_response = json.loads(make_gemini_request(conversation))
    llama_response = (make_groq_request(conversation))
    mixed_response = (make_groq_request(conversation, Mixtral))
    gemma_response = (make_groq_request(conversation, Gemma))

    print("Open AI Response:")
    print(json.dumps(openai_response, indent=4))

    print("Gemini Response:")
    print(json.dumps(gemini_response, indent=4))

    print("Llama Response:")
    print(llama_response)

    print("Mixed Response:")
    print(mixed_response)

    print("Gemma Response:")
    print(gemma_response)
