"""Catálogo oficial de los 15 avatares PNG personalizados de Mishi."""

AVATAR_DEFECTO = 'mishi-naranja-feliz'
TEMAS_VALIDOS = ('warm', 'pure')

AVATARES_MISHI = (
    {'id': 'mishi-naranja-feliz', 'nombre': 'Naranja feliz', 'archivo': 'img/mishi-avatars/avatars/mishi-naranja-feliz.png'},
    {'id': 'mishi-naranja-audifonos', 'nombre': 'Con audífonos', 'archivo': 'img/mishi-avatars/avatars/mishi-naranja-audifonos.png'},
    {'id': 'mishi-naranja-gorra', 'nombre': 'Con gorra', 'archivo': 'img/mishi-avatars/avatars/mishi-naranja-gorra.png'},
    {'id': 'mishi-blanco-gafas', 'nombre': 'Cool gafas', 'archivo': 'img/mishi-avatars/avatars/mishi-blanco-gafas.png'},
    {'id': 'mishi-blanco-lazo', 'nombre': 'Con lazo', 'archivo': 'img/mishi-avatars/avatars/mishi-blanco-lazo.png'},
    {'id': 'mishi-blanco-corazones', 'nombre': 'Cariñoso', 'archivo': 'img/mishi-avatars/avatars/mishi-blanco-corazones.png'},
    {'id': 'mishi-blanco-esponjoso', 'nombre': 'Esponjoso', 'archivo': 'img/mishi-avatars/avatars/mishi-blanco-esponjoso.png'},
    {'id': 'mishi-calico', 'nombre': 'Calicó guiño', 'archivo': 'img/mishi-avatars/avatars/mishi-calico.png'},
    {'id': 'mishi-gris-lector', 'nombre': 'Lector', 'archivo': 'img/mishi-avatars/avatars/mishi-gris-lector.png'},
    {'id': 'mishi-gris-dormilon', 'nombre': 'Dormilón', 'archivo': 'img/mishi-avatars/avatars/mishi-gris-dormilon.png'},
    {'id': 'mishi-gris-saludo', 'nombre': 'Saludando', 'archivo': 'img/mishi-avatars/avatars/mishi-gris-saludo.png'},
    {'id': 'mishi-negro-capucha', 'nombre': 'Con capucha', 'archivo': 'img/mishi-avatars/avatars/mishi-negro-capucha.png'},
    {'id': 'mishi-negro-travieso', 'nombre': 'Travieso', 'archivo': 'img/mishi-avatars/avatars/mishi-negro-travieso.png'},
    {'id': 'mishi-siames', 'nombre': 'Siamés', 'archivo': 'img/mishi-avatars/avatars/mishi-siames.png'},
    {'id': 'mishi-tuxedo', 'nombre': 'Elegante', 'archivo': 'img/mishi-avatars/avatars/mishi-tuxedo.png'},
)

AVATARES_POR_ID = {item['id']: item for item in AVATARES_MISHI}


def es_avatar_valido(avatar_id):
    return (avatar_id or '').strip() in AVATARES_POR_ID


def obtener_avatar_info(avatar_id):
    clave = (avatar_id or '').strip()
    return AVATARES_POR_ID.get(clave, AVATARES_POR_ID[AVATAR_DEFECTO])
