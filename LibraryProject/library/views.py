from django.shortcuts import render, redirect
from .models import Book
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import Borrow
from django.db.models import Q
from .models import Review
from .models import Reservation
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count, F, Q, Avg, Case, When, Value, IntegerField
from django.core.mail import send_mail

def book_list(request):
    
    books = Book.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        borrow_count=Count('borrow')
    )
    
    
    search_query = request.GET.get('search', '')
    genre_query = request.GET.get('genre', '')
    year_query = request.GET.get('year', '')

    
    if search_query:
        books = books.filter(Q(title__icontains=search_query) | Q(author__icontains=search_query))
    
    
    if genre_query:
        books = books.filter(genre__icontains=genre_query)
        
    
    if year_query:
        
        books = books.filter(publish_date__year=year_query)
    
    
    if request.user.is_authenticated:
        
        user_borrows = Borrow.objects.filter(user=request.user)
        
        if user_borrows.exists():
            borrowed_book_ids = user_borrows.values_list('book_id', flat=True)
            
            preferred_genres = list(Book.objects.filter(id__in=borrowed_book_ids).values_list('genre', flat=True).distinct())
            
            
            books = books.annotate(
                is_preferred=Case(
                    When(genre__in=preferred_genres, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('-is_preferred', '-avg_rating', '-borrow_count')
            
        else:
            
            books = books.annotate(is_preferred=Value(0, output_field=IntegerField())).order_by('-avg_rating', '-borrow_count')
    else:
        
        books = books.annotate(is_preferred=Value(0, output_field=IntegerField())).order_by('-avg_rating', '-borrow_count')
        
    return render(request, 'library/book_list.html', {'books': books})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            
            subject = 'به کتابخانه آنلاین خوش آمدید!'
            message = f'سلام {user.username} عزیز،\nثبت‌نام شما در سامانه مدیریت کتابخانه با موفقیت انجام شد.\nامیدواریم از مطالعه کتاب‌ها لذت ببرید!'
            recipient_list = [user.email if user.email else 'user@test.com']
            
            send_mail(subject, message, 'library@mysite.com', recipient_list)
            
            
            messages.success(request, 'ثبت‌نام شما با موفقیت انجام شد. اکنون می‌توانید وارد شوید.')
            return redirect('login')
    else:
        form = UserCreationForm()
    
    return render(request, 'library/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            
            user = form.get_user()
            
            login(request, user)
            return redirect('book_list')
    else:
        form = AuthenticationForm()
    
    return render(request, 'library/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('book_list')


@login_required(login_url='login')
def borrow_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    if book.available_copies > 0:
        due_date = timezone.now().date() + timedelta(days=14)
        
        
        Borrow.objects.create(
            user=request.user,
            book=book,
            due_date=due_date
        )
        
        book.available_copies -= 1
        book.save()
        
        
        subject = f'رسید امانت کتاب: {book.title}'
        message = f'کاربر گرامی {request.user.username}،\n\n' \
                  f'کتاب "{book.title}" با موفقیت به نام شما امانت ثبت شد.\n' \
                  f'مهلت بازگرداندن کتاب: {due_date} (۱۴ روز آینده)\n\n' \
                  f'لطفاً در موعد مقرر نسبت به بازگرداندن کتاب اقدام کنید تا مشمول جریمه دیرکرد نشوید.'
        
        recipient_list = [request.user.email if request.user.email else 'user@test.com']
        
        send_mail(subject, message, 'library@mysite.com', recipient_list)
        
        
        messages.success(request, f'کتاب "{book.title}" با موفقیت امانت گرفته شد و رسید آن برای شما ایمیل شد.')
        
    return redirect('book_list')

@login_required(login_url='login')
def user_dashboard(request):
    
    user_borrows = Borrow.objects.filter(user=request.user).order_by('-borrow_date')
    
    user_reservations = Reservation.objects.filter(user=request.user, is_active=True).order_by('-created_at')
    
    
    borrowed_book_ids = user_borrows.values_list('book_id', flat=True)
    
    
    borrowed_genres = Book.objects.filter(id__in=borrowed_book_ids).values_list('genre', flat=True).distinct()
    
    
    recommended_books = Book.objects.filter(
        genre__in=borrowed_genres
    ).exclude(
        id__in=borrowed_book_ids
    ).distinct()[:3]
    
    
    if not recommended_books.exists():
        
        recommended_books = Book.objects.exclude(id__in=borrowed_book_ids).order_by('?')[:3]
        
    return render(request, 'library/dashboard.html', {
        'borrows': user_borrows,
        'recommended_books': recommended_books,
        'reservations': user_reservations
    })

@login_required(login_url='login')
def return_book(request, borrow_id):
    borrow_record = get_object_or_404(Borrow, id=borrow_id, user=request.user)
    
    if not borrow_record.is_returned:
        
        borrow_record.is_returned = True
        borrow_record.return_date = timezone.now().date()
        
        
        delay_days = (borrow_record.return_date - borrow_record.due_date).days
        if delay_days > 0:
            borrow_record.penalty_amount = delay_days * 5000
            
        borrow_record.save()
        
        
        borrow_record.book.available_copies += 1
        borrow_record.book.save()
        
    return redirect('dashboard')

@login_required(login_url='login')
def pay_penalty(request, borrow_id):
    
    borrow_record = get_object_or_404(Borrow, id=borrow_id, user=request.user)
    
    
    if borrow_record.penalty_amount > 0 and not borrow_record.is_penalty_paid:
        
        borrow_record.is_penalty_paid = True
        borrow_record.save()
        
    
    return redirect('dashboard')

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    reviews = book.reviews.all().order_by('-created_at')
    
    
    if request.method == 'POST' and request.user.is_authenticated:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            
            Review.objects.create(book=book, user=request.user, rating=rating, comment=comment)
            return redirect('book_detail', book_id=book.id)
            
    return render(request, 'library/book_detail.html', {'book': book, 'reviews': reviews})


@login_required(login_url='login')
def reserve_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    
    if book.available_copies == 0:
        
        already_reserved = Reservation.objects.filter(user=request.user, book=book, is_active=True).exists()
        
        if not already_reserved:
            Reservation.objects.create(user=request.user, book=book)
            
            messages.success(request, f'شما با موفقیت در صف رزرو کتاب "{book.title}" قرار گرفتید.')
        else:
            
            messages.warning(request, 'شما قبلاً این کتاب را رزرو کرده‌اید و در صف انتظار هستید!')   
    return redirect(request.META.get('HTTP_REFERER', 'book_list'))

@login_required(login_url='login')
def cancel_reservation(request, reservation_id):
    
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user, is_active=True)
    
    
    book_title = reservation.book.title
    
    
    reservation.delete()
    
    
    messages.success(request, f'رزرو کتاب "{book_title}" با موفقیت لغو شد و از صف انتظار خارج شدید.')
    
    return redirect('dashboard')

@staff_member_required(login_url='login')
def manager_dashboard(request):
    
    total_books = Book.objects.count()
    total_users = User.objects.count()
    active_borrows = Borrow.objects.filter(is_returned=False).count()
    
    
    unpaid_penalties = Borrow.objects.filter(is_penalty_paid=False).aggregate(total=Sum('penalty_amount'))['total']
    if unpaid_penalties is None:
        unpaid_penalties = 0

    
    recent_borrows = Borrow.objects.all().order_by('-borrow_date')[:]

    
    all_books_inventory = Book.objects.annotate(
        borrowed_count=F('total_copies') - F('available_copies'),
        active_reservations=Count('reservation', filter=Q(reservation__is_active=True))
    ).order_by('-total_copies')

    
    today = timezone.now().date()
    delayed_borrows = Borrow.objects.filter(is_returned=False, due_date__lt=today).order_by('due_date')

   
    popular_books = Book.objects.annotate(borrow_count=Count('borrow')).order_by('-borrow_count')[:]

    
    top_users = User.objects.annotate(borrow_count=Count('borrow')).order_by('-borrow_count')[:]
    
    recent_reviews = Review.objects.select_related('user', 'book').order_by('-created_at')[:]
    context = {
        'total_books': total_books,
        'total_users': total_users,
        'active_borrows': active_borrows,
        'unpaid_penalties': unpaid_penalties,
        'recent_borrows': recent_borrows,
        'all_books_inventory': all_books_inventory,
        'delayed_borrows': delayed_borrows,
        'popular_books': popular_books,
        'top_users': top_users,
        'recent_reviews': recent_reviews,
    }
    
    return render(request, 'library/manager_dashboard.html', context)