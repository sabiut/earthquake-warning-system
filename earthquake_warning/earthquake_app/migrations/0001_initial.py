# Generated by Django 4.2.17 on 2025-01-04 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Earthquake',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usgs_id', models.CharField(max_length=100, unique=True)),
                ('magnitude', models.FloatField()),
                ('place', models.CharField(max_length=255)),
                ('time', models.DateTimeField()),
                ('longitude', models.FloatField()),
                ('latitude', models.FloatField()),
                ('depth', models.FloatField()),
                ('is_alert_sent', models.BooleanField(default=False)),
            ],
        ),
    ]
