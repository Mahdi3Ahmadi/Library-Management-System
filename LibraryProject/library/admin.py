from django.contrib import admin
from .models import Book, Borrow, Reservation, Review


admin.site.register(Book)
admin.site.register(Borrow)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    
    list_display = ('book', 'user', 'rating', 'short_comment', 'created_at')
    
    
    list_filter = ('rating', 'created_at')
    
    
    search_fields = ('book__title', 'user__username', 'comment')
    
    
    def short_comment(self, obj):
        if len(obj.comment) > 50:
            return obj.comment[:50] + ' ...'
        return obj.comment
    short_comment.short_description = 'خلاصه نظر'
    
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    
    list_display = ('book', 'user', 'created_at', 'is_active_status')
    
    
    list_filter = ('is_active', 'created_at')
    
    
    search_fields = ('book__title', 'user__username')
    
    
    def is_active_status(self, obj):
        if obj.is_active:
            return "⏳ در انتظار موجودی (فعال)"
        return "✅ تعیین تکلیف شده / لغو شده"
    
    
    is_active_status.short_description = 'وضعیت رزرو'