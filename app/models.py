from django.db import models # type: ignore

# Products model
class Products(models.Model):
    product_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    image_file = models.CharField(max_length=50)
    ingredients = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    avg_rating = models.CharField(max_length=20, default=5.0)
    toxicity = models.BooleanField(default=False)
    keywords = models.CharField(max_length=200, null=True)

# Reviews model
class Reviews(models.Model):
    review_id = models.CharField(max_length=50, unique=True)
    review = models.CharField(max_length=200)
    reviewer = models.CharField(max_length=100)
    rating = models.CharField(max_length=3)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)