import json

import requests

# Replace with your actual AppID
appid = 'DanielYa-askthesh-PRD-ae1d2d212-2fc72fbe'
user_token = 'v^1.1#i^1#p^1#r^0#f^0#I^3#t^H4sIAAAAAAAAAOVYbYwTRRhu7wNC+BCECCFoyiJHvMvuzm637XW5Ftr7oCVwV+hxegSE7e4sXW67u+5sKc1hvBSFGIkJkQORqBcI+PFHc1F+cIqIISAxikhi/MCAMWowfEQk6J2Cu3vl6J0EkGviJfZPM++8887zPPO+M7MDOkaNqdwU2XR1vHN0SVcH6ChxOqmxYMyo8qoJpSXTyx2gwMHZ1fFwR1mu9OcaxKVkjV0KkaYqCLrWp2QFsbYxgKV1hVU5JCFW4VIQsQbPxkOLF7E0AVhNVw2VV2XMFa0LYG4e+BIewStQjDchwoRpVW7EbFYDmI8XKNHrT3jcNMV7vLzZj1AaRhVkcIoRwGhAMzhgcNrdDADrYVi3h2CAbznmaoE6klTFdCEAFrThsvZYvQDr7aFyCEHdMINgwWioId4UitbVNzbXkAWxgnkd4gZnpNHgVq0qQFcLJ6fh7adBtjcbT/M8RAgjg/0zDA7Khm6AuQf4ttQUoKCH9gDI8IASaW9RpGxQ9RRn3B6HZZEEXLRdWagYkpG9k6KmGom1kDfyrUYzRLTOZf0tSXOyJEpQD2D14VBrKBbDgnWcIkG5lcM51GYkIUrisaV1OAcpgRZoisZpkffRYgLmJ+qPlpd5yEy1qiJIlmjI1agaYWiihkO1YQq0MZ2alCY9JBoWokI/Oq+h22/6kTdWMW0kFWtdYcoUwmU377wCA6MNQ5cSaQMORBjaYUsUwDhNkwRsaKedi/n0WY8CWNIwNJYkM5kMkXETqr6GpAGgyMcWL4rzSZjiMNPXqvV+f+nOA3DJpsJDcySSWCOrmVjWm7lqAlDWYEHGz3gYJq/7YFjBodZ/GAo4k4MrolgVkoB+ivd5fQxNA57j/MWokGA+SUkLB0xwWTzF6W3Q0GSOhzhv5lk6BXVJMGOJtLtahLjg9Ys44xdF3NoYcUqEEECYSPD+6v9Todxtqschr0OjKLletDynFmhNIlCURJKTW0gUeiJcFY6oVeI6fz2/NAMW8/5YJLJwnVgVDwXuthpuSb5Wlkxlms35iyGAVevFEyGiIgMKw6IX51UNxlRZ4rMja4HduhDjdCMbh7JsGoZFMqRp0eLs1UWj9y+3iXvjXbwz6j86n27JClkpO7JYWeORGYDTJMI6gQheTZFWraucef2wzKts1MPiLZk31xHF2iTZz1YS+q+chE2XQOt4QodITevmbZtosm5gzWobVMzzzNBVWYZ6CzXsek6l0gaXkOFIK+wiJLjEjbTD1ke5q91ur88zLF68fZSuGmlbUjG24rIF93itJgd/5Acd9o/KOQ+DnPNgidMJasBsahaYOap0WVnpuOlIMiAhcSKBpDWK+e2qQ6INZjVO0ksmO37d3RmpnV7ftL2yvTl7YtdRx7iCN4aulWDawCvDmFJqbMGTA5hxs6ecum/qeJoBDO0GwMO4PcvBrJu9ZdQDZVOYLzs/IDecf+PExt2eD/d0v/7umZemgfEDTk5nuaMs53TUJg+3PdjbdmjyuZ6dG6O9ne3zV++o3JXOOHYs/OybM5/+9PjceRtWb2nYg7/f987Bj7KHZ8wJb7yfeH7SoaprsbceXaFvCmw5/V3j3IZ29+QLv1+aWLF3/8XcyS2tHdNePPnDwtmTXBXbo93g1K7Lx365fmHz5Sszu7/6o2+fx3utr/WZJ3tqej7ZubV0T8+2rjBJbD5+YP6zDwnOee9duvLnK5MO/PgUk/nt86sVvRtenbr1aMtzFx/JXDo7+9tcdyPReZ5p933/V+XTfPCIXjHnhZf3nz1SrvUeW7aaWZmrPjdhrni8/O0l7UuOXD8UJRZV7A+Pfu3r+RFXX+T02lUrprx5Kr4tMDG+74v2j/v29q/l3+uZuAD9EQAA'
item_id = '186399645033'  # Use the item ID from your previous JSON snippet

# The URL for the GetSingleItem call of the eBay Shopping API
url = 'https://open.api.ebay.com/shopping'
headers = {
    'X-EBAY-API-APP-ID': appid,
    'X-EBAY-API-CALL-NAME': 'GetSingleItem',
    'X-EBAY-API-SITE-ID': '0',  # This is usually '0' for eBay US
    'X-EBAY-API-VERSION': '863',  # You can find the latest version number in the API documentation
    'X-EBAY-API-REQUEST-ENCODING': 'JSON',
    'X-EBAY-API-IAF-TOKEN': f'Bearer {user_token}',  # Include the token in the Authorization header if needed
    'Content-Type': 'application/json'
}
# The body of the POST request
data = json.dumps({
    'ItemID': item_id,
    'IncludeSelector': 'Details,ItemSpecifics,TextDescription,ShippingCosts'  # Specify additional info
})

# Make the POST request to the eBay Shopping API
response = requests.post(url, headers=headers, data=data)

# Check if the request was successful
if response.status_code == 200:
    item_details = response.json()  # Parse the JSON response
    print(item_details)  # Print the detailed item data
else:
    print(f"Error: {response.status_code}")
    print(response.text)  # To get more detail on the error

# keywords = 'iphone'
#
# # Construct the request URL for the Finding API
# url = f'https://svcs.ebay.com/services/search/FindingService/v1'
# params = {
#     'OPERATION-NAME': 'findItemsByKeywords',
#     'SERVICE-VERSION': '1.13.0',
#     'SECURITY-APPNAME': appid,
#     'RESPONSE-DATA-FORMAT': 'JSON',
#     'REST-PAYLOAD': '',
#     'keywords': keywords
# }
#
# # The actual call to eBay Finding API would look like this:
# response = requests.get(url, params=params)
# response_json = response.json()
#
# # # Simulated response for demonstration:
# # response_json = {
# #     "findItemsByKeywordsResponse": [
# #         {
# #             "searchResult": [
# #                 {
# #                     "@count": "1",
# #                     "item": [
# #                         {
# #                             "title": "Example iPhone",
# #                             "itemId": "1234567890",
# #                             "sellingStatus": {
# #                                 "currentPrice": {
# #                                     "@currencyId": "USD",
# #                                     "__value__": "200.00"
# #                                 }
# #                             },
# #                             "viewItemURL": "http://example.com/iphone",
# #                         }
# #                     ]
# #                 }
# #             ]
# #         }
# #     ]
# # }
# #
# # Extracting the search results
# search_results = response_json['findItemsByKeywordsResponse'][0]['searchResult'][0]['item']
# print(search_results[0])
# Displaying the search results
# for item in search_results:
#     print(f"Title: {item['title']}")
#     print(f"Item ID: {item['itemId']}")
#     print(f"Price: {item['sellingStatus']['currentPrice']['__value__']} {item['sellingStatus']['currentPrice']['@currencyId']}")
#     print(f"URL: {item['viewItemURL']}\n")
