from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0006_avatares_y_personalizacion'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notificacion',
            fields=[
                ('idNotificacion', models.AutoField(db_column='idNotificacion', primary_key=True, serialize=False)),
                ('clave', models.CharField(blank=True, default='', max_length=80)),
                ('tipo', models.CharField(default='info', max_length=30)),
                ('nivel', models.CharField(default='info', max_length=16)),
                ('titulo', models.CharField(max_length=120)),
                ('mensaje', models.CharField(max_length=280)),
                ('url_destino', models.CharField(default='/app/insights/?tab=control', max_length=120)),
                ('leida', models.BooleanField(default=False)),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('idUsuario', models.ForeignKey(db_column='idUsuario', on_delete=django.db.models.deletion.CASCADE, related_name='notificaciones', to='finanzas.usuario')),
            ],
            options={
                'db_table': 'Notificacion',
                'ordering': ['-creada_en', '-idNotificacion'],
            },
        ),
        migrations.AddIndex(
            model_name='notificacion',
            index=models.Index(fields=['idUsuario', 'leida'], name='idx_notif_usr_leida'),
        ),
        migrations.AddIndex(
            model_name='notificacion',
            index=models.Index(fields=['idUsuario', 'clave'], name='idx_notif_usr_clave'),
        ),
    ]
