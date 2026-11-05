CREATE DATABASE IF NOT EXISTS mishi;
USE mishi;

CREATE TABLE Usuario (
    idUsuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    mesada DECIMAL(10,2) NOT NULL
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
    monto DECIMAL(10,2) NOT NULL,
    estado VARCHAR(50) NOT NULL,
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