import re


def extract_asin_from_url(url):
    # Define the regular expression pattern to match an ASIN in the Amazon product URL
    pattern = r'/dp/([A-Z0-9]{10})'

    # Use the re.search() method to find the first occurrence of the pattern
    match = re.search(pattern, url)

    # If a match is found, return the first capturing group (ASIN), otherwise return None
    return match.group(1) if match else None
