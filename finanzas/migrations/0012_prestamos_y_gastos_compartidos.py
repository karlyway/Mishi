from decimal import Decimal
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0011_presupuestos_por_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='prestamo',
            name='fecha_limite',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='prestamo',
            name='fecha_pago',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='prestamo',
            name='transaccion_pago',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='prestamo_liquidado',
                to='finanzas.transaccion',
            ),
        ),
        migrations.AddField(
            model_name='gastocompartido',
            name='idUsuario',
            field=models.ForeignKey(
                blank=True,
                db_column='idUsuario',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='gastos_compartidos',
                to='finanzas.usuario',
            ),
        ),
        migrations.AddField(
            model_name='gastocompartido',
            name='mi_parte',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='gastocompartido',
            name='yo_pague_total',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='gastocompartido',
            name='creado_en',
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
        migrations.AlterField(
            model_name='gastocompartido',
            name='estado',
            field=models.CharField(default='Pendiente', max_length=50),
        ),
        migrations.AlterModelOptions(
            name='gastocompartido',
            options={'ordering': ['-creado_en', '-idGastoComp']},
        ),
        migrations.AddField(
            model_name='participante',
            name='pagado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='participante',
            name='fecha_pago',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='participante',
            name='transaccion_reembolso',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reembolso_participante',
                to='finanzas.transaccion',
            ),
        ),
        migrations.AlterField(
            model_name='participante',
            name='idGastoComp',
            field=models.ForeignKey(
                db_column='idGastoComp',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='participantes',
                to='finanzas.gastocompartido',
            ),
        ),
    ]
