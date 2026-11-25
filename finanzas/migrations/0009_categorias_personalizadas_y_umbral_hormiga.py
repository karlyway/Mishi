from decimal import Decimal
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0008_seguridad_privacidad_y_notif_descartada'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='umbral_hormiga',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('15000.00'),
                max_digits=10,
            ),
        ),
        migrations.AddField(
            model_name='categoria',
            name='idUsuario',
            field=models.ForeignKey(
                blank=True,
                db_column='idUsuario',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='categorias_personalizadas',
                to='finanzas.usuario',
            ),
        ),
        migrations.AddField(
            model_name='categoria',
            name='es_personalizada',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='categoria',
            name='tipo_aplicable',
            field=models.CharField(default='ambos', max_length=20),
        ),
        migrations.AddField(
            model_name='categoria',
            name='tono',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddIndex(
            model_name='categoria',
            index=models.Index(
                fields=['idUsuario', 'nombre'],
                name='idx_cat_usuario_nombre',
            ),
        ),
    ]
