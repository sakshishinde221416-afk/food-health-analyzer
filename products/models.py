from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    barcode = models.CharField(max_length=50, unique=True)
    product_name = models.CharField(max_length=200)
    brand = models.CharField(max_length=200, blank=True)
    ingredients = models.TextField(blank=True)
    
    # Nutritional information (per serving / 100g)
    calories = models.FloatField(null=True, blank=True)
    protein = models.FloatField(null=True, blank=True)
    carbohydrates = models.FloatField(null=True, blank=True)
    fat = models.FloatField(null=True, blank=True)
    saturated_fat = models.FloatField(null=True, blank=True)
    sugar = models.FloatField(null=True, blank=True)
    fiber = models.FloatField(null=True, blank=True)
    sodium = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_name} ({self.barcode})"


class ScanHistory(models.Model):
    """Stores scan & AI analysis history for authenticated users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scan_history')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='scans')
    scanned_at = models.DateTimeField(auto_now_add=True)
    analysis_rating = models.CharField(max_length=50, blank=True)
    analysis_summary = models.TextField(blank=True)

    class Meta:
        ordering = ['-scanned_at']

    def __str__(self):
        return f"{self.user.username} scanned {self.product.product_name}"


class FavoriteProduct(models.Model):
    """Stores user's saved/favorite products."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} saved {self.product.product_name}"

