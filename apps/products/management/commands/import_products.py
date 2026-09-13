from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.products.models import Product
from recommendation.utils.loader import load_json_file


class Command(BaseCommand):
    help = "Import or update products from the legacy hierarchical JSON catalog."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            default="recommendation/data/sofa.json",
            help="Path to the legacy JSON catalog.",
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"Catalog does not exist: {path}")

        products = load_json_file(path)
        created = 0
        updated = 0
        for item in products:
            _product, was_created = Product.objects.update_or_create(
                legacy_id=item.id,
                defaults={
                    "audience": item.person.value,
                    "product_type": item.productType.value,
                    "number_of_person": item.number_of_person,
                    "budget": item.budget,
                    "style": item.style.value,
                    "color": item.color.value,
                    "fabric_material": item.fabric_material.value if item.fabric_material else "",
                    "body_material": item.body_material.value if item.body_material else "",
                    "is_active": True,
                },
            )
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(products)} products: {created} created, {updated} updated."
            )
        )
