def job_serializer(job):
    return {
        "id": str(job["_id"]),  # Convert ObjectId to string
        "status": job["status"] if "status" in job else "",
        "start_time": job["start_time"] if "start_time" in job else "",
        "end_time": job["end_time"] if "end_time" in job else "",
        "result": job["result"] if "result" in job else {},
        "url": job["url"] if "url" in job else "",
        "error": job["error"] if "error" in job else {}
    }


def list_jobs_serializer(jobs):
    return [job_serializer(job) for job in jobs]


def product_serializer(product):
    return {
        "id": str(product["_id"]),
        "job_id": product["job_id"] if "job_id" in product else "",
        "product_id": product["product_id"],
        "domain": product["domain"] if "domain" in product else "",
        "title": product["title"],
        "description": product["description"],
        "price": product["price"],
        "image_url": product["image_url"],
        "specs": product["specs"],
        "features": product["features"],
        "reviews": product["reviews"] if "reviews" in product else [],
        "rating": product["rating"],
        "created_at": product["created_at"] if "created_at" in product else "",
        "updated_at": product["updated_at"] if "updated_at" in product else "",
        "generated_review": product["generated_review"] if "generated_review" in product else ""
    }


def list_products_serializer(products):
    return [product_serializer(product) for product in products]
