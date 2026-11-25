from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0007_notificaciones'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='acepto_politica_datos',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usuario',
            name='fecha_aceptacion_datos',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='version_politica_datos',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='notificacion',
            name='descartada',
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name='notificacion',
            index=models.Index(fields=['idUsuario', 'descartada', 'leida'], name='idx_notif_usr_desc_leida'),
        ),
    ]
