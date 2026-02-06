from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_product_attributes_product_barcode_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ErpProductSyncState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_synced_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
