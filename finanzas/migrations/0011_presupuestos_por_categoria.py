import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0010_metas_fecha_objetivo_y_aportes'),
    ]

    operations = [
        migrations.CreateModel(
            name='PresupuestoCategoria',
            fields=[
                ('idPresupuestoCat', models.AutoField(db_column='idPresupuestoCat', primary_key=True, serialize=False)),
                ('limiteMensual', models.DecimalField(decimal_places=2, max_digits=10)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('idCategoria', models.ForeignKey(
                    db_column='idCategoria',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='presupuestos_categoria',
                    to='finanzas.categoria',
                )),
                ('idUsuario', models.ForeignKey(
                    db_column='idUsuario',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='presupuestos_categoria',
                    to='finanzas.usuario',
                )),
            ],
            options={
                'db_table': 'Presupuesto_Categoria',
                'constraints': [
                    models.UniqueConstraint(
                        fields=('idUsuario', 'idCategoria'),
                        name='uniq_pres_cat_usuario_categoria',
                    ),
                ],
            },
        ),
    ]
