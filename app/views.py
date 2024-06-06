import uuid
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.http.response import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from .models import Products, Reviews
from django.db.models import Q
import random
from .toxic_ingredients import toxic_ingredients as TOXIC_INGREDIENTS
from .utils import get_products, handle_uploaded_file
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

CATEGORIES = ["food", "snacks", "drinks", "skin care", "personal care"] # Currently used categories
def index(request):
    """
    This the landing page of the website
    Redirects to the home page if valid user is active
    """
    product = Products.objects.last()
    return render(request, 'index.html', {'product': product})

def signup_(request):
    """
    GET:
        Return the signup page
    POST:
        Creates a new account
        Basic validation included
    """
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        cpassword = request.POST['cpassword']

        if User.objects.filter(email=email):
            messages.error(request, 'Email already exists!')
            return render(request, 'signup.html')
        
        if password != cpassword:
            messages.error(request, 'Password mismatch!')
            return render(request, 'signup.html')
        
        user = User.objects.create_user(username=email, email=email, password=password)
        user.save()
        messages.success(request, "Account Created Successfully! Please Login!")
        return render(request, 'login.html')

    return render(request, 'signup.html')

def login_(request):
    """
    GET:
        Return the login page
    POST:
        Authenticates and login the user
    """
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            user = User.objects.filter(username=user.get_username()).first()
            if user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password!")
            return render(request, 'login.html')

    return render(request, 'login.html')

def logout_(request):
    """
    Logouts an active user
    """
    if request.user:
        logout(request)
    messages.success(request, 'You have been logged out.')
    return render(request, 'login.html')

def home(request):
    """
    Returns home page if an active user exists
    """
    if request.user:
        products = get_products()
        random.shuffle(products)
        return render(request, 'home.html', {'categories': CATEGORIES, 'products': products[:12]})
    return redirect('login')

def admin_dashboard(request):
    """
    Returns admin dashboard only if a superuser logins
    """
    prods = get_products()
    users = User.objects.all()
    return render(request, 'admin_dashboard.html', {'products': prods,
                                                    'users': users,
                                                    'current_user': request.user})

@csrf_exempt
def add_product(request):
    """
    AJAX request handler for adding products
    """
    if request.method == 'POST':
        try:
            product_id = str(uuid.uuid4())[:8]
            name = request.POST['name']
            image_file = product_id + ".jpg"
            ingredients = request.POST['ingredients']
            category = request.POST['category']
            description = request.POST['description']
            keywords = request.POST['keywords']
            file = request.FILES['image_file']
            handle_uploaded_file(file, image_file)
            toxicity = False
            for i in ingredients.split(','):
                if i.strip().lower() in TOXIC_INGREDIENTS:
                    toxicity = True
            
            product = Products(
                product_id=product_id,
                name=name,
                image_file=image_file,
                ingredients=ingredients.lower(),
                category=category,
                description=description,
                toxicity=toxicity,
                keywords=keywords
            )
            product.save()

            return JsonResponse({'msg': "Product Added Successfully!"})
        except Exception as e:
            print(e)
            return JsonResponse({'msg': "Error!"})
    else:
        return JsonResponse({'msg': "Invalid request method."})

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from .models import Products

def recommend_safe_products(product_id):
    products = Products.objects.all()

    # Prepare data
    data = {
        'product_id': [product.product_id for product in products],
        'name': [product.name for product in products],
        'ingredients': [product.ingredients for product in products],
        'category': [product.category for product in products],
        'description': [product.description for product in products],
        'avg_rating': [product.avg_rating for product in products],
        'toxicity': [product.toxicity for product in products],
        'keywords': [product.keywords for product in products],
    }

    df = pd.DataFrame(data)

    # Get the input product's details
    input_product = df[df['product_id'] == product_id].iloc[0]
    input_category = input_product['category']

    # Combine relevant features for vectorization
    df['combined_features'] = df['keywords']

    # Vectorize combined features
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['combined_features'])

    # Compute similarity matrix
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # Get the index of the product that matches the product_id
    idx = df.index[df['product_id'] == product_id].tolist()[0]

    # Get the pairwise similarity scores of all products with that product
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Sort the products based on the similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the scores of the top 5 most similar products
    sim_scores = sim_scores[1:6]

    # Get the product indices
    product_indices = [i[0] for i in sim_scores]

    # Filter recommendations by category and sub-category if available
    recommended_products = df.iloc[product_indices]
    category_filtered_recommendations = recommended_products[recommended_products['category'] == input_category]

    # Filter out toxic products
    safe_recommendations_ids = category_filtered_recommendations[category_filtered_recommendations['toxicity'] == False]['product_id'].tolist()
    print(safe_recommendations_ids)

    # Use Django ORM to get the actual product instances
    safe_recommendations = Products.objects.filter(product_id=safe_recommendations_ids[0])

    return safe_recommendations


    
def product_details(request, product_id):
    """
    Returns detailed info a product
    """
    product = get_products(product_id)
    reviews = Reviews.objects.filter(product=get_object_or_404(Products, product_id=product_id))
    has_reviewed = reviews.filter(reviewer=request.user.username).first()
    print(has_reviewed)
    if product[0]['toxicity']:
        safe_recommendations = recommend_safe_products(product_id)
    else:
        safe_recommendations = None
    return render(request, 'product_details.html', {'categories': CATEGORIES,
                                                    'product': product[0],
                                                    'reviews': reviews,
                                                    'has_reviewed': has_reviewed,
                                                    'toxic_ingredients': TOXIC_INGREDIENTS,
                                                    'safe_recommendations': safe_recommendations})

def search(request):
    """
    Returns the search results
    """
    if request.method == 'GET':
        query = request.GET.get('search')
        products = Products.objects.filter(Q(name__icontains=query) | Q(category__icontains=query))
        return render(request, 'search_results.html', {'products': products, 'query': query})

def review(request, product_id):
    """
    Adds review to the database
    Updates the average rating of the product
    """
    if request.method == 'POST':
        rating = request.POST['rating']
        review_content = request.POST['review']
        product = get_object_or_404(Products, product_id=product_id)
        review_id = str(uuid.uuid4())[:8]
        reviews = Reviews(review_id=review_id, 
                          review=review_content, 
                          reviewer=request.user.username,
                          rating=rating,
                          product=product
                        )
        reviews.save()
        product.avg_rating = (float(product.avg_rating)+float(rating)) / 2
        product.save()
        return redirect('product_details', product_id)

    