from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_category_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='genre',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='genres/'),
        ),
    ]
