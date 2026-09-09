from django.contrib import admin
from .models import Product, ScanHistory, FavoriteProduct


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'brand', 'barcode', 'calories', 'protein', 'fat')
    search_fields = ('product_name', 'brand', 'barcode')


@admin.register(ScanHistory)
class ScanHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'analysis_rating', 'scanned_at')
    list_filter = ('analysis_rating', 'scanned_at')
    search_fields = ('user__username', 'product__product_name', 'product__barcode', 'analysis_summary')


@admin.register(FavoriteProduct)
class FavoriteProductAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__product_name', 'product__barcode')


