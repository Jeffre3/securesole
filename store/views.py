from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.views.decorators.http import require_POST
from django.contrib import messages
from django_ratelimit.decorators import ratelimit
from .models import UserActivityLog
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def get_recommended_products(product_id, top_n=3):
    product_descriptions = [f"{p['name']} {p['brand']}" for p in PRODUCTS]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(product_descriptions)

    product_index = next((index for (index, d) in enumerate(PRODUCTS) if d["id"] == product_id), None)
    if product_index is None:
        return []

    cosine_similarities = cosine_similarity(tfidf_matrix[product_index], tfidf_matrix).flatten()
    related_indices = cosine_similarities.argsort()[-top_n-1:-1][::-1]  # Exclude the current product

    return [PRODUCTS[i] for i in related_indices]
# Full product list
PRODUCTS = [
    {'id': 1, 'name': 'Reebok ATR Chill Sneaker', 'brand': 'Reebok', 'price': 59.99, 'image': 'https://images.openai.com/thumbnails/79c12c90c144aad51d57fca6375951ea.webp'},
    {'id': 2, 'name': 'Reebok Floatride Energy 6', 'brand': 'Reebok', 'price': 79.99, 'image': 'https://images.openai.com/thumbnails/3c02529e1e6583ccf331b6ab6252e406.webp'},
    {'id': 3, 'name': 'Reebok Royal BB4500 Hi2 Sneakers', 'brand': 'Reebok', 'price': 45.49, 'image': 'https://images.openai.com/thumbnails/a447a49727fd9f9b5684d1c36f05f5f6.webp'},
    {'id': 4, 'name': 'New Balance Elite Runner X1', 'brand': 'New Balance', 'price': 179.99, 'image': 'https://cdn.prod.website-files.com/624ebfbeeed5677ab444c417/65a528634bfb79d0a604e16a_2024%20shoes%20(15).png'},
    {'id': 5, 'name': 'New Balance AeroTech 5', 'brand': 'New Balance', 'price': 249.99, 'image': 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn:ANd9GcTo4YIFXcOMa4_-jSbUQ2JSJirBa6aBM0lsvpxYL-5ME-eg46f0ovvDgg3n-i8oDPdFWNTMAvaLcaEKcj92AIKlrKM3n2M8FfehAn5DkJwSSwzC_7aoMmcbyyg'},
    {'id': 6, 'name': 'New Balance 530', 'brand': 'New Balance', 'price': 200.99, 'image': 'https://shoenami.com.ph/cdn/shop/files/MR530SH-01.jpg?v=1717153349'},
    {'id': 7, 'name': 'Nike UltraBoost', 'brand': 'Nike', 'price': 69.99, 'image': 'https://shoenami.com.ph/cdn/shop/products/adidasUltraboost21J_CoreBlackCoreBlackCoreBlack_FY5390-3.jpg?v=1656661078'},
    {'id': 8, 'name': 'Nike RS-X', 'brand': 'Nike', 'price': 79.99, 'image': 'https://m.media-amazon.com/images/I/51RTG1X8UAL._AC_SL1000_.jpg'},
    {'id': 9, 'name': 'Nike Classic', 'brand': 'Nike', 'price': 59.99, 'image': 'https://static.nike.com/a/images/t_PDP_936_v1/f_auto,q_auto:eco/fcd8f4ec-1a32-4020-996e-8b8367edae34/NIKE+SB+FC+CLASSIC.png'},
    {'id': 10, 'name': 'Puma Vortex SpeedRunner 5000', 'brand': 'Puma', 'price': 189.99, 'image': 'https://images.puma.com/image/upload/f_auto,q_auto,b_rgb:fafafa,w_2000,h_2000/global/392593/02/sv01/fnd/PHL/fmt/png/Teveris-NITRO-Vortex-Sneakers'},
    {'id': 11, 'name': 'Puma ThunderStrike Fusion', 'brand': 'Puma', 'price': 219.99, 'image': 'https://cdn.shopify.com/s/files/1/0603/3031/1875/products/main-square_3f18bd28-59f1-4813-95d2-618fa335e2e3_540x.jpg?=75&v=1690442506'},
    {'id': 12, 'name': 'Puma AeroPulse Xtreme', 'brand': 'Puma', 'price': 249.99, 'image': 'https://images.puma.com/image/upload/f_auto,q_auto,b_rgb:fafafa,w_2000,h_2000/global/393271/02/sv01/fnd/PHL/fmt/png/Slipstream-Hi-Xtreme-Sneakers'},
    {'id': 13, 'name': 'Adidas TurboBoost UltraX', 'brand': 'Adidas', 'price': 199.99, 'image': 'https://www.shooos.com/media/catalog/product/cache/2/image/1350x778/9df78eab33525d08d6e5fb8d27136e95/a/d/adidas-ultraboost-20-fv83191.jpg'},
    {'id': 14, 'name': 'Adidas HyperCharge RS-X2', 'brand': 'Adidas', 'price': 219.99, 'image': 'https://assets.adidas.com/images/w_600,f_auto,q_auto/c22a22aa144941789482ad1f01884f78_9366/Response_Super_2.0_Shoes_Black_H04562_01_standard.jpg'},
    {'id': 15, 'name': 'Adidas QuantumFlex Boost', 'brand': 'Adidas', 'price': 249.99, 'image': 'https://barofashion.com/wp-content/uploads/2025/02/b9.jpg'},
]

# 2FA Setup View
@login_required
def setup_2fa(request):
    if request.user.socialaccount_set.exists():
        request.session['otp_verified'] = True
        return redirect('home')

    device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
    if not device:
        device = TOTPDevice.objects.create(user=request.user, confirmed=True)
        request.session['otp_verified'] = False

    otp_uri = device.config_url
    return render(request, 'store/setup_2fa.html', {'otp_uri': otp_uri})


# 2FA Verification View
@login_required
@require_POST
@ratelimit(key='ip', rate='5/m', block=True)
def verify_2fa(request):
    token = request.POST.get('otp_token')
    device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()

    if device:
        if device.verify_token(token):
            request.session['otp_verified'] = True
            UserActivityLog.objects.create(user=request.user, action='2fa_success')
            return redirect('home')
        else:
            UserActivityLog.objects.create(user=request.user, action='2fa_failure')
            messages.error(request, 'Invalid token. Please try again.')
            return render(request, 'store/setup_2fa.html', {'otp_uri': device.config_url})
    else:
        messages.error(request, 'No 2FA device found. Please set up 2FA first.')
        return redirect('setup_2fa')


# Register View
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form})


# Login View
@ratelimit(key='ip', rate='5/m', block=True)
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            UserActivityLog.objects.create(user=user, action='login', timestamp=now())
            return redirect('setup_2fa')
        else:
            username = request.POST.get('username')
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(username=username)
                UserActivityLog.objects.create(user=user, action='failed_login', timestamp=now())
            except User.DoesNotExist:
                pass
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})


# Home View
@login_required
def home_view(request):
    if not request.session.get('otp_verified', False):
        if not request.user.socialaccount_set.exists():
            return redirect('setup_2fa')
        else:
            request.session['otp_verified'] = True
    return render(request, 'store/home.html')


# Logout View
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('login')


def product_view(request):
    brand_filter = request.GET.get('brand')
    viewed_id = request.GET.get('viewed')  # Product ID of interest

    all_brands = sorted(set(p['brand'] for p in PRODUCTS))
    filtered_products = [p for p in PRODUCTS if p['brand'].lower() == brand_filter.lower()] if brand_filter else PRODUCTS

    recommended = []
    if viewed_id and viewed_id.isdigit():
        recommended = get_recommended_products(int(viewed_id))

    return render(request, 'store/product.html', {
        'products': filtered_products,
        'brands': all_brands,
        'selected_brand': brand_filter,
        'recommended': recommended
    })



# Add to Cart View
def add_to_cart(request):
    if request.method == 'POST':
        product_id = int(request.POST.get('product_id', 0))
        product = next((p for p in PRODUCTS if p['id'] == product_id), None)

        if product:
            cart = request.session.get('cart', [])
            if not isinstance(cart, list):
                cart = []
            cart.append(product)
            request.session['cart'] = cart
            return redirect('checkout')
    return redirect('product')


# Checkout View
def checkout_view(request):
    cart = request.session.get('cart', [])
    if not cart:
        return redirect('product')
    total_price = sum(item['price'] for item in cart)
    return render(request, 'store/checkout.html', {'cart': cart, 'total_price': total_price})


# Remove from Cart View
@require_POST
def remove_from_cart(request):
    index = int(request.POST.get('index', -1))
    cart = request.session.get('cart', [])
    if 0 <= index < len(cart):
        del cart[index]
        request.session['cart'] = cart
    return redirect('checkout')
