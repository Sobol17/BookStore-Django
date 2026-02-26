from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_alter_banner_options_alter_bookpurchasephoto_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='order',
            field=models.PositiveIntegerField(default=0, verbose_name='Порядок'),
        ),
        migrations.AlterModelOptions(
            name='category',
            options={
                'ordering': ('order', 'name'),
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
            },
        ),
    ]
