import os
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count
from products.services import get_or_fetch_product
from products.models import ScanHistory, Product
from .gemini_service import (
    ask_gemini, 
    analyze_food_product, 
    compare_products_gemini, 
    generate_insights_gemini
)


def gemini_test_view(request):
    """
    Test endpoint for verifying Django connection to Google Gemini API.
    """
    test_prompt = "Explain in 2 simple sentences why protein is important for the human body."
    
    ai_response = ask_gemini(test_prompt)

    if ai_response:
        return JsonResponse({
            "success": True,
            "response": ai_response
        })
    else:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key or api_key == "PASTE_MY_GEMINI_API_KEY_HERE":
            return JsonResponse({
                "success": False,
                "message": "Gemini API key is not configured in .env file. Please set GEMINI_API_KEY in .env."
            }, status=500)
        return JsonResponse({
            "success": False,
            "message": "Unable to get AI response"
        }, status=500)


def product_health_analysis_view(request, barcode):
    """
    Given a barcode:
    1. Fetch product from PostgreSQL DB or Open Food Facts API.
    2. Read logged-in user's UserProfile (if authenticated).
    3. Analyze product using Gemini AI personalized with user profile.
    4. Return structured product data & health analysis JSON.
    """
    print("Analysis request barcode:", barcode)

    # 1. Get or fetch product
    product, source = get_or_fetch_product(barcode)

    if not product:
        print("Product lookup failed for barcode:", barcode)
        return JsonResponse({
            "success": False,
            "message": "Product not found"
        }, status=404)

    print("Product loaded:", product.product_name)

    # 2. Extract logged-in user's UserProfile if available
    user_profile = None
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        user_profile = request.user.profile

    # 3. Perform Gemini AI health analysis
    analysis_data = analyze_food_product(product, user_profile=user_profile)

    if not analysis_data:
        print("[View Error] Gemini analysis failed or returned None.")
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key or api_key == "PASTE_MY_GEMINI_API_KEY_HERE":
            return JsonResponse({
                "success": False,
                "message": "Gemini API key is not configured in .env file. Please set GEMINI_API_KEY in .env."
            }, status=500)
        return JsonResponse({
            "success": False,
            "message": "Unable to perform health analysis"
        }, status=500)

    # 4. Fallback for personalized_note if unauthenticated
    if not request.user.is_authenticated and not analysis_data.get("personalized_note"):
        analysis_data["personalized_note"] = "Log in and complete your profile for more personalized guidance."

    # 5. Save scan history for authenticated users
    if request.user.is_authenticated:
        try:
            from django.utils import timezone
            from datetime import timedelta
            from products.models import ScanHistory

            rating = analysis_data.get("overall_rating", "")
            summary = analysis_data.get("summary", "")

            # Avoid duplicate entries within 60 seconds for the same product
            recent_scan = ScanHistory.objects.filter(
                user=request.user,
                product=product,
                scanned_at__gte=timezone.now() - timedelta(seconds=60)
            ).first()

            if recent_scan:
                recent_scan.analysis_rating = rating
                recent_scan.analysis_summary = summary
                recent_scan.save()
            else:
                ScanHistory.objects.create(
                    user=request.user,
                    product=product,
                    analysis_rating=rating,
                    analysis_summary=summary
                )
        except Exception as e:
            print(f"[ScanHistory Error] Failed to save scan history: {e}")

    # 6. Return combined response
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
        },
        "analysis": analysis_data
    })


def product_comparison_analysis_view(request, barcode_a, barcode_b):
    """
    Compares two products via Gemini AI.
    Does NOT create ScanHistory items.
    Returns JSON response containing comparison analysis.
    """
    if barcode_a == barcode_b:
        return JsonResponse({
            "success": False,
            "message": "Please select two different products to compare."
        }, status=400)

    product_a, _ = get_or_fetch_product(barcode_a)
    product_b, _ = get_or_fetch_product(barcode_b)

    if not product_a or not product_b:
        return JsonResponse({
            "success": False,
            "message": "One or both products could not be found."
        }, status=404)

    user_profile = None
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        user_profile = request.user.profile

    comparison_data = compare_products_gemini(product_a, product_b, user_profile=user_profile)

    if not comparison_data:
        return JsonResponse({
            "success": False,
            "message": "Unable to perform AI product comparison at this time."
        }, status=500)

    return JsonResponse({
        "success": True,
        "product_a": {
            "name": product_a.product_name,
            "brand": product_a.brand,
            "barcode": product_a.barcode,
        },
        "product_b": {
            "name": product_b.product_name,
            "brand": product_b.brand,
            "barcode": product_b.barcode,
        },
        "comparison": comparison_data
    })


@login_required
def generate_ai_insights_view(request):
    """
    Generates AI educational insights for the logged-in user based on their aggregated scan data.
    Does NOT expose raw PII, passwords, or emails to Gemini.
    """
    date_range = request.GET.get('range', '30')
    if request.method == 'POST':
        date_range = request.POST.get('range', date_range)

    now = timezone.now()
    scans_qs = ScanHistory.objects.filter(user=request.user)

    if date_range == '7':
        scans_qs = scans_qs.filter(scanned_at__gte=now - timedelta(days=7))
        range_label = "Last 7 Days"
    elif date_range == 'all':
        range_label = "All Time"
    else:
        scans_qs = scans_qs.filter(scanned_at__gte=now - timedelta(days=30))
        range_label = "Last 30 Days"

    total_scans = scans_qs.count()
    if total_scans == 0:
        return JsonResponse({
            "success": False,
            "message": "No scan history available for this date range to generate insights."
        }, status=400)

    analyzed_scans = scans_qs.exclude(analysis_rating='').exclude(analysis_rating__isnull=True).count()

    rating_counts = {
        "good_choice": scans_qs.filter(analysis_rating='Good Choice').count(),
        "moderate": scans_qs.filter(analysis_rating='Moderate').count(),
        "limit_intake": scans_qs.filter(analysis_rating='Limit Intake').count(),
    }

    # Unique products scanned in date range
    unique_product_ids = scans_qs.values_list('product_id', flat=True).distinct()
    unique_products = Product.objects.filter(id__in=unique_product_ids)

    def get_avg(field_name):
        val = unique_products.aggregate(avg_val=Avg(field_name))['avg_val']
        return round(val, 1) if val is not None else 'N/A'

    avg_nutrition = {
        "calories": get_avg('calories'),
        "protein": get_avg('protein'),
        "carbohydrates": get_avg('carbohydrates'),
        "fat": get_avg('fat'),
        "saturated_fat": get_avg('saturated_fat'),
        "sugar": get_avg('sugar'),
        "fiber": get_avg('fiber'),
        "sodium": get_avg('sodium'),
    }

    # Top 5 product names
    top_scans = (
        scans_qs
        .values('product__product_name')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')[:5]
    )
    top_product_names = [item['product__product_name'] for item in top_scans if item['product__product_name']]

    stats_payload = {
        "date_range_label": range_label,
        "total_scans": total_scans,
        "analyzed_scans": analyzed_scans,
        "rating_dist": rating_counts,
        "avg_nutrition": avg_nutrition,
        "top_products": top_product_names,
    }

    insights_data = generate_insights_gemini(stats_payload)

    if not insights_data:
        return JsonResponse({
            "success": False,
            "message": "Unable to generate AI insights at this time. Please try again later."
        }, status=500)

    return JsonResponse({
        "success": True,
        "insights": insights_data
    })

