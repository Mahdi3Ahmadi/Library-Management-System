from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="نام کتاب")
    author = models.CharField(max_length=150, verbose_name="نویسنده")
    genre = models.CharField(max_length=100, verbose_name="ژانر")
    publish_date = models.DateField(verbose_name="تاریخ انتشار")
    total_copies = models.PositiveIntegerField(default=1, verbose_name="تعداد کل نسخه‌ها")
    available_copies = models.PositiveIntegerField(default=1, verbose_name="نسخه‌های قابل امانت")
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True, verbose_name="تصویر جلد")
    description = models.TextField(null=True, blank=True, verbose_name="خلاصه داستان/توضیحات")
    
    def __str__(self):
        return f"{self.title} - {self.author}"
    

class Borrow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="کتاب")
    borrow_date = models.DateField(auto_now_add=True, verbose_name="تاریخ امانت")
    due_date = models.DateField(verbose_name="تاریخ مهلت بازگشت")
    return_date = models.DateField(null=True, blank=True, verbose_name="تاریخ بازگرداندن واقعی")
    is_returned = models.BooleanField(default=False, verbose_name="بازگردانده شده؟")
    penalty_amount = models.PositiveIntegerField(default=0, verbose_name="مبلغ جریمه (تومان)")
    is_penalty_paid = models.BooleanField(default=False, verbose_name="جریمه پرداخت شده؟")

    def __str__(self):
        return f"{self.user.username} امانت گرفته: {self.book.title}"
    
class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews', verbose_name="کتاب")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    rating = models.PositiveIntegerField(verbose_name="امتیاز (۱ تا ۵)")
    comment = models.TextField(verbose_name="متن نظر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.rating} ستاره)" 
    

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="کتاب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ رزرو")
    is_active = models.BooleanField(default=True, verbose_name="در انتظار؟")

    def __str__(self):
        return f"{self.user.username} در صف انتظار: {self.book.title}"