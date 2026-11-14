CREATE DATABASE IF NOT EXISTS mishi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mishi;

CREATE TABLE Usuario (
    idUsuario INT AUTO_INCREMENT PRIMARY KEY,
    cuenta_id INT UNIQUE NULL,
    nombre VARCHAR(100) NOT NULL,
    universidad VARCHAR(150) NOT NULL DEFAULT '',
    frecuencia VARCHAR(20) NOT NULL DEFAULT 'quincenal',
    mesada DECIMAL(10,2) NOT NULL DEFAULT 0.00
);

CREATE TABLE Presupuesto (
    idPresupuesto INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario INT NOT NULL UNIQUE,
    limiteDiario DECIMAL(10,2) NOT NULL,
    limiteMensual DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE
);

CREATE TABLE Meta_Ahorro (
    idMeta INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario INT NOT NULL,
    nombre VARCHAR(100) NOT NULL DEFAULT 'Mi meta',
    categoria VARCHAR(100) NOT NULL DEFAULT 'General',
    objetivo DECIMAL(10,2) NOT NULL,
    acumulado DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE
);

CREATE TABLE Categoria (
    idCategoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
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
    FOREIGN KEY (idCategoria) REFERENCES Categoria(idCategoria)
);

CREATE TABLE Prestamo (
    idPrestamo INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario INT NOT NULL,
    deudor VARCHAR(100) NOT NULL,
    concepto VARCHAR(255) NOT NULL DEFAULT '',
    fecha DATE NOT NULL,
    tipo VARCHAR(50) NOT NULL DEFAULT 'Por cobrar',
    monto DECIMAL(10,2) NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'Pendiente',
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE
);

CREATE TABLE GastoCompartido (
    idGastoComp INT AUTO_INCREMENT PRIMARY KEY,
    idTransaccion INT NOT NULL UNIQUE,
    descripcion VARCHAR(255) NOT NULL,
    montoTotal DECIMAL(10,2) NOT NULL,
    estado VARCHAR(50) NOT NULL,
    FOREIGN KEY (idTransaccion) REFERENCES Transaccion(idTransaccion) ON DELETE CASCADE
);

CREATE TABLE Participante (
    idParticipante INT AUTO_INCREMENT PRIMARY KEY,
    idGastoComp INT NOT NULL,
    nombreAmigo VARCHAR(100) NOT NULL,
    parteAportada DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (idGastoComp) REFERENCES GastoCompartido(idGastoComp) ON DELETE CASCADE
);

INSERT INTO Categoria (nombre) VALUES
    ('Alimentación'),
    ('Transporte'),
    ('Universidad'),
    ('Ocio'),
    ('Hogar'),
    ('Salud'),
    ('Mesada / Ingreso'),
    ('Otros');
