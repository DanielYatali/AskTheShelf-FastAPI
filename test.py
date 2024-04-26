import json
import time

import requests

#read products from products.txt
#each line has a url
#make a request to http://localhost:8000/api/v1/jobs/ with the url

def read_products():
    with open('products.txt') as f:
        products = f.readlines()
    return products

def main():
    products = read_products()
    for product in products:
        product = product.strip()
        print(product)
        token = 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InZHbENva05kNXktUTA4dzNPZnVBViJ9.eyJlbWFpbCI6ImRhbmllbHlhdGFsaTkwMkBnbWFpbC5jb20iLCJpc3MiOiJodHRwczovL2Rldi1mbzBtN2drZWhhemF5Z3BlLnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExODA3Mzc5NzgxMjU0NDYxNjkyMiIsImF1ZCI6WyJhc2t0aGVzaGVsZi5jb20iLCJodHRwczovL2Rldi1mbzBtN2drZWhhemF5Z3BlLnVzLmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE3MTQwOTYyODksImV4cCI6MTcxNDE4MjY4OSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF6cCI6ImZyMWFXZkhJbGRsVmhRZkpSS0FrU0xUOXlncEZFTWtwIn0.mvFohm6S-zfRhKK4yns-7Bb6BEcN2T_c9jmj34_p6k0J3zEzJpwlHHRhC3yvEQ_bv6QV_uXS8-C65MdcKs4o3bsmHc-2DTbz9H9lX4dQ6A78-C3PF4VtGxkvh4fwgHGfa8-wis2t6XNZiRx3G6lM8cJWt34PCdnMXLQiTVNMOdymHKWxM52Z2Uok9eEGC8Zal4_LdrfRtImIo501iGxC0d9DVXXKiHE4HSrN2kwbpXXD1QLWWEau3pi151c_c0fnP9GM8bIz0QefAuuibErY1bH9mSqiklk44xvrWjudFwZ-7pYMItdefgqRcchQECqagUKsGzYLvbXHUsoS8qzeAA'
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        data = {
            'url': product
        }
        response = requests.post('http://localhost:8000/api/v1/jobs/', headers=headers, data=json.dumps(data))
        print(response.status_code)
        print(response.text)
        print('---')
        time.sleep(5)


if __name__ == '__main__':
    main()
