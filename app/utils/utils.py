import re


def extract_asin_from_url(url):
    """
    Extracts the Amazon Standard Identification Number (ASIN) from an Amazon product URL that contains '/dp/'.

    Parameters:
        url (str): The Amazon product URL from which the ASIN is to be extracted, expecting a '/dp/' segment.

    Returns:
        str: The ASIN if found, otherwise None.
    """
    try:
        # Decode URL-encoded characters
        from urllib.parse import unquote
        url = unquote(url)

        # Define the regular expression pattern to match an ASIN in the Amazon product URL specifically after '/dp/'
        pattern = r'/dp/([A-Z0-9]{10})'
        match = re.search(pattern, url)

        # Return the ASIN if found
        return match.group(1) if match else None
    except Exception as e:
        print(f"Error extracting ASIN: {e}")
        return None


def make_affiliate_link(url, affiliate_tag=None):
    if not affiliate_tag:
        affiliate_tag = '070777-20'
    return f"{url}?tag={affiliate_tag}"


def make_affiliate_link_from_asin(asin, affiliate_tag=None):
    if not affiliate_tag:
        affiliate_tag = '070777-20'
    return f"https://www.amazon.com/dp/{asin}?tag={affiliate_tag}"
