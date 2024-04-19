import asyncio

from app.services.llm_service import LLMService


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

    user_query = "What is the weight of this product?"
    product = {
        "product_id": "B0CXX7T52Q",
        "domain": "www.amazon.com",
        "title": "Lenovo Legion 5 Gaming Laptop, 15.6\" WQHD 165Hz Display, 8-Core AMD Ryzen 7 7735HS, NVIDIA Geforce RTX 4060, 32GB DDR5 RAM, 1TB NVMe SSD, Backlit Keyboard, WiFi 6, HDMI, Win 11, w/CUE Accessories",
        "description": "Lenovo Legion 5 Gaming Laptop",
        "price": 1179.99,
        "image_url": "https://m.media-amazon.com/images/I/71OF9CFOuUL._AC_SX300_SY300_.jpg",
        "rating": 0.0,
        "specs": {
            "ASIN": "B0CXX7T52Q",
            "Customer Reviews": "",
            "Best Sellers Rank": "",
            "Date First Available": "March 13, 2024",
            "Standing screen display size": "‎15.6 Inches",
            "Screen Resolution": "‎2560 x 1440 pixels",
            "Processor": "‎4.75 GHz ryzen_7",
            "RAM": "‎DDR5",
            "Hard Drive": "‎1 TB SSD",
            "Graphics Coprocessor": "‎NVIDIA GeForce RTX 4060",
            "Chipset Brand": "‎NVIDIA",
            "Card Description": "‎Dedicated",
            "Brand": "‎Lenovo",
            "Item Weight": "‎8.78 pounds",
            "Product Dimensions": "‎14.13 x 10.33 x 0.95 inches",
            "Item Dimensions  LxWxH": "‎14.13 x 10.33 x 0.95 inches",
            "Color": "‎Storm Grey",
            "Processor Brand": "‎Intel",
            "Number of Processors": "‎8",
            "Hard Drive Interface": "‎PCIE x 4"
        },
        "features": [
            "【8-Core Processor】AMD Ryzen 7 7735HS, 8 Cores and 16 Threads, 3.2GHz Base Clock, Up to 4.75GHz Boost Clock, 16MB Cache, AMD Radeon 680M. Providing impressive processing power for seamless multitasking, content creation and gaming.",
            "【NVIDIA Geforce RTX 4060】Gaming Excellence Elevate your gaming experience with the NVIDIA GeForce RTX 4060 8GB GPU, delivering ultra-realistic graphics and smooth frame rates. Dive into the latest AAA titles and esports games with confidence.",
            "【Gaming Display】15.6\" WQHD (2560x1440) IPS 350nits Anti-glare, 100% sRGB, 165Hz, Dolby Vision, FreeSync, G-SYNC. Enjoy true-to-life colors and smooth motion, whether you're gaming, watching videos, or working on creative projects.",
            "【Upgraded to 32GB DDR5 Memory】Substantial high-bandwidth RAM to smoothly run your games and photo- and video-editing applications, as well as multiple programs and browser tabs all at once.",
            "【Upgraded to 1TB NVMe SSD】Get up to 15x faster performance than a traditional hard drive. Give you a long-lasting and smooth experience, both system boot up and application start are very fast."
        ],
        "created_at": "2024-04-17T02:24:00.694000",
        "updated_at": "2024-04-16T22:24:18.653000",
        "variants": {
            "Capacity:": [
                {
                    "name": "16GB DDR5 | 1TB NVMe SSD"
                },
                {
                    "name": "16GB DDR5 | 512GB NVMe SSD"
                },
                {
                    "name": "32GB DDR5 | 1TB NVMe SSD"
                },
                {
                    "name": "32GB DDR5 | 2TB NVMe SSD"
                },
                {
                    "name": "64GB DDR5 | 1TB NVMe SSD"
                },
                {
                    "name": "64GB DDR5 | 2TB NVMe SSD"
                }
            ],
            "Style:": []
        },
        "number_of_reviews": "2",
        "affiliate_url": ""
    }
    conversation = [
        {
            "role": "system",
            "content": prompt
        },
        {
            "role": "user",
            "content": "I looking for a laptop with at least 16GB of RAM and 1TB of storage. I also need a good graphics card. Can you help me find one?",
        },
        {
            "role": "system",
            "content": f"{product}"
        },
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
