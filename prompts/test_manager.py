import asyncio
import json

from app.services.llm_service import LLMService


# Read prompts from a list of files
def read_prompts(prompt_files):
    prompts = []
    for filename in prompt_files:
        try:
            with open(filename, mode='r') as file:
                prompts.append(file.read())
        except FileNotFoundError:
            print(f"Error: {filename} was not found.")
        except Exception as e:
            print(f"An error occurred while reading {filename}: {e}")
    return prompts


# Run a conversation based on a prompt and product information
async def run_conversation(prompt, product, user_query):
    conversation = [
        {"role": "system", "content": prompt},
        {"role": "user",
         "content": "I'm looking for a laptop with at least 16GB of RAM and 1TB of storage. I also need a good graphics card. Can you help me find one?"},
        {"role": "system", "content": json.dumps(product)},
        {"role": "user", "content": user_query}
    ]
    response = await LLMService.make_llm_request(conversation)
    return response


# Main function to manage test execution and write results
def main():
    prompt_files = ["manager.txt"]
    prompts = read_prompts(prompt_files)
    product = {
        "product_id": "B0CXX7T52Q",
        "title": "Lenovo Legion 5 Gaming Laptop",
        "price": 1179.99,
        "image_url": "https://example.com/image.jpg"
    }
    user_query = "What is the weight of this product?"

    results = []
    loop = asyncio.get_event_loop()
    for prompt in prompts:
        try:
            result = loop.run_until_complete(run_conversation(prompt, product, user_query))
            results.append({"prompt": prompt, "response": result})
        except Exception as e:
            results.append({"prompt": prompt, "error": str(e)})

    # Write results to a file
    with open('test_results.json', 'w') as outfile:
        json.dump(results, outfile, indent=4)


def test_manager_test():
    promptFile = "manager.txt"
    prompt = ""
    try:
        with open(promptFile, mode='r') as file:
            prompt = file.read()
    except FileNotFoundError:
        print("Error: The file was not found.")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    user_query = "how much does it weigh?"
    product = {
        "product_id": "B0CXX7T52Q",
        "domain": "www.amazon.com",
        "title": "Lenovo Legion 5 Gaming Laptop, 15.6\" WQHD 165Hz Display, 8-Core AMD Ryzen 7 7735HS, NVIDIA Geforce RTX 4060, 32GB DDR5 RAM, 1TB NVMe SSD, Backlit Keyboard, WiFi 6, HDMI, Win 11, w/CUE Accessories",
        "price": 1179.99,
        "image_url": "https://m.media-amazon.com/images/I/71OF9CFOuUL._AC_SX300_SY300_.jpg",
        "rating": 0.0,
        "affiliate_url": ""
    }
    conversation = [
        {
            "role": "system",
            "content": prompt
        },
        # {
        #     "role": "user",
        #     "content": "I looking for a laptop with at least 16GB of RAM and 1TB of storage. I also need a good graphics card. Can you help me find one?",
        # },
        # {
        #     "role": "system",
        #     "content": f"{product}"
        # },
        {
            "role": "user",
            "content": user_query
        }
    ]

    # Running the async function within the event loop
    loop = asyncio.get_event_loop()
    try:
        response = loop.run_until_complete(LLMService.make_llm_request(conversation))
        print(response)
        assert response is not None  # You could add more specific assertions here
    except Exception as e:
        print(f"Failed to get response from LLMService: {e}")


# To run the test function
if __name__ == "__main__":
    test_manager_test()
