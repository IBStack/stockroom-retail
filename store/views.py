from decimal import Decimal, InvalidOperation
from uuid import uuid4
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from .models import Category, Product, Sale, SaleItem

@login_required
def dashboard(request):
    today_sales = Sale.objects.filter(sold_at__date=__import__('datetime').date.today())
    context = {'today_total': today_sales.aggregate(total=Sum('total'))['total'] or 0, 'today_count': today_sales.count(), 'product_count': Product.objects.filter(active=True).count(), 'low_stock': Product.objects.filter(active=True, stock__lte=F('reorder_level')).order_by('stock')[:6], 'recent_sales': Sale.objects.select_related('cashier').all()[:7]}
    return render(request, 'store/dashboard.html', context)

@login_required
def products(request):
    q = request.GET.get('q','').strip(); category = request.GET.get('category','')
    items = Product.objects.select_related('category').all()
    if q: items = items.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    if category: items = items.filter(category_id=category)
    return render(request, 'store/products.html', {'products':items, 'categories':Category.objects.all(), 'q':q, 'selected_category':category})

@login_required
def product_create(request):
    return product_form(request)

@login_required
def product_edit(request, pk):
    return product_form(request, get_object_or_404(Product, pk=pk))

def product_form(request, instance=None):
    if request.method == 'POST':
        data = request.POST
        try:
            values = {'sku':data['sku'].strip(), 'name':data['name'].strip(), 'category_id':data['category'], 'price':Decimal(data['price']), 'cost':Decimal(data.get('cost') or 0), 'stock':int(data.get('stock') or 0), 'reorder_level':int(data.get('reorder_level') or 5), 'active':data.get('active') == 'on'}
            if instance: Product.objects.filter(pk=instance.pk).update(**values)
            else: Product.objects.create(**values)
            messages.success(request, 'Product saved successfully.'); return redirect('products')
        except (KeyError, InvalidOperation, ValueError): messages.error(request, 'Please check all product fields.')
    return render(request, 'store/product_form.html', {'product':instance, 'categories':Category.objects.all()})

@login_required
def pos(request):
    items = Product.objects.filter(active=True, stock__gt=0).select_related('category')
    return render(request, 'store/pos.html', {'products':items})

@login_required
@transaction.atomic
def checkout(request):
    if request.method != 'POST': return redirect('pos')
    ids = request.POST.getlist('product_id'); payment = request.POST.get('payment_method','cash')
    sale_lines = []; total = Decimal('0.00')
    for product_id in ids:
        quantity = request.POST.get(f'quantity_{product_id}', '0')
        if not quantity or int(quantity) <= 0: continue
        product = Product.objects.select_for_update().get(pk=product_id)
        qty = int(quantity)
        if qty > product.stock: messages.error(request, f'Not enough stock for {product.name}.'); return redirect('pos')
        sale_lines.append((product, qty)); total += product.price * qty
    if not sale_lines: messages.error(request, 'Add at least one item to the sale.'); return redirect('pos')
    sale = Sale.objects.create(receipt_number=f'R-{uuid4().hex[:10].upper()}', cashier=request.user, payment_method=payment, total=total)
    for product, qty in sale_lines:
        SaleItem.objects.create(sale=sale, product=product, quantity=qty, unit_price=product.price)
        product.stock -= qty; product.save(update_fields=['stock','updated_at'])
    messages.success(request, f'Sale {sale.receipt_number} completed.')
    return redirect('sales')

@login_required
def sales(request): return render(request, 'store/sales.html', {'sales':Sale.objects.select_related('cashier').prefetch_related('items__product').all()[:100]})
