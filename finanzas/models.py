from decimal import Decimal

from django.db import models


class Usuario(models.Model):
    idUsuario = models.AutoField(primary_key=True, db_column='idUsuario')
    nombre = models.CharField(max_length=100)
    mesada = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

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
    idUsuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='idUsuario',
    )
    objetivo = models.DecimalField(max_digits=10, decimal_places=2)
    acumulado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'Meta_Ahorro'


class Categoria(models.Model):
    idCategoria = models.AutoField(primary_key=True, db_column='idCategoria')
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'Categoria'


class Transaccion(models.Model):
    idTransaccion = models.AutoField(primary_key=True, db_column='idTransaccion')
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
    idUsuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='idUsuario',
    )
    deudor = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=50)

    class Meta:
        db_table = 'Prestamo'


class GastoCompartido(models.Model):
    idGastoComp = models.AutoField(primary_key=True, db_column='idGastoComp')
    idTransaccion = models.OneToOneField(
        Transaccion,
        on_delete=models.CASCADE,
        db_column='idTransaccion',
        unique=True,
    )
    descripcion = models.CharField(max_length=255)
    montoTotal = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=50)

    class Meta:
        db_table = 'GastoCompartido'


class Participante(models.Model):
    idParticipante = models.AutoField(primary_key=True, db_column='idParticipante')
    idGastoComp = models.ForeignKey(
        GastoCompartido,
        on_delete=models.CASCADE,
        db_column='idGastoComp',
    )
    nombreAmigo = models.CharField(max_length=100)
    parteAportada = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'Participante'
