# Generated by Django 4.2.6 on 2023-11-03 11:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("frontend", "0009_registro_ip_respuesta1_registro_ip_respuesta10_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="registro_ip",
            name="recomendaciones",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="registro_ip",
            name="resultado",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="registro_ip",
            name="resumen",
            field=models.TextField(blank=True, null=True),
        ),
    ]
