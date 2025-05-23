# Generated by Django 5.2 on 2025-04-24 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_merge_20250422_1904'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeeprofile',
            name='department',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='employee_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='wallet_balance',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='employerprofile',
            name='wallet_balance',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
