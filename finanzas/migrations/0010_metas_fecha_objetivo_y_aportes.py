import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0009_categorias_personalizadas_y_umbral_hormiga'),
    ]

    operations = [
        migrations.AddField(
            model_name='metaahorro',
            name='fecha_objetivo',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metaahorro',
            name='creada_en',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='AporteMeta',
            fields=[
                ('idAporte', models.AutoField(db_column='idAporte', primary_key=True, serialize=False)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fecha', models.DateField(default=django.utils.timezone.localdate)),
                ('nota', models.CharField(blank=True, default='', max_length=120)),
                ('idMeta', models.ForeignKey(
                    db_column='idMeta',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='aportes',
                    to='finanzas.metaahorro',
                )),
                ('idUsuario', models.ForeignKey(
                    db_column='idUsuario',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='aportes_metas',
                    to='finanzas.usuario',
                )),
            ],
            options={
                'db_table': 'Aporte_Meta',
                'ordering': ['-fecha', '-idAporte'],
                'indexes': [
                    models.Index(fields=['idUsuario', 'fecha'], name='idx_aporte_usr_fecha'),
                ],
            },
        ),
    ]
