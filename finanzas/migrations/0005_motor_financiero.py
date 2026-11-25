from django.db import migrations, models


def reconciliar_saldo_inicial(apps, schema_editor):
    """Inicializa saldo_inicial = mesada para cuentas existentes sin alterar su saldo histórico."""
    Usuario = apps.get_model('finanzas', 'Usuario')
    for usuario in Usuario.objects.filter(saldo_inicial__isnull=True):
        usuario.saldo_inicial = usuario.mesada
        usuario.save(update_fields=['saldo_inicial'])


def revertir_saldo_inicial(apps, schema_editor):
    Usuario = apps.get_model('finanzas', 'Usuario')
    Usuario.objects.update(saldo_inicial=None)


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0004_metaahorro_categoria_metaahorro_nombre_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='saldo_inicial',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='fecha_proximo_ingreso',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='dia_pago_mensual',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(reconciliar_saldo_inicial, revertir_saldo_inicial),
    ]
