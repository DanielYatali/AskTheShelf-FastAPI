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
def test_product_chat(json_file):
    """
    Tests that the manager can handle requests from both OpenAI and Gemini.
    """
    # with open(json_file, 'r') as f:
    #     json_data = json.load(f)
    with open(json_file, 'r', encoding='utf-8') as f:
        try:
            json_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from file '{json_file}': {e}")
            return None
    query = json_data["query"]
    messages = json_data["messages"]
    product = json_data["product"]
    answers = json_data["answer"]
    with open("product_chat_prompt.txt", "r") as f:
        prompt = f.read()
    prompt = prompt.replace("{{product}}", json.dumps(product))
    conversation = [
        {
            "role": "system",
            "content": prompt
        },
    ]
    for message in messages:
        conversation.append({
            "role": message["role"],
            "content": json.dumps(message)
        })

    pd.set_option('display.max_columns', None)  # Show all columns
    pd.set_option('display.max_rows', None)  # Show all rows
    pd.set_option('display.max_colwidth', None)
    openai_response = (make_openai_request(conversation))
    gemini_response = (make_gemini_request(conversation))
    # llama_response = (make_groq_request(conversation))
    # mixed_response = (make_groq_request(conversation, Mixtral))
    # gemma_response = (make_groq_request(conversation, Gemma))

    print("Open AI Response:")
    print(openai_response)

    print("Gemini Response:")
    print(gemini_response)
    #
    # print("Llama Response:")
    # print(llama_response)
    #
    # print("Mixed Response:")
    # print(mixed_response)
    #
    # print("Gemma Response:")
    # print(gemma_response)
