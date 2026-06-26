-- Crear base de datos
CREATE DATABASE IF NOT EXISTS concurso_danzas;
USE concurso_danzas;

-- Tabla de usuarios (admin)
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de participantes
CREATE TABLE participantes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_institucion VARCHAR(100) NOT NULL,
    nombre_danza VARCHAR(100) NOT NULL,
    categoria ENUM('A', 'B') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de calificaciones
CREATE TABLE calificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    participante_id INT NOT NULL,
    jurado1 DECIMAL(5,2) NOT NULL,
    jurado2 DECIMAL(5,2) NOT NULL,
    jurado3 DECIMAL(5,2) NOT NULL,
    puntaje_total DECIMAL(5,2) GENERATED ALWAYS AS (jurado1 + jurado2 + jurado3) STORED,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (participante_id) REFERENCES participantes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_participante (participante_id)
);

-- Insertar usuario admin por defecto
INSERT INTO usuarios (username, password) VALUES 
('admin', 'admin123'); -- En producción usar hash de contraseña