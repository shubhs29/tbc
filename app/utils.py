"""
This file contains helper functions for our app
"""

import os
from .models import Products
from thrivebychoice.settings import BASE_DIR
STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')


def handle_uploaded_file(file, file_name):
    """
    Args:
        file: FILES - file object from http request
        file_name: str - name of the file to be saved
    Writes the image in local drive
    """
    with open(os.path.join(STATIC_DIR, file_name), 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

def get_products(product_id=None):
    """
    Args:
        product_id: str(optional) - to get single product
    
    Returns a list of product details.
    This function is used to split the ingredients
    into a list.
    """
    if product_id:
        products = Products.objects.filter(product_id=product_id)
    else:
        products = Products.objects.all()
    prods = []
    for i in products:
        ingredients = [x.strip().lower() for x in i.ingredients.strip().split(",")]
        data = {
            "name": i.name,
            "product_id": i.product_id,
            "image_file": i.image_file,
            "category": i.category,
            "description": i.description,
            "ingredients": ingredients,
            "toxicity": i.toxicity,
            "avg_rating": i.avg_rating
        }
        prods.append(data)
    return prods