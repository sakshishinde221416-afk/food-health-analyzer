import requests
from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count, Q
from .models import Product, ScanHistory, FavoriteProduct



def home_page_view(request):
    """Renders the public home page."""
    return render(request, 'home.html')


def offline_page_view(request):
    """Renders the simple PWA offline page."""
    return render(request, 'offline.html')


def service_worker_view(request):
    """Serves sw.js from the root URL path (/sw.js) to enable root scope for PWA."""
    sw_path = settings.BASE_DIR / 'static' / 'sw.js'
    return FileResponse(open(sw_path, 'rb'), content_type='application/javascript')



@login_required(login_url='login')
def barcode_search_page_view(request):
    """Renders the HTML page for barcode search and scanner."""
    return render(request, 'products/barcode_search.html')



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator


@login_required(login_url='login')
def scan_history_view(request):
    """
    Displays scan history for logged-in users with search, rating filter, date range filter,
    summary counts, preserved pagination parameters, and responsive layout.
    """
    # Total scans for logged-in user (unfiltered count)
    total_scans_count = ScanHistory.objects.filter(user=request.user).count()

    # Base queryset strictly scoped to request.user
    scans_qs = ScanHistory.objects.filter(user=request.user).select_related('product').order_by('-scanned_at')

    # Extract filter params
    q = request.GET.get('q', '').strip()
    rating = request.GET.get('rating', '').strip()
    range_param = request.GET.get('range', '').strip()

    # Search filter (product_name, brand, barcode)
    if q:
        scans_qs = scans_qs.filter(
            Q(product__product_name__icontains=q) |
            Q(product__brand__icontains=q) |
            Q(product__barcode__icontains=q)
        )

    # Rating filter
    if rating == 'good':
        scans_qs = scans_qs.filter(analysis_rating='Good Choice')
    elif rating == 'moderate':
        scans_qs = scans_qs.filter(analysis_rating='Moderate')
    elif rating == 'limit':
        scans_qs = scans_qs.filter(analysis_rating='Limit Intake')
    elif rating == 'not_analyzed':
        scans_qs = scans_qs.filter(Q(analysis_rating='') | Q(analysis_rating__isnull=True))

    # Date range filter
    now = timezone.now()
    if range_param == '7':
        scans_qs = scans_qs.filter(scanned_at__gte=now - timedelta(days=7))
    elif range_param == '30':
        scans_qs = scans_qs.filter(scanned_at__gte=now - timedelta(days=30))
    elif range_param == '90':
        scans_qs = scans_qs.filter(scanned_at__gte=now - timedelta(days=90))

    matching_scans_count = scans_qs.count()
    has_active_filters = bool(q or rating or range_param)

    # Pagination (10 items per page)
    paginator = Paginator(scans_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'products/scan_history.html', {
        'page_obj': page_obj,
        'q': q,
        'rating': rating,
        'range_param': range_param,
        'total_scans_count': total_scans_count,
        'matching_scans_count': matching_scans_count,
        'has_active_filters': has_active_filters,
    })


@login_required(login_url='login')
def delete_scan_history_item_view(request, item_id):
    """Deletes a single scan history record belonging to the logged-in user."""
    if request.method == 'POST':
        item = get_object_or_404(ScanHistory, id=item_id, user=request.user)
        product_name = item.product.product_name
        item.delete()
        messages.success(request, f"Removed '{product_name}' from your scan history.")
    return redirect('scan_history')


@login_required(login_url='login')
def clear_scan_history_view(request):
    """Clears all scan history records for the logged-in user."""
    if request.method == 'POST':
        deleted_count, _ = ScanHistory.objects.filter(user=request.user).delete()
        if deleted_count > 0:
            messages.success(request, "Your entire scan history has been cleared.")
        else:
            messages.info(request, "Your scan history is already empty.")
    return redirect('scan_history')




def clean_float(val):
    """Safely convert numerical values to float or None."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def fetch_product_from_open_food_facts(barcode):
    """Fetch product details from Open Food Facts API and save to PostgreSQL."""
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    headers = {
        "User-Agent": "FoodHealthApp/1.0 (Contact: admin@foodhealthapp.local)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        if data.get("status") != 1:
            return None

        product_data = data.get("product", {})
        if not product_data:
            return None

        nutriments = product_data.get("nutriments", {})

        product_name = (
            product_data.get("product_name") or
            product_data.get("product_name_en") or
            "Unknown Product"
        )
        brand = product_data.get("brands", "")
        ingredients = (
            product_data.get("ingredients_text") or
            product_data.get("ingredients_text_en") or
            ""
        )

        calories = clean_float(nutriments.get("energy-kcal_100g"))
        if calories is None:
            calories = clean_float(nutriments.get("energy-kcal_value"))

        protein = clean_float(nutriments.get("proteins_100g"))
        carbohydrates = clean_float(nutriments.get("carbohydrates_100g"))
        fat = clean_float(nutriments.get("fat_100g"))
        saturated_fat = clean_float(nutriments.get("saturated-fat_100g"))
        sugar = clean_float(nutriments.get("sugars_100g"))
        fiber = clean_float(nutriments.get("fiber_100g"))
        sodium = clean_float(nutriments.get("sodium_100g"))

        # Save to PostgreSQL database safely without creating duplicates
        product, _ = Product.objects.update_or_create(
            barcode=barcode,
            defaults={
                "product_name": product_name,
                "brand": brand,
                "ingredients": ingredients,
                "calories": calories,
                "protein": protein,
                "carbohydrates": carbohydrates,
                "fat": fat,
                "saturated_fat": saturated_fat,
                "sugar": sugar,
                "fiber": fiber,
                "sodium": sodium,
            }
        )

        return product

    except Exception:
        return None


def barcode_lookup_view(request, barcode):
    """
    Barcode lookup workflow:
    1. Search local PostgreSQL database first.
    2. If missing, fetch from Open Food Facts API.
    3. Save fetched product to PostgreSQL.
    4. Return JSON response with source information and is_saved status.
    """
    product, source = get_or_fetch_product(barcode)

    if not product:
        return JsonResponse({
            "success": False,
            "message": "Product not found"
        }, status=404)

    is_saved = False
    if request.user.is_authenticated:
        is_saved = FavoriteProduct.objects.filter(user=request.user, product=product).exists()

    return JsonResponse({
        "success": True,
        "source": source,
        "product": {
            "barcode": product.barcode,
            "product_name": product.product_name,
            "brand": product.brand,
            "ingredients": product.ingredients,
            "calories": product.calories,
            "protein": product.protein,
            "carbohydrates": product.carbohydrates,
            "fat": product.fat,
            "saturated_fat": product.saturated_fat,
            "sugar": product.sugar,
            "fiber": product.fiber,
            "sodium": product.sodium,
            "is_saved": is_saved,
        }
    })


from .models import FavoriteProduct


@login_required(login_url='login')
def toggle_favorite_view(request, barcode):
    """
    Toggles a product in/out of the logged-in user's favorites.
    Accepts POST request. Returns JSON for AJAX or redirects.
    """
    if request.method == 'POST':
        product, _ = get_or_fetch_product(barcode)
        if not product:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.content_type:
                return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
            messages.error(request, "Product not found.")
            return redirect('barcode_search')

        fav = FavoriteProduct.objects.filter(user=request.user, product=product).first()
        if fav:
            fav.delete()
            saved = False
            msg = f"Removed '{product.product_name}' from saved products."
        else:
            FavoriteProduct.objects.create(user=request.user, product=product)
            saved = True
            msg = f"Saved '{product.product_name}' to your products."

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.content_type:
            return JsonResponse({
                'success': True,
                'saved': saved,
                'message': msg
            })

        messages.success(request, msg)
        next_url = request.POST.get('next', '')
        if next_url:
            return redirect(next_url)

    return redirect('saved_products')


@login_required(login_url='login')
def saved_products_page_view(request):
    """
    Displays the list of saved/favorite products for the logged-in user with pagination.
    """
    favorites_list = FavoriteProduct.objects.filter(user=request.user).select_related('product')
    paginator = Paginator(favorites_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'products/saved_products.html', {
        'page_obj': page_obj
    })


from .services import get_or_fetch_product


def generate_comparison_insights(p1, p2):
    """
    Generates objective, rule-based comparison insights comparing per-100g nutrition values.
    Only generates statements when both products have valid numerical values for that nutrient.
    """
    insights = []

    # Sugar
    if p1.sugar is not None and p2.sugar is not None and p1.sugar != p2.sugar:
        if p1.sugar < p2.sugar:
            insights.append(f"'{p1.product_name}' contains less sugar per 100g ({p1.sugar}g vs {p2.sugar}g).")
        else:
            insights.append(f"'{p2.product_name}' contains less sugar per 100g ({p2.sugar}g vs {p1.sugar}g).")

    # Protein
    if p1.protein is not None and p2.protein is not None and p1.protein != p2.protein:
        if p1.protein > p2.protein:
            insights.append(f"'{p1.product_name}' contains more protein per 100g ({p1.protein}g vs {p2.protein}g).")
        else:
            insights.append(f"'{p2.product_name}' contains more protein per 100g ({p2.protein}g vs {p1.protein}g).")

    # Saturated Fat
    if p1.saturated_fat is not None and p2.saturated_fat is not None and p1.saturated_fat != p2.saturated_fat:
        if p1.saturated_fat < p2.saturated_fat:
            insights.append(f"'{p1.product_name}' contains less saturated fat per 100g ({p1.saturated_fat}g vs {p2.saturated_fat}g).")
        else:
            insights.append(f"'{p2.product_name}' contains less saturated fat per 100g ({p2.saturated_fat}g vs {p1.saturated_fat}g).")

    # Fiber
    if p1.fiber is not None and p2.fiber is not None and p1.fiber != p2.fiber:
        if p1.fiber > p2.fiber:
            insights.append(f"'{p1.product_name}' contains more fiber per 100g ({p1.fiber}g vs {p2.fiber}g).")
        else:
            insights.append(f"'{p2.product_name}' contains more fiber per 100g ({p2.fiber}g vs {p1.fiber}g).")

    # Calories
    if p1.calories is not None and p2.calories is not None and p1.calories != p2.calories:
        if p1.calories < p2.calories:
            insights.append(f"'{p1.product_name}' has lower calories per 100g ({p1.calories} kcal vs {p2.calories} kcal).")
        else:
            insights.append(f"'{p2.product_name}' has lower calories per 100g ({p2.calories} kcal vs {p1.calories} kcal).")

    # Sodium
    if p1.sodium is not None and p2.sodium is not None and p1.sodium != p2.sodium:
        if p1.sodium < p2.sodium:
            insights.append(f"'{p1.product_name}' contains less sodium per 100g ({p1.sodium}g vs {p2.sodium}g).")
        else:
            insights.append(f"'{p2.product_name}' contains less sodium per 100g ({p2.sodium}g vs {p1.sodium}g).")

    return insights


@login_required(login_url='login')
def compare_products_view(request):
    """
    Renders side-by-side comparison page for two products given barcode_a and barcode_b.
    """
    barcode_a = request.GET.get('barcode_a', '').strip()
    barcode_b = request.GET.get('barcode_b', '').strip()

    product_a = None
    product_b = None
    insights = []
    error_msg = None

    if barcode_a or barcode_b:
        if not barcode_a or not barcode_b:
            error_msg = "Please enter both product barcodes to compare."
        elif not barcode_a.isdigit() or not barcode_b.isdigit():
            error_msg = "Barcodes must contain digits only."
        elif barcode_a == barcode_b:
            error_msg = "Please select two different products to compare."
        else:
            product_a, _ = get_or_fetch_product(barcode_a)
            product_b, _ = get_or_fetch_product(barcode_b)

            if not product_a and not product_b:
                error_msg = f"Neither product found for barcodes '{barcode_a}' and '{barcode_b}'."
            elif not product_a:
                error_msg = f"Product A not found for barcode '{barcode_a}'."
            elif not product_b:
                error_msg = f"Product B not found for barcode '{barcode_b}'."
            else:
                insights = generate_comparison_insights(product_a, product_b)

    return render(request, 'products/compare.html', {
        'barcode_a': barcode_a,
        'barcode_b': barcode_b,
        'product_a': product_a,
        'product_b': product_b,
        'insights': insights,
        'error_msg': error_msg,
    })


@login_required(login_url='login')
def food_insights_view(request):
    """
    Renders the My Food Insights page with summary statistics, average nutrition per 100g on unique products,
    rating doughnut chart data, top 5 most scanned products, and transparent rule-based observations.
    """
    range_param = request.GET.get('range', '30')
    now = timezone.now()
    scans_qs = ScanHistory.objects.filter(user=request.user)

    if range_param == '7':
        scans_qs = scans_qs.filter(scanned_at__gte=now - timedelta(days=7))
        date_range_label = "Last 7 Days"
    elif range_param == 'all':
        date_range_label = "All Time"
    else:
        range_param = '30'
        scans_qs = scans_qs.filter(scanned_at__gte=now - timedelta(days=30))
        date_range_label = "Last 30 Days"

    total_scans = scans_qs.count()
    analyzed_scans = scans_qs.exclude(analysis_rating='').exclude(analysis_rating__isnull=True).count()
    saved_products_count = FavoriteProduct.objects.filter(user=request.user).count()

    rating_counts = {
        "good_choice": scans_qs.filter(analysis_rating='Good Choice').count(),
        "moderate": scans_qs.filter(analysis_rating='Moderate').count(),
        "limit_intake": scans_qs.filter(analysis_rating='Limit Intake').count(),
    }

    rating_label_map = {
        "good_choice": "Good Choice",
        "moderate": "Moderate",
        "limit_intake": "Limit Intake"
    }

    most_common_rating = "Not Available"
    if analyzed_scans > 0:
        max_key = max(rating_counts, key=rating_counts.get)
        if rating_counts[max_key] > 0:
            most_common_rating = rating_label_map[max_key]

    # Nutrition Averages for Unique Products in Range
    unique_product_ids = scans_qs.values_list('product_id', flat=True).distinct()
    unique_products = Product.objects.filter(id__in=unique_product_ids)

    def calc_avg(field_name):
        val = unique_products.aggregate(a=Avg(field_name))['a']
        return round(val, 1) if val is not None else None

    avg_calories = calc_avg('calories')
    avg_protein = calc_avg('protein')
    avg_carbs = calc_avg('carbohydrates')
    avg_fat = calc_avg('fat')
    avg_sat_fat = calc_avg('saturated_fat')
    avg_sugar = calc_avg('sugar')
    avg_fiber = calc_avg('fiber')
    avg_sodium = calc_avg('sodium')

    # Top 5 Most Scanned Products for logged-in user in range
    top_scanned_items = (
        scans_qs
        .values('product__product_name', 'product__brand', 'product__barcode')
        .annotate(scan_count=Count('id'))
        .order_by('-scan_count')[:5]
    )

    # Rule-Based Smart Insights
    rule_insights = []
    if total_scans > 0:
        if avg_sugar is not None and avg_sugar >= 12.0:
            rule_insights.append("Many of your recently scanned packaged products contain relatively higher sugar per 100g.")
        if avg_fiber is not None and avg_fiber < 3.0:
            rule_insights.append("Your scanned products generally show lower fiber values.")
        if avg_protein is not None and avg_protein >= 6.0:
            rule_insights.append("Several scanned products contain moderate protein values.")
        if avg_sat_fat is not None and avg_sat_fat >= 5.0:
            rule_insights.append("Among the products you scanned, some have notable saturated fat per 100g.")
        if avg_sodium is not None and avg_sodium >= 0.4:
            rule_insights.append("Some of your scanned products contain higher sodium levels per 100g.")

        if not rule_insights:
            rule_insights.append("Your scanned products show balanced nutrition values across tested categories.")

    context = {
        'range_param': range_param,
        'date_range_label': date_range_label,
        'total_scans': total_scans,
        'analyzed_scans': analyzed_scans,
        'saved_products_count': saved_products_count,
        'most_common_rating': most_common_rating,
        'avg_calories': avg_calories,
        'avg_protein': avg_protein,
        'avg_carbs': avg_carbs,
        'avg_fat': avg_fat,
        'avg_sat_fat': avg_sat_fat,
        'avg_sugar': avg_sugar,
        'avg_fiber': avg_fiber,
        'avg_sodium': avg_sodium,
        'rating_counts': rating_counts,
        'top_scanned_items': top_scanned_items,
        'rule_insights': rule_insights,
    }
    return render(request, 'products/food_insights.html', context)

