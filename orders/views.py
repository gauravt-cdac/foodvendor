from urllib import response
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from marketplace.models import Cart
from marketplace.context_processors import get_cart_amounts
from .forms import OrderForm
from .models import Order, OrderedFood, Payment
import simplejson as json
from .utils import generate_order_number
from accounts.utils import send_notification
from django.contrib.auth.decorators import login_required
import razorpay
from foodOnline_main.settings import RZP_KEY_ID, RZP_KEY_SECRET


# Initialize Razorpay Client
client = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))


@login_required(login_url='login')
def place_order(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('marketplace')

    cart_totals = get_cart_amounts(request)
    subtotal = cart_totals['subtotal']
    total_tax = cart_totals['tax']
    grand_total = cart_totals['grand_total']
    tax_data = cart_totals['tax_dict']
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order()
            order.first_name = form.cleaned_data['first_name']
            order.last_name = form.cleaned_data['last_name']
            order.phone = form.cleaned_data['phone']
            order.email = form.cleaned_data['email']
            order.address = form.cleaned_data['address']
            order.country = form.cleaned_data['country']
            order.state = form.cleaned_data['state']
            order.city = form.cleaned_data['city']
            order.pin_code = form.cleaned_data['pin_code']
            order.user = request.user
            order.total = grand_total
            order.tax_data = json.dumps(tax_data)
            order.total_tax = total_tax
            order.payment_method = request.POST['payment_method']
            order.save()
            order.order_number = generate_order_number(order.id)
            order.save()

            # Create Razorpay Order
            DATA = {
                "amount": float(order.total) * 100,  # in paise
                "currency": "INR",
                "receipt": "receipt #" + order.order_number,
                "notes": {"order_id": order.order_number},
            }
            rzp_order = client.order.create(data=DATA)
            rzp_order_id = rzp_order['id']

            context = {
                'order': order,
                'cart_items': cart_items,
                'rzp_order_id': rzp_order_id,
                'RZP_KEY_ID': RZP_KEY_ID,
                'rzp_amount': float(order.total) * 100,
                'subtotal': subtotal,
                'tax_dict': tax_data,
                'grand_total': grand_total,
            }
            return render(request, 'orders/place_order.html', context)
        else:
            print(form.errors)

    return render(request, 'orders/place_order.html')


@login_required(login_url='login')
def payments(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'POST':
        order_number = request.POST.get('order_number')
        transaction_id = request.POST.get('transaction_id')
        payment_method = request.POST.get('payment_method')
        status = request.POST.get('status')

        order = Order.objects.get(user=request.user, order_number=order_number)
        payment = Payment(
            user=request.user,
            transaction_id=transaction_id,
            payment_method=payment_method,
            amount=order.total,
            status=status
        )
        payment.save()

        # Update order
        order.payment = payment
        order.is_ordered = True
        order.save()

        # Move items from cart to ordered_food
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            OrderedFood.objects.create(
                order=order,
                payment=payment,
                user=request.user,
                fooditem=item.fooditem,
                quantity=item.quantity,
                price=item.fooditem.price,
                amount=item.fooditem.price * item.quantity
            )

        # Send customer confirmation
        send_notification(
            'Thank you for ordering with us.',
            'orders/order_confirmation_email.html',
            {'user': request.user, 'order': order, 'to_email': order.email}
        )

        # Notify vendors
        vendor_emails = []
        for item in cart_items:
            vendor_email = item.fooditem.vendor.user.email
            if vendor_email not in vendor_emails:
                vendor_emails.append(vendor_email)

        send_notification(
            'You have received a new order.',
            'orders/new_order_received.html',
            {'order': order, 'to_email': vendor_emails}
        )

        # Optionally clear cart
        # cart_items.delete()

        response = {
            'order_number': order_number,
            'transaction_id': transaction_id,
        }
        return JsonResponse(response)

    return HttpResponse('Payments view')


def order_complete(request):
    order_number = request.GET.get('order_no')
    transaction_id = request.GET.get('trans_id')

    try:
        order = Order.objects.get(order_number=order_number, payment__transaction_id=transaction_id, is_ordered=True)
        ordered_food = OrderedFood.objects.filter(order=order)

        subtotal = sum(item.price * item.quantity for item in ordered_food)
        tax_data = json.loads(order.tax_data)

        context = {
            'order': order,
            'ordered_food': ordered_food,
            'subtotal': subtotal,
            'tax_data': tax_data,
        }
        return render(request, 'orders/order_complete.html', context)
    except:
        return redirect('home')
