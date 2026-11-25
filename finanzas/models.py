from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

class Usuario(models.Model):
    idUsuario = models.AutoField(primary_key=True, db_column='idUsuario')

    cuenta = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='perfil_mishi'
    )

    nombre = models.CharField(max_length=100)

    universidad = models.CharField(
        max_length=150,
        blank=True,
        default=''
    )

    frecuencia = models.CharField(
        max_length=20,
        default='quincenal'
    )

    mesada = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    saldo_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    fecha_proximo_ingreso = models.DateField(
        null=True,
        blank=True
    )

    dia_pago_mensual = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    avatar = models.CharField(
        max_length=40,
        default='mishi-naranja-feliz'
    )

    ocultar_saldo = models.BooleanField(default=False)

    alertas_activas = models.BooleanField(default=True)

    tema_visual = models.CharField(
        max_length=16,
        default='warm'
    )

    acepto_politica_datos = models.BooleanField(default=False)

    fecha_aceptacion_datos = models.DateTimeField(
        null=True,
        blank=True
    )

    version_politica_datos = models.CharField(
        max_length=20,
        blank=True,
        default=''
    )

    umbral_hormiga = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('15000.00')
    )

    def save(self, *args, **kwargs):
        if self._state.adding and self.saldo_inicial is None:
            self.saldo_inicial = self.mesada
        if self.fecha_proximo_ingreso and self.frecuencia == 'mensual' and not self.dia_pago_mensual:
            self.dia_pago_mensual = self.fecha_proximo_ingreso.day
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'Usuario'

class Presupuesto(models.Model):
    idPresupuesto = models.AutoField(primary_key=True, db_column='idPresupuesto')
    idUsuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        db_column='idUsuario',
        unique=True,
    )
    limiteDiario = models.DecimalField(max_digits=10, decimal_places=2)
    limiteMensual = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'Presupuesto'


class MetaAhorro(models.Model):
    idMeta = models.AutoField(primary_key=True, db_column='idMeta')
    idUsuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='idUsuario')
    nombre = models.CharField(max_length=100, default='Mi meta')
    categoria = models.CharField(max_length=100, default='General')
    objetivo = models.DecimalField(max_digits=10, decimal_places=2)
    acumulado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fecha_objetivo = models.DateField(null=True, blank=True)
    creada_en = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'Meta_Ahorro'


class AporteMeta(models.Model):
    idAporte = models.AutoField(primary_key=True, db_column='idAporte')
    idMeta = models.ForeignKey(
        MetaAhorro,
        on_delete=models.CASCADE,
        db_column='idMeta',
        related_name='aportes',
    )
    idUsuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='idUsuario',
        related_name='aportes_metas',
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(default=timezone.localdate)
    nota = models.CharField(max_length=120, blank=True, default='')

    class Meta:
        db_table = 'Aporte_Meta'
        ordering = ['-fecha', '-idAporte']
        indexes = [
            models.Index(fields=['idUsuario', 'fecha'], name='idx_aporte_usr_fecha'),
        ]


class Categoria(models.Model):
    idCategoria = models.AutoField(primary_key=True, db_column='idCategoria')
    nombre = models.CharField(max_length=100)
    idUsuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='idUsuario',
        null=True,
        blank=True,
        related_name='categorias_personalizadas',
    )
    es_personalizada = models.BooleanField(default=False)
    tipo_aplicable = models.CharField(max_length=20, default='ambos')
    tono = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'Categoria'
        indexes = [
            models.Index(fields=['idUsuario', 'nombre'], name='idx_cat_usuario_nombre'),
        ]


class PresupuestoCategoria(models.Model):
    idPresupuestoCat = models.AutoField(primary_key=True, db_column='idPresupuestoCat')
    idUsuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='idUsuario',
        related_name='presupuestos_categoria',
    )
    idCategoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        db_column='idCategoria',
        related_name='presupuestos_categoria',
    )
    limiteMensual = models.DecimalField(max_digits=10, decimal_places=2)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Presupuesto_Categoria'
        constraints = [
            models.UniqueConstraint(
                fields=['idUsuario', 'idCategoria'],
                name='uniq_pres_cat_usuario_categoria',
            ),
        ]


class Transaccion(models.Model):
    idTransaccion = models.AutoField(primary_key=True, db_column='idTransaccion')

    descripcion = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )
    idUsuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='idUsuario',
    )
    idCategoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        db_column='idCategoria',
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
    tipo = models.CharField(max_length=50)

    class Meta:
        db_table = 'Transaccion'


class Prestamo(models.Model):
    idPrestamo = models.AutoField(primary_key=True, db_column='idPrestamo')
    idUsuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='idUsuario')
    deudor = models.CharField(max_length=100)
    concepto = models.CharField(max_length=255, default='')
    fecha = models.DateField(auto_now_add=True)
    fecha_limite = models.DateField(null=True, blank=True)
    fecha_pago = models.DateField(null=True, blank=True)
    tipo = models.CharField(max_length=50, default='Por cobrar')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=50, default='Pendiente')
    transaccion_pago = models.OneToOneField(
        Transaccion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prestamo_liquidado',
    )

    class Meta:
        db_table = 'Prestamo'


class GastoCompartido(models.Model):
    idGastoComp = models.AutoField(primary_key=True, db_column='idGastoComp')
    idUsuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='idUsuario',
        null=True,
        blank=True,
        related_name='gastos_compartidos',
    )
    idTransaccion = models.OneToOneField(
        Transaccion,
        on_delete=models.CASCADE,
        db_column='idTransaccion',
        unique=True,
    )
    descripcion = models.CharField(max_length=255)
    montoTotal = models.DecimalField(max_digits=10, decimal_places=2)
    mi_parte = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    yo_pague_total = models.BooleanField(default=True)
    estado = models.CharField(max_length=50, default='Pendiente')
    creado_en = models.DateField(default=timezone.localdate)

    class Meta:
        db_table = 'GastoCompartido'
        ordering = ['-creado_en', '-idGastoComp']


class Participante(models.Model):
    idParticipante = models.AutoField(primary_key=True, db_column='idParticipante')
    idGastoComp = models.ForeignKey(
        GastoCompartido,
        on_delete=models.CASCADE,
        db_column='idGastoComp',
        related_name='participantes',
    )
    nombreAmigo = models.CharField(max_length=100)
    parteAportada = models.DecimalField(max_digits=10, decimal_places=2)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)
    transaccion_reembolso = models.OneToOneField(
        Transaccion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reembolso_participante',
    )

    class Meta:
        db_table = 'Participante'


class Notificacion(models.Model):
    idNotificacion = models.AutoField(primary_key=True, db_column='idNotificacion')
    idUsuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='idUsuario',
        related_name='notificaciones',
    )
    clave = models.CharField(max_length=80, blank=True, default='')
    tipo = models.CharField(max_length=30, default='info')
    nivel = models.CharField(max_length=16, default='info')
    titulo = models.CharField(max_length=120)
    mensaje = models.CharField(max_length=280)
    url_destino = models.CharField(max_length=120, default='/app/insights/?tab=control')
    leida = models.BooleanField(default=False)
    descartada = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Notificacion'
        ordering = ['-creada_en', '-idNotificacion']
        indexes = [
            models.Index(fields=['idUsuario', 'leida'], name='idx_notif_usr_leida'),
            models.Index(fields=['idUsuario', 'clave'], name='idx_notif_usr_clave'),
            models.Index(fields=['idUsuario', 'descartada', 'leida'], name='idx_notif_usr_desc_leida'),
        ]
