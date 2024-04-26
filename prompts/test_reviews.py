import os

from groq import Groq

from app.services.llm_service import LLMService
import asyncio
from dotenv import load_dotenv

load_dotenv()


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


async def test_generate_reviews():
    prompts = read_prompts(["reviews_prompt.txt"])

    product = {"affiliate_url": "",
               "created_at": {"$date": {"$numberLong": "1713627832245"}},
               "description": "ASUS Vivobook Go 15 is lightweight and compact. It’s designed to make you productive and keep you entertained wherever you go! With its 180° lay-flat hinge, physical webcam shield and loads of thoughtful design features, Vivobook Go 15 is the laptop that sets you free on the go. *The actual transfer speed of USB 3.0, 3.1, 3.2 (Gen 1 and 2), and/or Type-C will vary depending on many factors including the processing speed of the host device, file attributes and other factors related to system configuration and your operating environment.",
               "domain": "www.amazon.com",
               "embedding_text": "Summary:\n- Title: ASUS 2023 Vivobook Go 15 Laptop, 15.6\" FHD Display, AMD Ryzen 5 7520U Processor, 8GB RAM, 512GB SSD, Windows 11 Home, Mixed Black, E1504FA-AS52\n- Category: Laptops\n- Price: $549.99\n- Key Facts: Lightweight and compact design, AMD Ryzen 5 processor, fast-charging battery, ASUS IceCool thermal technology, ErgoSense keyboard, AI Noise-Canceling Technology, 15.6\" FHD display with NanoEdge bezels, extensive connectivity options.\n- Description Summary: ASUS Vivobook Go 15 offers incredible performance with its AMD processor and 512GB SSD, fast-charging capability, durability, ergonomic keyboard, noise-canceling technology, immersive display, and versatile connectivity.\n- Detailed Specifications:\n  - Screen: 15.6\" FHD (1920 x 1080 pixels) display\n  - Processor: AMD Ryzen 5 7520U (4.3 GHz)\n  - RAM: 8 GB LPDDR5\n  - Storage: 512 GB SSD\n  - Graphics: AMD Radeon Graphics (6 GB)\n  - Operating System: Windows 11 Home\n  - Connectivity: Bluetooth, Wi-Fi 6E, USB A, USB C, HDMI\n  - Weight: 3.59 pounds\n  - Dimensions: 14.9 x 0.7 x 9.15 inches\n  - Color: Mixed Black\n  - Other: ASUS IceCool technology, Military-grade durability, ErgoSense keyboard design, AI Noise-Canceling Technology, Fast connectivity options.",
               "features": [
                   "【Incredible performance】: Equipped with an AMD Ryzen 5 processor and 512GB SSD, this laptop is designed to provide an ultrafast and smooth experience",
                   "【Fast charging battery】: ASUS fast-charge technology can recharge the battery up to 50% capacity in just 30 minutes, allowing you to quickly top it up without interrupting your workflow",
                   "【Extra toughness and durability】: This laptop stays cool in all situations thanks to ASUS IceCool thermal technology, and meets US military-grade standards for longevity and sustainability",
                   "【Effortless typing experience】: The precisely measured and fine-tuned ErgoSense keyboard design reduces strain on your hands and wrists",
                   "【Smooth video call experience】: AI Noise-Canceling Technology isolates unwanted noise for smooth communications",
                   "【Generous screen size】: With its 15.6 inch FHD display and ultra-slim NanoEdge bezels, this laptop offers an immersive visual experience",
                   "【Extensive and stable connectivity】: Stay connected with multiple laptop ports, including USB A, USB C, and HDMI on laptop. Built-in Wi-Fi 6E and Bluetooth 5 offer the most stable and fast connectivity"],
               "generated_review": "Introducing the ASUS 2023 Vivobook Go 15 Laptop! This laptop boasts a lightweight and compact design, perfect for productivity on-the-go. Equipped with standout features like an AMD Ryzen 5 processor, 512GB SSD, and Windows 11 Home, it aims to keep you entertained and efficient wherever you are.\n\n**Common Praises:**\n- Users appreciate the fast performance enabled by the AMD Ryzen 5 processor and 512GB SSD.\n- The fast-charging battery capability stands out, allowing a quick 50% recharge in just 30 minutes.\n- Durability is commended, with ASUS IceCool thermal technology keeping the laptop cool, meeting military-grade standards.\n- The ErgoSense keyboard design reduces hand and wrist strain, enhancing the typing experience.\n- The laptop offers smooth video calls with AI Noise-Canceling Technology.\n- The 15.6-inch FHD display with NanoEdge bezels provides an immersive visual experience.\n- Users value the extensive and stable connectivity options with multiple ports and Wi-Fi 6E.\n\n**Common Critiques:**\n- Some users faced issues where the laptop stopped working after a short period of use.\n- Dissatisfaction was expressed regarding the screen quality being washed out, slow performance, and inaccurate product descriptions.\n\n**User Experience Overview:**\nFeedback indicates a mix of experiences, with users praising the laptop's performance, design, and durability. However, issues like screen quality and misleading product descriptions have been noted, impacting overall user satisfaction.\n\n**User Tips and Recommendations:**\n- Ensure to check the product thoroughly upon receiving it to verify advertised features.\n- Consider investing in a laptop sleeve or protective cover to maintain the laptop's finish.\n- For those sensitive to screen quality, test the display angles to find the best viewing experience.\n- Take advantage of the fast-charging feature to quickly top up the battery when needed.\n- If specific features like a backlit keyboard are essential, verify them before purchase to align expectations.",
               "image_url": "https://m.media-amazon.com/images/I/71tj1W5NoQL.__AC_SX300_SY300_QL70_FMwebp_.jpg",
               "job_id": "f6b42b94-e2f2-4741-a57e-bc0c168bbbe0", "number_of_reviews": "70 ratings",
               "price": {"$numberDouble": "549.99"}, "product_id": "B0BXRD41GM", "qa": [],
               "rating": {"$numberDouble": "4.1"},
               "reviews": [
                   {"rating": {"$numberDouble": "1.0"}, "date": "Reviewed in the United States on February 11, 2024",
                    "text": "I loved it for approximately 30 days, until it stopped working. It would not turn on. Thinking it was the charger, I replaced it. Still nothing.",
                    "author": "Edye"},
                   {"rating": {"$numberDouble": "3.0"}, "date": "Reviewed in the United States on January 9, 2024",
                    "text": "I’m trying to like this laptop but screen quality is washed out and dull and grainy! It’s slow too I’m not satisfied with this purchase at all. Said it’s FHD but I’ve not seen any FHD screen look like this",
                    "author": "Laura"},
                   {"rating": {"$numberDouble": "3.0"}, "date": "Reviewed in the United States on December 8, 2023",
                    "text": "Great when it works but after few days will not turn on. Requested return/ refund from Amazon warranty.",
                    "author": "Conrad San Diego"},
                   {"rating": {"$numberDouble": "2.0"}, "date": "Reviewed in the United States on January 25, 2024",
                    "text": "The laptop works fine so far. But the images were misleading. They show a fingerprint scanner on the track pad (one of the reasons I chose this product) but IT DOES NOT HAVE ONE.Disappointed in the misleading images by the buyer. Let's see how it worksAlso the microsoft license expires on January 31 2024. So it's useless",
                    "author": "jj"},
                   {"rating": {"$numberDouble": "2.0"}, "date": "Reviewed in the United States on October 13, 2023",
                    "text": "Had very good experience with multiple ASUS products in the past, and it has non-glossy screen, thus 2 stars, but this one (ASUS 2023 Vivobook Go 15 Laptop, 15.6” FHD Display, AMD Ryzen 5 7520U Processor, 8GB RAM ...) goes back.I did not test it in depth, as was put off on the very start - the keyboard was nothing like proudly advertised at all - not ErgoSense, not backlit, not dished, just very uncomfortable basic strait cheep old type keys with paint stickers, that start to dissolve very fast. Just horrible. If even the visible outer parts are not as described, how can I trust about quality of insides of that offer?Btw. exterior finish is not good too - shows every touch with every thing, and hard to clean.",
                    "author": "AmazonKunde"},
                   {"rating": {"$numberDouble": "2.0"}, "date": "Reviewed in the United States on December 1, 2023",
                    "text": "The laptop is not as on the website. There is not a fingerprint recognition button",
                    "author": "Brando"},
                   {"rating": {"$numberDouble": "1.0"}, "date": "Reviewed in the United States on December 2, 2023",
                    "text": "Enseñan fotos en la 15.6 con lector de huellas, sin embargo no es asi, falsa publicidad a pesar de que cada toque a la laptop se le marca y muy dificil de limpiar, dura demasiado en cargar tambien",
                    "author": "Starlyn"},
                   {"rating": {"$numberDouble": "1.0"}, "date": "Reviewed in the United States on September 11, 2023",
                    "text": "Had to return because it stopped working in less than the 2 weeks we had it.  It just wouldn’t turn on. I realize it’s the risk you take with electronics. Had no problems returning to Amazon for a refund.",
                    "author": "rachel s."},
                   {"rating": {"$numberDouble": "1.0"}, "date": "Reviewed in the United States on December 8, 2023",
                    "text": "Excellent laptop however it doesn't have a backlit keyboard.", "author": "Techpro"},
                   {"rating": {"$numberDouble": "5.0"}, "date": "Reviewed in the United States on December 17, 2023",
                    "text": "Very satisfied with my purchase.  With some tweaking and setup it's working great.",
                    "author": "Kindle Customer"},
                   {"rating": {"$numberDouble": "5.0"}, "date": "Reviewed in the United States on April 16, 2024",
                    "text": "Personal use.  Works fast, high qualityGreat graphics.", "author": "Amazon Customer"},
                   {"rating": {"$numberDouble": "4.0"}, "date": "Reviewed in the United States on February 28, 2024",
                    "text": "I’ve owned this laptop for two months so far. Here’s what I love: It’s light weight. And it does what we all pray our laptop will do. Work. Every time we open it. It doesn’t get overheated unless I’m working on bed right on my comforter. Yeah I know: don’t do that. And most often I don’t. But I will say even when I do, it’s doesn’t get screaming hot. And of course I move it best I can to keep the vents free.And the battery is amazing. I work for hours on end before it poops out. It boots up fairly quickly and operates without hardly a drag and I’m creating graphic elements and so forth inside of Canva. So, she’s quick. Not lightning, but this is under $500 soooo since that is the case, I’d say, wow, nice on speed!The two bummers are: no lighted keyboard. But, I’m surviving. And then there’s the screen. Don’t get me wrong. It’s got a beautiful picture. The drag is that the angle of preciousness is tricky to land on. When you tilt it exactly where it needs to be you see a clear and amazing picture of what ever you’re looking at. But have it off a bit and well, the colors and so forth are not accurate. The screen has what I’ve taken to call a shadow across it. I don’t know what it’s called when a screen does this and I don’t even care to look the term up. But, when it happens I must mess with the angle so I can see it without it being dark.I’m thankful I could get into a laptop at all because money was not there to get one any better. I just wish that screen wouldn’t be such a bugger bear to get right. I work with graphics/color a ton so to me it matters.However, all said, I’d buy it again and resolve to just deal with the screen. And if you were to ask me, and it would seem you are since you’re reading this review, if you need a laptop and don’t have much to spend this baby will deliver everything you need it to do. Which is to work. And end of day, we all need our laptops to work.",
                    "author": "Theresa Jane"},
                   {"rating": {"$numberDouble": "5.0"}, "date": "Reviewed in the United States on December 1, 2023",
                    "text": "Great lap top computer. Works good. Very fast. Price was reasonable", "author": "Gator"},
                   {"rating": {"$numberDouble": "5.0"}, "date": "Reviewed in the United States on March 4, 2024",
                    "text": "I don't use it but was told  she is happy with ot", "author": "Ma"},
                   {"rating": {"$numberDouble": "5.0"}, "date": "Reviewed in the United States on February 3, 2024",
                    "text": "Si me llegó y no se demoró ni mucho tiempo y sobretodo llegó en buen estado nada de rayaduras ni nada, solo que es un poco feo el material ya que se quedan marcadas las huellas en la computadora",
                    "author": "Nayely Moreira"},
                   {"rating": {"$numberDouble": "4.0"}, "date": "Reviewed in the United States on February 10, 2024",
                    "text": "I was looking for a solid, functional, light, and cheap laptop I could use when I was travelling.  This fits that niche perfectly; great for watching videos, web browsing, basic word/excel/etc. work.  Won't be able to handle anything too intense, and I doubt it would run anything more than the most basic video games (I haven't tried), but for what it is, its  great.",
                    "author": "Kyzzer"},
                   {"rating": {"$numberDouble": "4.0"}, "date": "Reviewed in the United States on January 29, 2024",
                    "text": "Wish the keyboard was back-lit. Otherwise, product is good.", "author": "GEH"},
                   {"rating": {"$numberDouble": "4.0"}, "date": "Reviewed in the United States on August 7, 2023",
                    "text": "This is a zippy laptop and performs fairly well given its size and class of laptop. I would give it a 5 star review if it would have come with current generation WiFi onboard. This laptop only supports 802.11ac (aka WiFi 5) and does not support its newer and much faster 802.11ax (aka WiFi 6). I did not notice this in the product description when ordering it and would have chosen something otherwise had I seen it. I can't think of a reason why Asus would opt to use last generation wireless network technology for a SKU released in 2023 when there shouldn't be much of a cost difference between current and last generation chips.",
                    "author": "Geoffrey Wolf"},
                   {"rating": {"$numberDouble": "5.0"}, "date": "Reviewed in the United States on December 21, 2023",
                    "text": "Excelent", "author": "arturo gonzalez"}], "similar_products": [{
            "title": "ASUS Vivobook 15 Laptop, 15.6â€ FHD (1920 x 1080) Display, Intel Core i3-1215U CPU, Intel UHD Graphics, 8GB RAM, 128GB SSD, Windows 11 Home in S Mode, Quiet Blue, F1504ZA-AS34",
            "image": "https://m.media-amazon.com/images/I/41t96QC2q8L._AC_.jpg",
            "asin": "B0BXRMMNH5",
            "url": "https://www.amazon.com/dp/B0BXRMMNH5",
            "price": "$360.00"}, {
            "title": "ASUS VivoBook 15 Laptop, 15.6\" Display, AMD Ryzen 5 4600H CPU, AMD Radeon GPU, 8GB RAM, 256GB SSD, Windows 11 Home, Quiet Blue, M1502IA-AS51",
            "image": "https://m.media-amazon.com/images/I/41PX3SO9S3L._AC_.jpg",
            "asin": "B09ZKHHPYJ",
            "url": "https://www.amazon.com/dp/B09ZKHHPYJ",
            "price": "$589.99"}, {
            "title": "ASUS Vivobook Laptop, 15.6\" FHD Display, 12th Gen Intel Core i3-1215U Processor, 16GB RAM, 1TB SSD, Webcam, Numeric Keypad, HDMI, Wi-Fi, Windows 11 Home, Blue",
            "image": "https://m.media-amazon.com/images/I/419KrOptWZL._AC_.jpg",
            "asin": "B0CLHBLZ74",
            "url": "https://www.amazon.com/dp/B0CLHBLZ74",
            "price": "$479.00"}, {
            "title": "ASUS VivoBook 15 Thin and Light Laptop, 15.6” FHD Display, Intel i3-1005G1 CPU, 8GB RAM, 128GB SSD, Backlit Keyboard, Fingerprint, Windows 10 Home in S Mode, Slate Gray, F512JA-AS34",
            "image": "https://m.media-amazon.com/images/I/41oaMSUsOVL._AC_.jpg",
            "asin": "B0869L1326",
            "url": "https://www.amazon.com/dp/B0869L1326",
            "price": "$339.00"}, {
            "title": "Acer Aspire 3 A314-23P-R3QA Slim Laptop | 14.0\" Full HD IPS Display | AMD Ryzen 5 7520U Quad-Core Processor | AMD Radeon Graphics | 8GB LPDDR5 | 512GB NVMe SSD | Wi-Fi 6 | Windows 11 Home,Silver",
            "image": "https://m.media-amazon.com/images/I/41YTf4aaHCL._AC_.jpg",
            "asin": "B0BSLVF5F5",
            "url": "https://www.amazon.com/dp/B0BSLVF5F5",
            "price": "$399.99"}],
               "specs": {"ASIN": "B0BXRD41GM", "Customer Reviews": "", "Best Sellers Rank": "",
                         "Date First Available": "March 8, 2023", "Standing screen display size": "‎15.6 Inches",
                         "Screen Resolution": "‎1920 x 1080 pixels", "Max Screen Resolution": "‎1920x1080 Pixels",
                         "Processor": "‎4.3 GHz ryzen_5", "RAM": "‎8 GB LPDDR5", "Memory Speed": "‎2400 MHz",
                         "Hard Drive": "‎512 GB SSD", "Graphics Coprocessor": "‎AMD Radeon Graphics",
                         "Chipset Brand": "‎AMD", "Card Description": "‎Integrated", "Graphics Card Ram Size": "‎6 GB",
                         "Wireless Type": "‎Bluetooth, 802.11ac", "Number of USB 2.0 Ports": "‎1",
                         "Number of USB 3.0 Ports": "‎1", "Brand": "‎ASUS", "Series": "‎Vivobook Go 15",
                         "Item model number": "‎E1504FA-AS52", "Hardware Platform": "‎PC",
                         "Operating System": "‎Windows 11 Home", "Item Weight": "‎3.59 pounds",
                         "Product Dimensions": "‎14.9 x 0.7 x 9.15 inches",
                         "Item Dimensions  LxWxH": "‎14.9 x 0.7 x 9.15 inches", "Color": "‎Mixed Black",
                         "Processor Brand": "‎AMD", "Number of Processors": "‎4", "Computer Memory Type": "‎DDR5 RAM",
                         "Flash Memory Size": "‎512 GB", "Hard Drive Interface": "‎PCIE x 8",
                         "Hard Drive Rotational Speed": "‎7200 RPM", "Optical Drive Type": "‎No Drive",
                         "Voltage": "‎19 Volts", "Batteries": "‎1 Lithium Ion batteries required. (included)"},
               "title": "ASUS 2023 Vivobook Go 15 Laptop, 15.6\" FHD Display, AMD Ryzen 5 7520U Processor, 8GB RAM, 512GB SSD, Windows 11 Home, Mixed Black, E1504FA-AS52",
               "updated_at": {"$date": {"$numberLong": "1713613484336"}},
               "user_id": "google-oauth2|118073797812544616922",
               "variants": {"Style:": [{"name": "15.6\" | Ryzen 5"}, {"name": "16\" | Ryzen 5"}]}}

    # inside the prompt has a placeholder for the {{product}} object
    # replace the placeholder with the product object
    prompts = [prompt.replace("{{product}}", str(product)) for prompt in prompts]
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
    for prompt in prompts:
        conversation = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": f"{product}"
            }
        ]
        # chat_completion = client.chat.completions.create(
        #     messages=[
        #         {
        #             "role": "system",
        #             "content": prompt
        #         },
        #         {
        #             "role": "user",
        #             "content": f"{product}"
        #         }
        #     ],
        #     model="mixtral-8x7b-32768",
        # )
        # print(chat_completion.choices[0].message.content)
        # response = await LLMService.make_llm_request(conversation)
        # use asyncio to run the function in an event loop
        response = await LLMService.make_llm_request(conversation)
        print(response + "\n\n")


def test_reviews():
    asyncio.run(test_generate_reviews())
