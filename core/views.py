from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from .models import Product, Order, OrderItem
from .forms import POSForm, ManagerLoginForm, ProductForm, AddStockForm
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from functools import wraps

# Decorator to check manager auth
def manager_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('is_manager'):
            return redirect('manager_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Helper to get cart from session
def get_cart(request):
    return request.session.get('pos_cart', {})

def save_cart(request, cart):
    request.session['pos_cart'] = cart
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

def manager_login(request):
    if request.method == 'POST':
        form = ManagerLoginForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['code'] == '123123':
                request.session['is_manager'] = True
                return redirect('manage_dashboard')
            else:
                messages.error(request, "Invalid Code")
    else:
        form = ManagerLoginForm()
    return render(request, 'core/manager_login.html', {'form': form})

@manager_required
def manage_dashboard(request):
    return render(request, 'core/manage_dashboard.html')

@manager_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product Added Successfully")
            return redirect('manage_dashboard')
    else:
        form = ProductForm()
    return render(request, 'core/add_product.html', {'form': form})

@manager_required
def remove_product(request):
    products = Product.objects.all()
    return render(request, 'core/remove_product.html', {'products': products})

@manager_required
def remove_product_action(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, f"Deleted {product.name}")
    return redirect('remove_product')

@manager_required
def add_stock(request):
    products = Product.objects.all()
    return render(request, 'core/add_stock.html', {'products': products})

@manager_required
def add_stock_action(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = AddStockForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            product.stock_quantity += quantity
            product.save()
            messages.success(request, f"Added {quantity} to {product.name}. New total: {product.stock_quantity}")
    return redirect('add_stock')

def report_view(request):
    # Daily Sales Logic
    today = timezone.now().date()
    daily_orders = Order.objects.filter(date_created__date=today)

    daily_sales = daily_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    # Products sold today
    sold_items = OrderItem.objects.filter(order__in=daily_orders) \
        .values('product__name') \
        .annotate(total_qty=Sum('quantity')) \
        .order_by('-total_qty')

    context = {
        'daily_sales': daily_sales,
        'sold_items': sold_items,
        'date': today
    }
    return render(request, 'core/reports.html', context)
