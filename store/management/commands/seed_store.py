from django.core.management.base import BaseCommand
from store.models import Category, Product
class Command(BaseCommand):
    help = 'Seed the store with demo categories and products'
    def handle(self, *args, **kwargs):
        samples = {'Beverages':[('BEV-001','Sparkling Water',1.5,32),('BEV-002','Cold Brew Coffee',3.75,18)], 'Snacks':[('SNK-001','Sea Salt Chips',2.25,14),('SNK-002','Granola Bar',1.95,26)], 'Household':[('HOM-001','All-Purpose Cleaner',5.5,9)]}
        for name, products in samples.items():
            category, _ = Category.objects.get_or_create(name=name)
            for sku, pname, price, stock in products: Product.objects.get_or_create(sku=sku, defaults={'name':pname,'category':category,'price':price,'cost':price*.55,'stock':stock,'reorder_level':5})
        self.stdout.write(self.style.SUCCESS('Demo store data is ready.'))
