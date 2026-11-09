from django.contrib import admin
from .models import (
    Usuario,
    Presupuesto,
    MetaAhorro,
    Categoria,
    Transaccion,
    Prestamo,
    GastoCompartido,
    Participante
)

admin.site.register(Usuario)
admin.site.register(Presupuesto)
admin.site.register(MetaAhorro)
admin.site.register(Categoria)
admin.site.register(Transaccion)
admin.site.register(Prestamo)
admin.site.register(GastoCompartido)
admin.site.register(Participante)