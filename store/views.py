from django.shortcuts import render
from django.http import JsonResponse
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import google.generativeai as genai
import logging

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

# Setup logging
logger = logging.getLogger(__name__)

def store(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    if request.user.is_authenticated:
        try:
            customer = request.user.customer
        except ObjectDoesNotExist:
            customer = Customer.objects.create(user=request.user)

    products = Product.objects.all()
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)

def cart(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    if request.user.is_authenticated:
        try:
            customer = request.user.customer
        except ObjectDoesNotExist:
            customer = Customer.objects.create(user=request.user)

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)

def checkout(request):
    data = cartData(request)
    
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    if request.user.is_authenticated:
        try:
            customer = request.user.customer
        except ObjectDoesNotExist:
            customer = Customer.objects.create(user=request.user)

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    if request.user.is_authenticated:
        try:
            customer = request.user.customer
        except ObjectDoesNotExist:
            customer = Customer.objects.create(user=request.user)

        product = Product.objects.get(id=productId)
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

        if action == 'add':
            orderItem.quantity = (orderItem.quantity + 1)
        elif action == 'remove':
            orderItem.quantity = (orderItem.quantity - 1)

        orderItem.save()

        if orderItem.quantity <= 0:
            orderItem.delete()

        return JsonResponse('Item was added', safe=False)

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        try:
            customer = request.user.customer
        except ObjectDoesNotExist:
            customer = Customer.objects.create(user=request.user)

        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment submitted..', safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def chatbot(request):
    """
    AI Chatbot endpoint using Google Gemini API.
    Handles user messages and returns AI-powered responses.
    """
    try:
        # Log incoming raw body to help debug frontend issues
        try:
            logger.info(f"Chatbot request body: {request.body}")
        except Exception:
            pass

        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'response': 'தயவுசெய்து ஒரு செய்தி உள்ளிடுங்கள்.'}, status=400)

        # Get AI response using Gemini
        ai_response = get_gemini_response(user_message)

        return JsonResponse({'response': ai_response})

    except json.JSONDecodeError:
        return JsonResponse({'response': 'தவறான கோப்பு வடிவம்.'}, status=400)
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        return JsonResponse({
            'response': 'மன்னிக்கவும், ஒரு பிழை ஏற்பட்டது. தயவுசெய்து பின்னர் மீண்டும் முயற்சிக்கவும் அல்லது ஆதரவிற்கு அணுகுங்கள்.'
        }, status=500)


def get_gemini_response(user_message):
    """
    Generate AI response using Google Gemini API.
    Provides context about the store and products.
    """
    try:
        # Quick check: make sure GEMINI_API_KEY is set and not the placeholder
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key or 'your-gemini' in str(api_key).lower():
            # Return a helpful fallback response listing products so the chatbot remains useful
            products = Product.objects.all()
            if products.exists():
                product_list = ', '.join([f"{p.name} (ரூ.{p.price})" for p in products[:10]])
                return ("AI உதவியாளர் அமைக்கப்படவில்லை (API விசை இல்லை அல்லது இடமாற்றி உள்ளது). "
                        "தயவுசெய்து GEMINI_API_KEY ஐ உங்கள் சூழலில் அல்லது .env கோப்பில் அமைக்கவும். "
                        f"இந்நிலையில், கிடைக்கக்கூடிய பொருட்கள்: {product_list}.")
            return "AI உதவியாளர் அமைக்கப்படவில்லை. தயவுசெய்து GEMINI_API_KEY ஐ உங்கள் சூழலில் அல்லது .env கோப்பில் அமைக்கவும்."

        # Get product context
        products = Product.objects.all()
        product_context = ""
        if products.exists():
            product_context = "\n\nStore Products:\n"
            for product in products[:15]:
                product_context += f"- {product.name}: ரூ.{product.price}\n"

        # Create the system prompt with store context (instruct model to respond in Tamil)
        system_prompt = f"""You are a helpful AI customer service assistant for UzhavanHub, an online marketplace for farmers and fresh produce.

Store Name: UzhavanHub
Your role: Help customers find products, manage their shopping experience, answer questions about checkout, shipping, and provide excellent customer service.

{product_context}

IMPORTANT: You MUST respond only in Tamil language. All responses must be in Tamil.

Guidelines:
- Be friendly, helpful, and professional
- Focus on the store's products and services
- If asked about topics unrelated to the store, politely redirect to store-related queries
- Provide concise, clear responses
- Use emojis occasionally to make responses friendly
- Address customer needs efficiently"""

        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-pro')

        # Generate response using Gemini
        response = model.generate_content(
            f"{system_prompt}\n\nCustomer: {user_message}",
            safety_settings=[
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
        )

        if getattr(response, 'text', None):
            return response.text
        else:
            return "நான் ஒரு பதிலை உருவாக்குவதில் சிக்கல் எதிர்கொண்டேன். தயவுசெய்து மீண்டும் முயற்சிக்கவும்."

    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        msg = str(e)
        # Friendly message for common API key error
        if ('api key not valid' in msg.lower() or 'api_key_invalid' in msg.lower() or
                ('invalid' in msg.lower() and 'api' in msg.lower())):
            # Provide fallback product info to the user
            products = Product.objects.all()
            if products.exists():
                product_list = ', '.join([f"{p.name} (ரூ.{p.price})" for p in products[:10]])
                return ("AI உதவியாளர் Gemini API உடன் அங்கீகரிக்க முடியவில்லை (தவறான API விசை). "
                        "தயவுசெய்து GEMINI_API_KEY ஐ உங்கள் .env அல்லது சூழலில் புதுப்பிக்கவும். "
                        f"இந்நிலையில், கிடைக்கக்கூடிய பொருட்கள்: {product_list}.")
            return "AI உதவியாளர் Gemini API உடன் அங்கீகரிக்க முடியவில்லை (தவறான API விசை). தயவுசெய்து GEMINI_API_KEYஐ உங்கள் .env அல்லது சூழலில் புதுப்பிக்கவும்."

        # Generic fallback
        return f"ஒரு பிழை ஏற்பட்டது: {msg}"


def profile(request):
    """
    User profile page showing account info and order history.
    """
    if not request.user.is_authenticated:
        return render(request, 'store/login_required.html')
    
    try:
        customer = request.user.customer
    except ObjectDoesNotExist:
        customer = Customer.objects.create(user=request.user)
    
    # Get user's orders
    orders = Order.objects.filter(customer=customer).prefetch_related('orderitem_set')
    
    # Handle profile update form
    if request.method == 'POST':
        customer.name = request.POST.get('name', customer.name)
        customer.email = request.POST.get('email', customer.email)
        customer.save()
        
        # Update user's email if provided
        if request.POST.get('email'):
            request.user.email = request.POST.get('email')
            request.user.save()
        
        context = {
            'customer': customer,
            'orders': orders,
            'user': request.user,
            'message': 'Profile updated successfully!'
        }
        return render(request, 'store/profile.html', context)
    
    data = cartData(request)
    context = {
        'customer': customer,
        'orders': orders,
        'user': request.user,
        'cartItems': data['cartItems']
    }
    return render(request, 'store/profile.html', context)


def learning(request):
    """
    Learning/Blog page with farming tips and educational articles.
    """
    articles = Learning.objects.all()
    
    # Filter by category if provided
    category = request.GET.get('category', None)
    if category:
        articles = articles.filter(category=category)
    
    # Get unique categories
    categories = Learning.objects.values_list('category', flat=True).distinct()
    
    data = cartData(request)
    context = {
        'articles': articles,
        'categories': categories,
        'selected_category': category,
        'cartItems': data['cartItems']
    }
    return render(request, 'store/learning.html', context)

