from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import F, Q, Sum, Count, ExpressionWrapper, DecimalField
from django.shortcuts import get_object_or_404, redirect, render
from .models import (Category, Customer, Product, Sale, SaleItem, Vendor, PurchaseOrder,
                     PurchaseOrderItem, StockAdjustment, Return, ReturnItem)


def staff_required(view):
    return user_passes_test(lambda user: user.is_active and user.is_staff, login_url='/admin/login/')(view)


@login_required
def dashboard(request):
    today_sales = Sale.objects.filter(sold_at__date=date.today())
    context = {'today_total': today_sales.aggregate(total=Sum('total'))['total'] or 0,
               'today_count': today_sales.count(),
               'product_count': Product.objects.filter(active=True).count(),
               'customer_count': Customer.objects.count(),
               'low_stock': Product.objects.filter(active=True, stock__lte=F('reorder_level')).order_by('stock')[:6],
               'recent_sales': Sale.objects.select_related('cashier','customer').all()[:7],
               'open_orders': PurchaseOrder.objects.filter(status__in=['draft','sent','partial']).count()}
    return render(request, 'store/dashboard.html', context)


@login_required
def products(request):
    q = request.GET.get('q','').strip(); category = request.GET.get('category','')
    items = Product.objects.select_related('category').all()
    if q: items = items.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    if category: items = items.filter(category_id=category)
    return render(request, 'store/products.html', {'products':items, 'categories':Category.objects.all(), 'q':q, 'selected_category':category})


@staff_required
def product_create(request): return product_form(request)


@staff_required
def product_edit(request, pk): return product_form(request, get_object_or_404(Product, pk=pk))


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
    return render(request, 'store/pos.html', {'products':items, 'customers':Customer.objects.all()})


@login_required
@transaction.atomic
def checkout(request):
    if request.method != 'POST': return redirect('pos')
    ids = request.POST.getlist('product_id'); payment = request.POST.get('payment_method','cash')
    customer_id = request.POST.get('customer_id') or None
    sale_lines = []; total = Decimal('0.00')
    for product_id in ids:
        quantity = request.POST.get(f'quantity_{product_id}', '0')
        if not quantity or int(quantity) <= 0: continue
        product = Product.objects.select_for_update().get(pk=product_id)
        qty = int(quantity)
        if qty > product.stock: messages.error(request, f'Not enough stock for {product.name}.'); return redirect('pos')
        sale_lines.append((product, qty)); total += product.price * qty
    if not sale_lines: messages.error(request, 'Add at least one item to the sale.'); return redirect('pos')
    sale = Sale.objects.create(receipt_number=f'R-{uuid4().hex[:10].upper()}', cashier=request.user, customer_id=customer_id, payment_method=payment, total=total)
    for product, qty in sale_lines:
        SaleItem.objects.create(sale=sale, product=product, quantity=qty, unit_price=product.price)
        product.stock -= qty; product.save(update_fields=['stock','updated_at'])
        StockAdjustment.objects.create(product=product, delta=-qty, reason='sale', note=sale.receipt_number, actor=request.user)
    messages.success(request, f'Sale {sale.receipt_number} completed.')
    return redirect('sales')


@login_required
def sales(request):
    return render(request, 'store/sales.html', {'sales':Sale.objects.select_related('cashier','customer').prefetch_related('items__product').all()[:100]})


@staff_required
def customers(request):
    q = request.GET.get('q','').strip(); items = Customer.objects.all()
    if q: items = items.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))
    if request.method == 'POST':
        Customer.objects.create(name=request.POST.get('name','').strip(), email=request.POST.get('email','').strip(), phone=request.POST.get('phone','').strip(), notes=request.POST.get('notes','').strip())
        messages.success(request, 'Customer profile created.'); return redirect('customers')
    return render(request, 'store/customers.html', {'customers':items, 'q':q})


@staff_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'store/customer_detail.html', {'customer':customer, 'sales':customer.sales.select_related('cashier').prefetch_related('items__product')[:100]})


@staff_required
def vendors(request):
    if request.method == 'POST':
        Vendor.objects.create(name=request.POST.get('name','').strip(), email=request.POST.get('email','').strip(), phone=request.POST.get('phone','').strip(), notes=request.POST.get('notes','').strip())
        messages.success(request, 'Vendor added.'); return redirect('vendors')
    return render(request, 'store/vendors.html', {'vendors':Vendor.objects.all()})


@staff_required
def purchase_orders(request):
    if request.method == 'POST':
        vendor_id = request.POST.get('vendor'); product_ids = request.POST.getlist('product_id')
        if not vendor_id or not product_ids: messages.error(request, 'Select a vendor and at least one product.'); return redirect('purchase_orders')
        with transaction.atomic():
            po = PurchaseOrder.objects.create(order_number=f'PO-{uuid4().hex[:8].upper()}', vendor_id=vendor_id, created_by=request.user, status='sent', expected_at=request.POST.get('expected_at') or None, notes=request.POST.get('notes',''))
            for product_id in product_ids:
                qty = int(request.POST.get(f'quantity_{product_id}', '0') or 0)
                if qty > 0:
                    product = Product.objects.get(pk=product_id)
                    PurchaseOrderItem.objects.create(purchase_order=po, product=product, quantity_ordered=qty, unit_cost=product.cost)
        messages.success(request, f'Purchase order {po.order_number} created.'); return redirect('purchase_orders')
    return render(request, 'store/purchase_orders.html', {'orders':PurchaseOrder.objects.select_related('vendor','created_by').prefetch_related('items__product')[:100], 'vendors':Vendor.objects.filter(active=True), 'products':Product.objects.filter(active=True)})


@staff_required
def receive_purchase_order(request, pk):
    po = get_object_or_404(PurchaseOrder.objects.prefetch_related('items__product'), pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            for item in po.items.select_for_update().select_related('product'):
                received = int(request.POST.get(f'received_{item.id}', item.quantity_received) or 0)
                received = min(max(received, item.quantity_received), item.quantity_ordered)
                delta = received - item.quantity_received
                if delta:
                    item.quantity_received = received; item.save(update_fields=['quantity_received'])
                    product = Product.objects.select_for_update().get(pk=item.product_id)
                    product.stock += delta; product.cost = item.unit_cost; product.save(update_fields=['stock','cost','updated_at'])
                    StockAdjustment.objects.create(product=product, delta=delta, reason='purchase', note=po.order_number, actor=request.user)
            remaining = po.items.filter(quantity_received__lt=F('quantity_ordered')).exists()
            po.status = 'partial' if remaining else 'received'
            if po.status == 'received': po.received_at = __import__('django').utils.timezone.now()
            po.save(update_fields=['status','received_at'])
        messages.success(request, f'{po.order_number} receiving updated.'); return redirect('purchase_orders')
    return render(request, 'store/receive_order.html', {'order':po})


@staff_required
@transaction.atomic
def stock_adjustments(request):
    if request.method == 'POST':
        try:
            product = Product.objects.select_for_update().get(pk=request.POST['product'])
            delta = int(request.POST['delta'])
            if product.stock + delta < 0: raise ValueError
            product.stock += delta; product.save(update_fields=['stock','updated_at'])
            StockAdjustment.objects.create(product=product, delta=delta, reason=request.POST.get('reason','manual'), note=request.POST.get('note',''), actor=request.user)
            messages.success(request, 'Inventory adjustment recorded.'); return redirect('stock_adjustments')
        except (KeyError, ValueError): messages.error(request, 'Enter a valid adjustment that does not make stock negative.')
    return render(request, 'store/adjustments.html', {'products':Product.objects.filter(active=True), 'adjustments':StockAdjustment.objects.select_related('product','actor')[:100]})


@staff_required
def returns(request):
    if request.method == 'POST':
        sale = get_object_or_404(Sale, receipt_number=request.POST.get('receipt_number'))
        return_lines = []; total = Decimal('0.00')
        for item in sale.items.select_related('product'):
            qty = int(request.POST.get(f'quantity_{item.id}', '0') or 0)
            already = ReturnItem.objects.filter(sale_item=item).aggregate(qty=Sum('quantity'))['qty'] or 0
            if qty < 0 or qty > item.quantity - already: messages.error(request, f'Invalid return quantity for {item.product.name}.'); return redirect('returns')
            if qty: return_lines.append((item, qty)); total += item.unit_price * qty
        if not return_lines: messages.error(request, 'Enter a return quantity for at least one item.'); return redirect('returns')
        with transaction.atomic():
            record = Return.objects.create(return_number=f'RT-{uuid4().hex[:8].upper()}', sale=sale, processed_by=request.user, reason=request.POST.get('reason',''), total=total)
            for item, qty in return_lines:
                ReturnItem.objects.create(return_record=record, sale_item=item, quantity=qty, unit_price=item.unit_price)
                product = Product.objects.select_for_update().get(pk=item.product_id); product.stock += qty; product.save(update_fields=['stock','updated_at'])
                StockAdjustment.objects.create(product=product, delta=qty, reason='return', note=record.return_number, actor=request.user)
        messages.success(request, f'Return {record.return_number} recorded.'); return redirect('returns')
    receipt = request.GET.get('receipt','').strip(); sale = None
    if receipt: sale = Sale.objects.filter(receipt_number=receipt).prefetch_related('items__product').first()
    return render(request, 'store/returns.html', {'returns':Return.objects.select_related('sale','processed_by').all()[:100], 'sale':sale})


@staff_required
def reports(request):
    sales = Sale.objects.all(); total = sales.aggregate(value=Sum('total'))['value'] or 0
    cogs = SaleItem.objects.filter(sale__in=sales).aggregate(value=Sum(ExpressionWrapper(F('quantity') * F('product__cost'), output_field=DecimalField(max_digits=12, decimal_places=2))))['value'] or 0
    top_products = SaleItem.objects.values('product__name','product__sku').annotate(units=Sum('quantity'), revenue=Sum(ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField(max_digits=12, decimal_places=2)))).order_by('-revenue')[:8]
    return render(request, 'store/reports.html', {'total':total, 'cogs':cogs, 'margin':total-cogs, 'sale_count':sales.count(), 'payment_mix':sales.values('payment_method').annotate(total=Sum('total'), count=Count('id')).order_by('-total'), 'top_products':top_products, 'low_stock':Product.objects.filter(active=True, stock__lte=F('reorder_level')).order_by('stock')})
