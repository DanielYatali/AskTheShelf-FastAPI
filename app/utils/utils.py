import re


def extract_asin_from_url(url):
    url = url.replace('%2F', '/')
    # Define the regular expression pattern to match an ASIN in the Amazon product URL
    pattern = r'/dp/([A-Z0-9]{10})'

    # Use the re.search() method to find the first occurrence of the pattern
    match = re.search(pattern, url)

    # If a match is found, return the first capturing group (ASIN), otherwise return None
    return match.group(1) if match else None


def make_affiliate_link(url, affiliate_tag=None):
    if not affiliate_tag:
        affiliate_tag = '070777-20'
    return f"{url}?tag={affiliate_tag}"
