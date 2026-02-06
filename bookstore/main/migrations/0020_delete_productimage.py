from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0019_erp_product_sync_state'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ProductImage',
        ),
    ]
