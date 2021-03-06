# Generated by Django 3.1.12 on 2021-12-11 06:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('novels', '0055_auto_20211211_0625'),
    ]

    operations = [
        migrations.AlterField(
            model_name='novel',
            name='new_image',
            field=models.ImageField(default='', upload_to='full/'),
        ),
        migrations.AlterField(
            model_name='novel',
            name='new_image_thumb',
            field=models.ImageField(default='', upload_to='thumbnail/'),
        ),
        migrations.AlterField(
            model_name='novel',
            name='original_image',
            field=models.ImageField(default='', upload_to='original/'),
        ),
    ]
