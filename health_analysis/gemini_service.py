import os
import json
import re
from google import genai
from google.genai import types


def ask_gemini(prompt):
    """
    Helper function to query Google Gemini API safely using gemini-3.6-flash.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "PASTE_MY_GEMINI_API_KEY_HERE":
        print("[Gemini Service Error] GEMINI_API_KEY is missing or set to placeholder in .env")
        return None

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        if response and response.text:
            return response.text.strip()
        return None

    except Exception as e:
        print(f"[Gemini Service Exception] {type(e).__name__}: {e}")
        return None


def analyze_food_product(product, user_profile=None):
    """
    Analyzes a Product object using Gemini AI (gemini-3.6-flash), personalized with user physical metrics,
    health conditions, and food allergies. Returns structured health analysis JSON.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "PASTE_MY_GEMINI_API_KEY_HERE":
        print("[Gemini Service Error] GEMINI_API_KEY is missing or set to default placeholder in .env")
        return None

    def fmt(val, unit=""):
        return f"{val} {unit}".strip() if val is not None else "Not provided"

    # Build profile context if user is logged in & has profile
    if user_profile:
        age_str = fmt(user_profile.age, "years")
        gender_str = user_profile.gender or "Not provided"
        height_str = fmt(user_profile.height_cm, "cm")
        weight_str = fmt(user_profile.weight_kg, "kg")
        dietary_str = user_profile.dietary_preference or "None specified"
        
        allergies_str = user_profile.food_allergies.strip() if user_profile.food_allergies else "None listed"
        notes_str = user_profile.other_health_notes.strip() if user_profile.other_health_notes else "None"

        profile_context_str = f"""
User Profile Context:
- Age: {age_str}
- Gender: {gender_str}
- Height: {height_str}
- Weight: {weight_str}
- Dietary Preference: {dietary_str}

User Known Health Conditions (Self-Reported):
- Diabetes: {"Yes" if user_profile.has_diabetes else "No"}
- Hypertension (High Blood Pressure): {"Yes" if user_profile.has_hypertension else "No"}
- High Cholesterol: {"Yes" if user_profile.has_high_cholesterol else "No"}
- Heart Condition: {"Yes" if user_profile.has_heart_condition else "No"}

Listed Food Allergies: {allergies_str}
Other Health Notes: {notes_str}
"""
    else:
        profile_context_str = "No user profile provided (General public analysis)."

    prompt = f"""
You are an expert educational food nutritionist. Analyze the following food product nutritional data and ingredients:

Product Name: {product.product_name}
Brand: {product.brand or 'Not available'}
Ingredients: {product.ingredients or 'Not available'}

Nutritional Information (per 100g):
- Calories: {fmt(product.calories, 'kcal')}
- Protein: {fmt(product.protein, 'g')}
- Carbohydrates: {fmt(product.carbohydrates, 'g')}
- Fat: {fmt(product.fat, 'g')}
- Saturated Fat: {fmt(product.saturated_fat, 'g')}
- Sugar: {fmt(product.sugar, 'g')}
- Fiber: {fmt(product.fiber, 'g')}
- Sodium: {fmt(product.sodium, 'g')}

{profile_context_str}

IMPORTANT SAFETY AND FORMATTING RULES:
1. Provide GENERAL EDUCATIONAL NUTRITION INFORMATION ONLY. This is NOT a medical diagnosis or medical advice.
2. DO NOT diagnose new conditions. DO NOT make absolute disease claims (e.g. NEVER say "This food will cause diabetes", "You will develop heart disease", or "This product is dangerous for you").
3. Use cautious educational wording like "Frequent intake may contribute to...", "This may be less suitable if consumed often...", "Based on the profile information provided...".
4. ALLERGY CHECK: Carefully compare the user's listed food allergies against the product's listed ingredients.
   - If an ingredient matches an allergy (or derivative), set "allergy_alert": true and populate "allergy_warning" with a clear warning (e.g. "The ingredient list contains peanuts, which matches your peanut allergy.").
   - If no listed allergy is found or no allergies were provided, set "allergy_alert": false and "allergy_warning": "".
5. HEALTH CONDITIONS GUIDANCE: If the user has explicitly reported conditions (Diabetes, Hypertension, High Cholesterol, Heart Condition), populate "condition_specific_notes" with educational guidance relating to sugar, sodium, saturated fat, etc. If no condition applies, keep "condition_specific_notes" empty.
6. "overall_rating" MUST be EXACTLY ONE of: "Good Choice", "Moderate", or "Limit Intake".
7. Return ONLY valid JSON in the exact structure specified below. Do not wrap in extra markdown text outside JSON.

EXACT JSON STRUCTURE:
{{
  "summary": "Brief 2-3 sentence overall nutritional summary.",
  "positive_points": ["Point 1", "Point 2"],
  "concerns": ["Concern 1", "Concern 2"],
  "body_impacts": ["Impact 1", "Impact 2"],
  "possible_long_term_risks": ["Risk 1", "Risk 2"],
  "who_should_be_careful": ["Group 1", "Group 2"],
  "condition_specific_notes": ["Note 1", "Note 2"],
  "consumption_advice": ["Advice 1", "Advice 2"],
  "personalized_note": "Personalized guidance based on user profile or login suggestion.",
  "allergy_alert": false,
  "allergy_warning": "",
  "overall_rating": "Good Choice",
  "disclaimer": "This is general educational nutrition information and does not constitute medical advice. Always verify allergen information on the product packaging."
}}
"""

    try:
        client = genai.Client(api_key=api_key)

        print("Calling Gemini API (gemini-3.6-flash)...")
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
        except Exception as primary_err:
            print(f"[Gemini Service Warning] gemini-3.6-flash call failed ({primary_err}). Trying fallback model gemini-1.5-flash...")
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

        if not response or not response.text:
            print("[Gemini Service Error] Received empty response text from Gemini API.")
            return None

        print("Gemini response received successfully!")
        raw_text = response.text.strip()

        # Clean markdown code fences if present (e.g., ```json ... ```)
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
            raw_text = re.sub(r"\s*```$", "", raw_text)

        try:
            analysis_data = json.loads(raw_text)
        except json.JSONDecodeError as json_err:
            print(f"[Gemini Service Error] Failed to parse JSON response: {json_err}")
            return None

        # Enforce valid overall_rating constraint
        valid_ratings = {"Good Choice", "Moderate", "Limit Intake"}
        if analysis_data.get("overall_rating") not in valid_ratings:
            analysis_data["overall_rating"] = "Moderate"

        # Ensure mandatory keys exist
        if "allergy_alert" not in analysis_data:
            analysis_data["allergy_alert"] = False
        if "allergy_warning" not in analysis_data:
            analysis_data["allergy_warning"] = ""
        if "condition_specific_notes" not in analysis_data or not isinstance(analysis_data["condition_specific_notes"], list):
            analysis_data["condition_specific_notes"] = []

        if "personalized_note" not in analysis_data or not analysis_data["personalized_note"]:
            if not user_profile:
                analysis_data["personalized_note"] = "Log in and complete your profile for more personalized guidance."
            else:
                analysis_data["personalized_note"] = "Personalized evaluation completed based on your profile."

        return analysis_data

    except Exception as e:
        print(f"[Gemini Service Exception] {type(e).__name__}: {e}")
        return None


def compare_products_gemini(product_a, product_b, user_profile=None):
    """
    Compares two food products using Gemini AI and returns balanced educational trade-off analysis.
    Does NOT declare one product universally healthier, avoids medical diagnosis, and respects safety disclaimers.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "PASTE_MY_GEMINI_API_KEY_HERE":
        print("[Gemini Service Error] GEMINI_API_KEY is missing or set to placeholder in .env")
        return None

    def fmt(val, unit=""):
        return f"{val} {unit}".strip() if val is not None else "Not provided"

    # Profile Context
    profile_context_str = "None provided"
    if user_profile:
        age_str = fmt(user_profile.age, "years")
        gender_str = user_profile.gender or "Not provided"
        dietary_str = user_profile.dietary_preference or "None specified"
        allergies_str = user_profile.food_allergies.strip() if user_profile.food_allergies else "None listed"
        notes_str = user_profile.other_health_notes.strip() if user_profile.other_health_notes else "None"

        profile_context_str = f"""
- Age: {age_str}
- Gender: {gender_str}
- Dietary Preference: {dietary_str}
- Known Allergies: {allergies_str}
- Health Notes: {notes_str}
"""

    prompt = f"""
You are an expert, objective food nutrition educator.
Compare the following two packaged food products objectively based on their nutrition facts (per 100g) and ingredient lists.

USER PROFILE:
{profile_context_str}

PRODUCT A:
- Name: {product_a.product_name}
- Brand: {product_a.brand or 'Not available'}
- Barcode: {product_a.barcode}
- Ingredients: {product_a.ingredients or 'Not available'}
- Calories: {fmt(product_a.calories, 'kcal')}
- Protein: {fmt(product_a.protein, 'g')}
- Carbohydrates: {fmt(product_a.carbohydrates, 'g')}
- Total Fat: {fmt(product_a.fat, 'g')}
- Saturated Fat: {fmt(product_a.saturated_fat, 'g')}
- Sugar: {fmt(product_a.sugar, 'g')}
- Fiber: {fmt(product_a.fiber, 'g')}
- Sodium: {fmt(product_a.sodium, 'g')}

PRODUCT B:
- Name: {product_b.product_name}
- Brand: {product_b.brand or 'Not available'}
- Barcode: {product_b.barcode}
- Ingredients: {product_b.ingredients or 'Not available'}
- Calories: {fmt(product_b.calories, 'kcal')}
- Protein: {fmt(product_b.protein, 'g')}
- Carbohydrates: {fmt(product_b.carbohydrates, 'g')}
- Total Fat: {fmt(product_b.fat, 'g')}
- Saturated Fat: {fmt(product_b.saturated_fat, 'g')}
- Sugar: {fmt(product_b.sugar, 'g')}
- Fiber: {fmt(product_b.fiber, 'g')}
- Sodium: {fmt(product_b.sodium, 'g')}

CRITICAL INSTRUCTIONS:
1. Do NOT make medical diagnoses or promise disease cure/prevention.
2. Do NOT declare one product universally healthier or better for everyone. Explain trade-offs objectively using phrases like 'may be a better fit', 'contains less', 'contains more', 'may be worth limiting'.
3. Always return valid JSON only, strictly matching this exact schema:

{{
  "comparison_summary": "Short 2-3 sentence overview of main trade-offs between Product A and Product B.",
  "product_a_strengths": ["List of nutritional or ingredient advantages for Product A"],
  "product_b_strengths": ["List of nutritional or ingredient advantages for Product B"],
  "important_differences": ["Key nutrition or ingredient differences to note"],
  "who_might_prefer_product_a": ["Types of dietary goals/preferences that align with Product A"],
  "who_might_prefer_product_b": ["Types of dietary goals/preferences that align with Product B"],
  "final_note": "A balanced concluding sentence.",
  "disclaimer": "Educational comparison only. Always check product packaging for accurate ingredient and allergen details."
}}
"""

    try:
        client = genai.Client(api_key=api_key)

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
        except Exception:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

        if not response or not response.text:
            return None

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
            raw_text = re.sub(r"\s*```$", "", raw_text)

        comparison_data = json.loads(raw_text)
        return comparison_data

    except Exception as e:
        print(f"[Gemini Comparison Exception] {type(e).__name__}: {e}")
        return None


def generate_insights_gemini(stats_payload):
    """
    Generates an educational AI nutrition summary based strictly on aggregated, anonymous scan statistics.
    Returns structured JSON with keys:
    - summary (string)
    - positive_patterns (list of string)
    - areas_to_consider (list of string)
    - shopping_tip (list of string)
    - comparison_tip (string)
    - disclaimer (string)
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "PASTE_MY_GEMINI_API_KEY_HERE":
        print("[Gemini Service Error] GEMINI_API_KEY is missing or placeholder in .env")
        return None

    date_range_label = stats_payload.get("date_range_label", "Last 30 Days")
    total_scans = stats_payload.get("total_scans", 0)
    analyzed_scans = stats_payload.get("analyzed_scans", 0)
    rating_dist = stats_payload.get("rating_dist", {})
    avg_nutrition = stats_payload.get("avg_nutrition", {})
    top_products = stats_payload.get("top_products", [])

    prompt = f"""
You are an expert food nutrition educator analyzing anonymous, aggregated scan history data for a user.

AGGREGATED ANONYMOUS DATA:
- Date Range: {date_range_label}
- Total Scans Count: {total_scans}
- Analyzed Products Count: {analyzed_scans}
- Scanned Products Rating Breakdown:
  - Good Choice: {rating_dist.get('good_choice', 0)}
  - Moderate: {rating_dist.get('moderate', 0)}
  - Limit Intake: {rating_dist.get('limit_intake', 0)}
- Average Nutrition per 100g across scanned unique products:
  - Calories: {avg_nutrition.get('calories', 'N/A')} kcal
  - Protein: {avg_nutrition.get('protein', 'N/A')} g
  - Carbohydrates: {avg_nutrition.get('carbohydrates', 'N/A')} g
  - Total Fat: {avg_nutrition.get('fat', 'N/A')} g
  - Saturated Fat: {avg_nutrition.get('saturated_fat', 'N/A')} g
  - Sugar: {avg_nutrition.get('sugar', 'N/A')} g
  - Fiber: {avg_nutrition.get('fiber', 'N/A')} g
  - Sodium: {avg_nutrition.get('sodium', 'N/A')} g
- Most Scanned Product Names: {', '.join(top_products) if top_products else 'None'}

CRITICAL MANDATORY INSTRUCTIONS:
1. Provide educational nutrition guidance ONLY.
2. Discuss patterns strictly among the products scanned (e.g. "Based on your scanned products...", "Among the products analyzed...", "This may help you compare future purchases...").
3. NEVER diagnose any disease or medical condition.
4. NEVER predict or claim that the user has any medical condition or definitely ate/consumed these foods.
5. Do NOT refer to personal user identities (no email, username, etc.).
6. Always return valid JSON matching this exact schema:

{{
  "summary": "Educational summary of the nutritional patterns seen in the scanned packaged foods.",
  "positive_patterns": ["List of positive nutritional trends observed among scanned products"],
  "areas_to_consider": ["List of nutritional points to watch or consider when shopping"],
  "shopping_tip": ["Practical tips for evaluating packaged foods next time"],
  "comparison_tip": "A quick tip on how to compare future label choices.",
  "disclaimer": "Educational summary based on scanned packaged product information per 100g. This does not represent total dietary intake and is not medical advice."
}}
"""

    try:
        client = genai.Client(api_key=api_key)

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
        except Exception:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

        if not response or not response.text:
            return None

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
            raw_text = re.sub(r"\s*```$", "", raw_text)

        insights_data = json.loads(raw_text)
        return insights_data

    except Exception as e:
        print(f"[Gemini Insights Exception] {type(e).__name__}: {e}")
        return None


