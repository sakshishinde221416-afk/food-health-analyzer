from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def signup_view(request):
    """Handles new user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Input Validations
        if not username or not email or not password or not confirm_password:
            messages.error(request, "All fields are required.")
            return render(request, 'accounts/signup.html', {'username': username, 'email': email})

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/signup.html', {'username': username, 'email': email})

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken. Please choose another.")
            return render(request, 'accounts/signup.html', {'username': username, 'email': email})

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'accounts/signup.html', {'username': username, 'email': email})

        # Create new user securely (User.objects.create_user handles PBKDF2 hashing)
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Log in automatically after registration & redirect to dashboard
        login(request, user)
        messages.success(request, f"Welcome {username}! Your account was created successfully.")
        return redirect('dashboard')

    return render(request, 'accounts/signup.html')


def login_view(request):
    """Handles user authentication & login."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, 'accounts/login.html', {'username': username})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next', '').strip()
            if not next_url:
                next_url = 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'accounts/login.html', {'username': username})

    return render(request, 'accounts/login.html')


def logout_view(request):
    """Logs the user out and redirects to public home page."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


from datetime import timedelta
from django.utils import timezone
from django.db.models.functions import TruncDate
from django.db.models import Count, Q
from products.models import ScanHistory


@login_required(login_url='login')
def dashboard_view(request):
    """Renders the user dashboard page after login with scan stats, rating chart, activity trend, recent scans, and profile summary."""
    user_scans = ScanHistory.objects.filter(user=request.user)

    scan_stats = user_scans.aggregate(
        total_scans=Count('id'),
        good_choice_count=Count('id', filter=Q(analysis_rating='Good Choice')),
        limit_intake_count=Count('id', filter=Q(analysis_rating='Limit Intake')),
        not_analyzed_count=Count('id', filter=Q(analysis_rating='') | Q(analysis_rating__isnull=True)),
    )

    total_scans = scan_stats['total_scans']
    good_choice_count = scan_stats['good_choice_count']
    limit_intake_count = scan_stats['limit_intake_count']
    not_analyzed_count = scan_stats['not_analyzed_count']
    moderate_count = max(0, total_scans - (good_choice_count + limit_intake_count + not_analyzed_count))

    rating_counts = {
        'total_scans': total_scans,
        'good_choice': good_choice_count,
        'moderate': moderate_count,
        'limit_intake': limit_intake_count,
        'not_analyzed': not_analyzed_count,
    }

    # Generate 7-day Scan Activity Trend Data
    today = timezone.now().date()
    start_date = today - timedelta(days=6)

    activity_qs = (
        user_scans.filter(
            scanned_at__date__gte=start_date,
            scanned_at__date__lte=today
        )
        .annotate(scan_date=TruncDate('scanned_at'))
        .values('scan_date')
        .annotate(count=Count('id'))
    )

    counts_by_date = {item['scan_date']: item['count'] for item in activity_qs}

    activity_labels = []
    activity_counts = []
    total_7day_scans = 0

    for i in range(7):
        day = start_date + timedelta(days=i)
        label_str = day.strftime('%d %b')
        count = counts_by_date.get(day, 0)
        activity_labels.append(label_str)
        activity_counts.append(count)
        total_7day_scans += count

    activity_data = {
        'labels': activity_labels,
        'counts': activity_counts,
        'total_7day_scans': total_7day_scans,
    }

    recent_scans = user_scans.select_related('product')[:5]

    profile = getattr(request.user, 'profile', None)
    is_profile_incomplete = True
    if profile:
        if profile.age or profile.dietary_preference:
            is_profile_incomplete = False

    return render(request, 'accounts/dashboard.html', {
        'recent_scans': recent_scans,
        'profile': profile,
        'is_profile_incomplete': is_profile_incomplete,
        'rating_counts': rating_counts,
        'activity_data': activity_data,
    })




@login_required(login_url='login')
def profile_view(request):
    """Allows authenticated users to view and update their health profile."""
    profile = request.user.profile
    errors = {}

    if request.method == 'POST':
        age_str = request.POST.get('age', '').strip()
        gender = request.POST.get('gender', '').strip()
        height_str = request.POST.get('height_cm', '').strip()
        weight_str = request.POST.get('weight_kg', '').strip()
        dietary_preference = request.POST.get('dietary_preference', '').strip()

        parsed_age = None
        if age_str:
            try:
                val = int(age_str)
                if val <= 0 or val > 120:
                    errors['age'] = "Please enter a valid age between 1 and 120."
                else:
                    parsed_age = val
            except ValueError:
                errors['age'] = "Age must be a valid positive number."

        parsed_height = None
        if height_str:
            try:
                val = float(height_str)
                if val <= 0 or val > 300:
                    errors['height_cm'] = "Height must be a positive number."
                else:
                    parsed_height = val
            except ValueError:
                errors['height_cm'] = "Height must be a valid number."

        parsed_weight = None
        if weight_str:
            try:
                val = float(weight_str)
                if val <= 0 or val > 500:
                    errors['weight_kg'] = "Weight must be a positive number."
                else:
                    parsed_weight = val
            except ValueError:
                errors['weight_kg'] = "Weight must be a valid number."

        if errors:
            messages.error(request, "Please correct the errors highlighted below.")
            return render(request, 'accounts/profile.html', {
                'profile': profile,
                'errors': errors,
            })

        # Save profile fields safely
        profile.age = parsed_age
        profile.gender = gender
        profile.height_cm = parsed_height
        profile.weight_kg = parsed_weight
        profile.dietary_preference = dietary_preference
        profile.has_diabetes = request.POST.get('has_diabetes') == 'on'
        profile.has_hypertension = request.POST.get('has_hypertension') == 'on'
        profile.has_high_cholesterol = request.POST.get('has_high_cholesterol') == 'on'
        profile.has_heart_condition = request.POST.get('has_heart_condition') == 'on'
        profile.food_allergies = request.POST.get('food_allergies', '').strip()
        profile.other_health_notes = request.POST.get('other_health_notes', '').strip()
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('profile')

    return render(request, 'accounts/profile.html', {'profile': profile})

