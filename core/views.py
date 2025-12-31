from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from .models import Product, Order, OrderItem
from .forms import POSForm
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

# Helper to get cart from session
def get_cart(request):
    return request.session.get('pos_cart', {})

def save_cart(request, cart):
    request.session['pos_cart'] = cart
    request.session.modified = True

# Online Cart Helpers
def get_online_cart(request):
    return request.session.get('online_cart', {})

def save_online_cart(request, cart):
    request.session['online_cart'] = cart
    request.session.modified = True

def pos_view(request):
    form = POSForm()
    cart = get_cart(request)
    cart_items = []
    total_amount = Decimal('0.00')

    for product_id, item in cart.items():
        subtotal = Decimal(str(item['price'])) * item['quantity']
        total_amount += subtotal
        cart_items.append({
            'product_id': product_id,
            'name': item['name'],
            'price': Decimal(str(item['price'])),
            'quantity': item['quantity'],
            'subtotal': subtotal
        })

    context = {
        'form': form,
        'cart_items': cart_items,
        'total_amount': total_amount
    }
    return render(request, 'core/pos.html', context)

def pos_add_item(request):
    if request.method == 'POST':
        form = POSForm(request.POST)
        if form.is_valid():
            barcode = form.cleaned_data['barcode']
            if not barcode:
                 messages.error(request, "Please enter a barcode.")
                 return redirect('pos_view')

            try:
                # Try to find by barcode first, then product code
                product = Product.objects.filter(barcode=barcode).first()
                if not product:
                    product = Product.objects.filter(product_code=barcode).first()

                if product:
                    if product.stock_quantity > 0:
                        cart = get_cart(request)
                        product_id = str(product.id)

                        if product_id in cart:
                            cart[product_id]['quantity'] += 1
                        else:
                            cart[product_id] = {
                                'name': product.name,
                                'price': str(product.price),
                                'quantity': 1
                            }

                        save_cart(request, cart)
                        messages.success(request, f"Added {product.name}")
                    else:
                        messages.error(request, f"Out of stock: {product.name}")
                else:
                    messages.error(request, "Product not found.")
            except Exception as e:
                messages.error(request, f"Error: {e}")

    return redirect('pos_view')

def pos_remove_item(request, product_id):
    cart = get_cart(request)
    if product_id in cart:
        del cart[product_id]
        save_cart(request, cart)
        messages.success(request, "Item removed.")
    return redirect('pos_view')

def pos_clear(request):
    request.session['pos_cart'] = {}
    messages.info(request, "Transaction cleared.")
    return redirect('pos_view')

@transaction.atomic
def pos_checkout(request):
    if request.method == 'POST':
        cart = get_cart(request)
        if not cart:
            messages.error(request, "Cart is empty.")
            return redirect('pos_view')

        total_amount = Decimal('0.00')
        order_items = []

        # Calculate total and prepare items
        for product_id, item in cart.items():
            product = get_object_or_404(Product, id=product_id)
            quantity = item['quantity']

            # Check stock again
            if product.stock_quantity < quantity:
                messages.error(request, f"Not enough stock for {product.name}. Available: {product.stock_quantity}")
                return redirect('pos_view')

            price = Decimal(str(item['price']))
            total_amount += price * quantity
            order_items.append((product, quantity, price))

        # Create Order
        order = Order.objects.create(
            order_type='POS',
            total_amount=total_amount
        )

        # Create OrderItems and update stock
        for product, quantity, price in order_items:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_sale=price
            )
            product.stock_quantity -= quantity
            product.save()

        # Clear cart
        request.session['pos_cart'] = {}
        messages.success(request, f"Sale completed! Total: ${total_amount}")

    return redirect('pos_view')

def product_list(request):
    products = Product.objects.all()
    return render(request, 'core/product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'core/product_detail.html', {'product': product})

def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        cart = get_online_cart(request)
        product_id = str(product.id)

        if product.stock_quantity > 0:
            if product_id in cart:
                cart[product_id]['quantity'] += 1
            else:
                cart[product_id] = {
                    'name': product.name,
                    'price': str(product.price),
                    'quantity': 1
                }
            save_online_cart(request, cart)
            messages.success(request, f"Added {product.name} to cart.")
        else:
            messages.error(request, "Out of stock.")

    return redirect('product_list') # Or detail page

def cart_view(request):
    cart = get_online_cart(request)
    cart_items = []
    total_amount = Decimal('0.00')

    for product_id, item in cart.items():
        subtotal = Decimal(str(item['price'])) * item['quantity']
        total_amount += subtotal
        cart_items.append({
            'product_id': product_id,
            'name': item['name'],
            'price': Decimal(str(item['price'])),
            'quantity': item['quantity'],
            'subtotal': subtotal
        })

    return render(request, 'core/cart.html', {
        'cart_items': cart_items,
        'total_amount': total_amount
    })

def remove_from_cart(request, product_id):
    cart = get_online_cart(request)
    if product_id in cart:
        del cart[product_id]
        save_online_cart(request, cart)
        messages.success(request, "Item removed from cart.")
    return redirect('cart_view')

@transaction.atomic
def checkout(request):
    if request.method == 'POST':
        cart = get_online_cart(request)
        if not cart:
            messages.error(request, "Cart is empty.")
            return redirect('cart_view')

        total_amount = Decimal('0.00')
        order_items = []

        for product_id, item in cart.items():
            product = get_object_or_404(Product, id=product_id)
            quantity = item['quantity']

            if product.stock_quantity < quantity:
                messages.error(request, f"Not enough stock for {product.name}. Available: {product.stock_quantity}")
                return redirect('cart_view')

            price = Decimal(str(item['price']))
            total_amount += price * quantity
            order_items.append((product, quantity, price))

        # Create Order
        order = Order.objects.create(
            order_type='ONLINE',
            total_amount=total_amount
        )

        for product, quantity, price in order_items:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_sale=price
            )
            product.stock_quantity -= quantity
            product.save()

        request.session['online_cart'] = {}
        messages.success(request, f"Order placed successfully! Order ID: {order.id}")
        return redirect('product_list')

    return redirect('cart_view')

def report_view(request):
    date_filter = request.GET.get('date_filter', 'week')
    now = timezone.now()

    if date_filter == 'month':
        start_date = now - timedelta(days=30)
    elif date_filter == 'year':
        start_date = now - timedelta(days=365)
    else: # week
        start_date = now - timedelta(days=7)

    orders = Order.objects.filter(date_created__gte=start_date).order_by('-date_created')

    total_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    online_sales = orders.filter(order_type='ONLINE').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    pos_sales = orders.filter(order_type='POS').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    context = {
        'orders': orders,
        'total_sales': total_sales,
        'online_sales': online_sales,
        'pos_sales': pos_sales,
        'date_filter': date_filter
    }
    return render(request, 'core/reports.html', context)
