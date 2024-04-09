# this python file will be used to test the job endpoint
# It will hit the service while it is running and check if the response is as expected
# It will not mock the service
# It will use the actual service
# It will use the actual database

import json
import requests
import pytest
from app.models.job import Job
from app.schemas.job_schema import JobIn, JobRequest

# The URL of the FastAPI app
url = "http://localhost:8000/api/v1/jobs"
token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InZHbENva05kNXktUTA4dzNPZnVBViJ9.eyJlbWFpbCI6ImRhbmllbEBnbWFpbC5jb20iLCJpc3MiOiJodHRwczovL2Rldi1mbzBtN2drZWhhemF5Z3BlLnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJhdXRoMHw2NjEyOTljZmEwMDlkYmI3YjkwZWZmOTMiLCJhdWQiOlsiYXNrdGhlc2hlbGYuY29tIiwiaHR0cHM6Ly9kZXYtZm8wbTdna2VoYXpheWdwZS51cy5hdXRoMC5jb20vdXNlcmluZm8iXSwiaWF0IjoxNzEyNTM1NzIwLCJleHAiOjE3MTI1NDI5MjAsInNjb3BlIjoib3BlbmlkIGVtYWlsIiwiYXpwIjoiZnIxYVdmSElsZGxWaFFmSlJLQWtTTFQ5eWdwRkVNa3AifQ.SPari30KKHIQUSrL94jVTJcocZINRbqnyai86tTVUdcyiUZsPMqrDfkWCyjxN0aQzuo5h9LDU_jkfJVcCo1kw-oHhx-rZYfH-1XvtmMdQMlPrhB1Ejof4Gf4J_klZjR0mY1-XxhQYaP7hg5Q7QHzp66Dgg_yOadITvpGdT9n4ACWrNEeq0EcvstYLNo2htIUOaUnLCdfVjzHdKLVQ65ORnef_OLLAb4UZNV_sf8jok4yStNEDckPC5NAzOLZ4nOwhm7godCW7JGXwmEbJBSzXHaBG_6VULtrKoV3eUfmOwCc7hk6qhKp-VH-ucvPwEscwR0_TIhr9tneImJSXztNvQ"


def test_get_jobs():
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 200


def test_create_job():
    headers = {
        "Authorization": f"Bearer {token}"
    }
    job = JobRequest(
        url="https://example.com",
    )
    response = requests.post(url, headers=headers, data=job.json())
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    assert job_id is not None
    response = requests.get(f"{url}/{job_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["url"] == "https://example.com"


