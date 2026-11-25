-- Esquema relacional de referencia de Mishi (alineado con modelos Django y migraciones 0001-0012).
-- Nota: Django gestiona la creación y evolución del esquema mediante `python manage.py migrate`.

CREATE DATABASE IF NOT EXISTS mishi_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mishi_db;

CREATE TABLE Usuario (
    idUsuario INT AUTO_INCREMENT PRIMARY KEY,
    cuenta_id INT UNIQUE NULL,
    nombre VARCHAR(100) NOT NULL,
    universidad VARCHAR(150) NOT NULL DEFAULT '',
    frecuencia VARCHAR(20) NOT NULL DEFAULT 'quincenal',
    mesada DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    saldo_inicial DECIMAL(12,2) NULL,
    fecha_proximo_ingreso DATE NULL,
    dia_pago_mensual SMALLINT UNSIGNED NULL,
    avatar VARCHAR(40) NOT NULL DEFAULT 'mishi-naranja-feliz',
    ocultar_saldo TINYINT(1) NOT NULL DEFAULT 0,
    alertas_activas TINYINT(1) NOT NULL DEFAULT 1,
    tema_visual VARCHAR(16) NOT NULL DEFAULT 'warm',
    acepto_politica_datos TINYINT(1) NOT NULL DEFAULT 0,
    fecha_aceptacion_datos DATETIME NULL,
    version_politica_datos VARCHAR(20) NOT NULL DEFAULT '',
    umbral_hormiga DECIMAL(10,2) NOT NULL DEFAULT 15000.00
);

CREATE TABLE Presupuesto (
    idPresupuesto INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario INT NOT NULL UNIQUE,
    limiteDiario DECIMAL(10,2) NOT NULL,
    limiteMensual DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE
);

CREATE TABLE Categoria (
    idCategoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    idUsuario INT NULL,
    es_personalizada TINYINT(1) NOT NULL DEFAULT 0,
    tipo_aplicable VARCHAR(20) NOT NULL DEFAULT 'ambos',
    tono VARCHAR(20) NOT NULL DEFAULT '',
    INDEX idx_cat_usuario_nombre (idUsuario, nombre),
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE
);

CREATE TABLE Presupuesto_Categoria (
    idPresupuestoCat INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario INT NOT NULL,
    idCategoria INT NOT NULL,
    limiteMensual DECIMAL(10,2) NOT NULL,
    actualizado_en DATETIME NOT NULL,
    UNIQUE KEY uniq_pres_cat_usuario_categoria (idUsuario, idCategoria),
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (idCategoria) REFERENCES Categoria(idCategoria) ON DELETE CASCADE
);

CREATE TABLE Meta_Ahorro (
    idMeta INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario INT NOT NULL,
    nombre VARCHAR(100) NOT NULL DEFAULT 'Mi meta',
    categoria VARCHAR(100) NOT NULL DEFAULT 'General',
    objetivo DECIMAL(10,2) NOT NULL,
    acumulado DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    fecha_objetivo DATE NULL,
    creada_en DATE NULL,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE
);

CREATE TABLE Aporte_Meta (
    idAporte INT AUTO_INCREMENT PRIMARY KEY,
    idMeta INT NOT NULL,
    idUsuario INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha DATE NOT NULL,
    nota VARCHAR(120) NOT NULL DEFAULT '',
    INDEX idx_aporte_usr_fecha (idUsuario, fecha),
    FOREIGN KEY (idMeta) REFERENCES Meta_Ahorro(idMeta) ON DELETE CASCADE,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE
);

CREATE TABLE Transaccion (
    idTransaccion INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario INT NOT NULL,
    idCategoria INT NOT NULL,
    descripcion VARCHAR(255) NOT NULL DEFAULT '',
    monto DECIMAL(10,2) NOT NULL,
    fecha DATE NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (idCategoria) REFERENCES Categoria(idCategoria) ON DELETE RESTRICT
);

CREATE TABLE Prestamo (
    idPrestamo INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario INT NOT NULL,
    deudor VARCHAR(100) NOT NULL,
    concepto VARCHAR(255) NOT NULL DEFAULT '',
    fecha DATE NOT NULL,
    fecha_limite DATE NULL,
    fecha_pago DATE NULL,
    tipo VARCHAR(50) NOT NULL DEFAULT 'Por cobrar',
    monto DECIMAL(10,2) NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'Pendiente',
    transaccion_pago_id INT UNIQUE NULL,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (transaccion_pago_id) REFERENCES Transaccion(idTransaccion) ON DELETE SET NULL
);

CREATE TABLE GastoCompartido (
    idGastoComp INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario INT NULL,
    idTransaccion INT NOT NULL UNIQUE,
    descripcion VARCHAR(255) NOT NULL,
    montoTotal DECIMAL(10,2) NOT NULL,
    mi_parte DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    yo_pague_total TINYINT(1) NOT NULL DEFAULT 1,
    estado VARCHAR(50) NOT NULL DEFAULT 'Pendiente',
    creado_en DATE NOT NULL,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (idTransaccion) REFERENCES Transaccion(idTransaccion) ON DELETE CASCADE
);

CREATE TABLE Participante (
    idParticipante INT AUTO_INCREMENT PRIMARY KEY,
    idGastoComp INT NOT NULL,
    nombreAmigo VARCHAR(100) NOT NULL,
    parteAportada DECIMAL(10,2) NOT NULL,
    pagado TINYINT(1) NOT NULL DEFAULT 0,
    fecha_pago DATE NULL,
    transaccion_reembolso_id INT UNIQUE NULL,
    FOREIGN KEY (idGastoComp) REFERENCES GastoCompartido(idGastoComp) ON DELETE CASCADE,
    FOREIGN KEY (transaccion_reembolso_id) REFERENCES Transaccion(idTransaccion) ON DELETE SET NULL
);

CREATE TABLE Notificacion (
    idNotificacion INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario INT NOT NULL,
    clave VARCHAR(80) NOT NULL DEFAULT '',
    tipo VARCHAR(30) NOT NULL DEFAULT 'info',
    nivel VARCHAR(16) NOT NULL DEFAULT 'info',
    titulo VARCHAR(120) NOT NULL,
    mensaje VARCHAR(280) NOT NULL,
    url_destino VARCHAR(120) NOT NULL DEFAULT '/app/insights/?tab=control',
    leida TINYINT(1) NOT NULL DEFAULT 0,
    descartada TINYINT(1) NOT NULL DEFAULT 0,
    creada_en DATETIME NOT NULL,
    INDEX idx_notif_usr_leida (idUsuario, leida),
    INDEX idx_notif_usr_clave (idUsuario, clave),
    INDEX idx_notif_usr_desc_leida (idUsuario, descartada, leida),
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE
);

INSERT INTO Categoria (nombre, idUsuario, es_personalizada, tipo_aplicable, tono) VALUES
    ('Alimentación', NULL, 0, 'ambos', ''),
    ('Transporte', NULL, 0, 'ambos', ''),
    ('Universidad', NULL, 0, 'ambos', ''),
    ('Ocio', NULL, 0, 'ambos', ''),
    ('Hogar', NULL, 0, 'ambos', ''),
    ('Salud', NULL, 0, 'ambos', ''),
    ('Mesada / Ingreso', NULL, 0, 'ambos', ''),
    ('Otros', NULL, 0, 'ambos', '');
