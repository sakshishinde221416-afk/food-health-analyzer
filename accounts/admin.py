from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'age', 'gender', 'dietary_preference', 
        'has_diabetes', 'has_hypertension', 'has_high_cholesterol', 'has_heart_condition', 
        'food_allergies', 'updated_at'
    )
    search_fields = ('user__username', 'user__email', 'dietary_preference', 'food_allergies', 'other_health_notes')
    list_filter = ('has_diabetes', 'has_hypertension', 'has_high_cholesterol', 'has_heart_condition', 'dietary_preference')
