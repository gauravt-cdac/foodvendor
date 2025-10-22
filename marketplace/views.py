from django.shortcuts import render
from vendor.models import Vendor
from django.shortcuts import get_object_or_404
from menu.models import Category
from menu.models import FoodItem
from django.db.models import Prefetch
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# Create your views here.
def marketplace(request):
    vendors = Vendor.objects.filter(is_approved = True, user__is_active = True)
    vendor_count = vendors.count()
    context = {
        "vendors" : vendors,
        "vendor_count" : vendor_count,
    }
    return render(request,'marketplace/listings.html',context)

def vendor_detail(request,vendor_slug):
    vendor = get_object_or_404(Vendor,vendor_slug= vendor_slug)
    categories = Category.objects.filter(vendor=vendor).prefetch_related(
        Prefetch(
            'fooditems',
            queryset= FoodItem.objects.filter(is_available= True)
        )
    )

    if request.user.is_authenticated:
        cart_items =Cart.objects.filter(user=request.user)
    else:
        cart_items = None
    
    context = {
        'vendor' : vendor ,
        'categories' : categories,
        'cart_items' : cart_items,
    }
    return render(request, 'marketplace/vendor_detail.html', context)

from django.http import JsonResponse
from .models import FoodItem, Cart

def add_to_cart(request, food_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest': 
            try:
                # Check if the food item exists
                fooditem = FoodItem.objects.get(id=food_id)

                # Check if the user already has this food item in the cart
                try:
                    chkcart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    chkcart.quantity += 1
                    chkcart.save()
                    return JsonResponse({'status': 'success', 'message': 'Increased the cart quantity'})
                except Cart.DoesNotExist:
                    Cart.objects.create(user=request.user, fooditem=fooditem, quantity=1)
                    return JsonResponse({'status': 'success', 'message': 'Added food to the cart'})

            except FoodItem.DoesNotExist:
                return JsonResponse({'status': 'failed', 'message': 'This food item does not exist'})
        else:
            return JsonResponse({'status': 'failed', 'message': 'Invalid request'})
    else:
        return JsonResponse({'status': 'Login required', 'message': 'Please log in to continue'})

def decrease_cart(request, food_id):
    if request.user.is_authenticated:
        if request.is_ajax():
            # Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    if chkCart.quantity > 1:
                        # decrease the cart quantity
                        chkCart.quantity -= 1
                        chkCart.save()
                    else:
                        chkCart.delete()
                        chkCart.quantity = 0
                    return JsonResponse({'status': 'Success', 'cart_counter': get_cart_counter(request), 'qty': chkCart.quantity, 'cart_amount': get_cart_amounts(request)})
                except:
                    return JsonResponse({'status': 'Failed', 'message': 'You do not have this item in your cart!'})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This food does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
        
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})

@login_required(login_url = 'login')
def cart(request):
    cart_items = Cart.objects.filter(user = request.user).order_by('created_at')
    context = {
        'cart_items' : 'cart_items'
    }
    return render(request,'marketplace/cart.html',context)

def delete_cart(request,cart_id):
    if request.user_is_authenticated:
        if request.is_ajax():
            try:
                #check if hte cartt item exist
                cart_item = Cart.objects.get(user = request.user,id = cart_id)
                if cart_item:
                    cart_item.delete()
                    return JsonResponse({'status':'Success',"message":"Cartitems has been deleted",'cart_counter': get_cart_counter(request)})
                else:
                    return JsonResponse({'status':'failed','message': 'Invalid reqeuest'})
            except:
                return JsonResponse({"status":"failed","message":"Cart item does not exist"})