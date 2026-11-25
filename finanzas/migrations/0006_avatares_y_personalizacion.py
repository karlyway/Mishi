from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0005_motor_financiero'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='avatar',
            field=models.CharField(default='mishi-naranja-feliz', max_length=40),
        ),
        migrations.AddField(
            model_name='usuario',
            name='ocultar_saldo',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usuario',
            name='alertas_activas',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='tema_visual',
            field=models.CharField(default='warm', max_length=16),
        ),
    ]
