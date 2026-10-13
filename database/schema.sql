-- =============================================================================
-- Campus AV Móvil — Estructura de la base de datos (MySQL / MariaDB)
--
-- Crear la base (una sola vez):
--   CREATE DATABASE amancio_app_movil CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- Crear las tablas:
--   flask --app run crear-tablas      (ejecuta este archivo)
--
-- Usa IF NOT EXISTS: si una tabla ya existe, no se toca.
-- FOREIGN_KEY_CHECKS = 0 permite crear las tablas en cualquier orden aunque
-- unas apunten a otras; al final se vuelve a activar.
-- =============================================================================

SET FOREIGN_KEY_CHECKS = 0;


-- =============================================================================
-- USUARIOS Y PERSONAS
-- Cuentas de acceso y fichas de cada tipo de persona.
-- =============================================================================
CREATE TABLE IF NOT EXISTS `usuario` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `rol` enum('ADMIN','DOCENTE','ALUMNO','AUXILIAR','PSICOLOGO') NOT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `debe_cambiar_password` tinyint(1) NOT NULL,
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `username` (`username`),
  KEY `ix_usuario_id_usuario` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `familiar` (
  `id_familiar` int(11) NOT NULL AUTO_INCREMENT,
  `dni` varchar(8) DEFAULT NULL,
  `nombres` varchar(250) DEFAULT NULL,
  `apellidos` varchar(250) DEFAULT NULL,
  `telefono` varchar(9) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `direccion` varchar(300) DEFAULT NULL,
  PRIMARY KEY (`id_familiar`),
  UNIQUE KEY `dni` (`dni`),
  KEY `ix_familiar_id_familiar` (`id_familiar`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `alumno` (
  `id_alumno` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) DEFAULT NULL,
  `dni` varchar(8) DEFAULT NULL,
  `nombres` varchar(250) NOT NULL,
  `apellidos` varchar(250) NOT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `genero` varchar(1) DEFAULT NULL,
  `direccion` varchar(300) DEFAULT NULL,
  `enfermedad` varchar(150) DEFAULT NULL,
  `talla_polo` varchar(5) DEFAULT NULL,
  `colegio_procedencia` varchar(100) DEFAULT NULL,
  `id_grado_ingreso` int(11) DEFAULT NULL,
  `relacion_fraternal` tinyint(1) DEFAULT NULL,
  `estado_ingreso` varchar(20) DEFAULT NULL,
  `motivo_rechazo` text DEFAULT NULL,
  `doc_dni_menor` varchar(500) DEFAULT NULL,
  `doc_dni_apoderado` varchar(500) DEFAULT NULL,
  `doc_fum` varchar(500) DEFAULT NULL,
  `doc_certificado_estudios` varchar(500) DEFAULT NULL,
  `id_familiar` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_alumno`),
  UNIQUE KEY `id_usuario` (`id_usuario`),
  UNIQUE KEY `dni` (`dni`),
  KEY `id_grado_ingreso` (`id_grado_ingreso`),
  KEY `id_familiar` (`id_familiar`),
  KEY `ix_alumno_id_alumno` (`id_alumno`),
  CONSTRAINT `alumno_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`),
  CONSTRAINT `alumno_ibfk_2` FOREIGN KEY (`id_grado_ingreso`) REFERENCES `grado` (`id_grado`),
  CONSTRAINT `alumno_ibfk_3` FOREIGN KEY (`id_familiar`) REFERENCES `familiar` (`id_familiar`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `docente` (
  `id_docente` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) DEFAULT NULL,
  `dni` varchar(8) NOT NULL,
  `nombres` varchar(250) NOT NULL,
  `apellidos` varchar(250) NOT NULL,
  `especialidad` varchar(100) DEFAULT NULL,
  `descripcion` text DEFAULT NULL,
  `telefono` varchar(9) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `url_perfil` varchar(255) DEFAULT NULL,
  `visible_web` tinyint(1) NOT NULL,
  PRIMARY KEY (`id_docente`),
  UNIQUE KEY `ix_docente_dni` (`dni`),
  UNIQUE KEY `id_usuario` (`id_usuario`),
  KEY `ix_docente_id_docente` (`id_docente`),
  CONSTRAINT `docente_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `administrador` (
  `id_admin` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) DEFAULT NULL,
  `dni` varchar(8) NOT NULL,
  `nombres` varchar(250) NOT NULL,
  `apellidos` varchar(250) NOT NULL,
  `telefono` varchar(9) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `url_perfil` varchar(255) DEFAULT NULL,
  `permisos` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`permisos`)),
  PRIMARY KEY (`id_admin`),
  UNIQUE KEY `dni` (`dni`),
  UNIQUE KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `administrador_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `auxiliar` (
  `id_auxiliar` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) DEFAULT NULL,
  `dni` varchar(8) NOT NULL,
  `nombres` varchar(250) NOT NULL,
  `apellidos` varchar(250) NOT NULL,
  `telefono` varchar(9) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_auxiliar`),
  UNIQUE KEY `dni` (`dni`),
  UNIQUE KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `auxiliar_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `psicologo` (
  `id_psicologo` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) DEFAULT NULL,
  `dni` varchar(8) NOT NULL,
  `nombres` varchar(250) NOT NULL,
  `apellidos` varchar(250) NOT NULL,
  `telefono` varchar(9) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_psicologo`),
  UNIQUE KEY `dni` (`dni`),
  UNIQUE KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `psicologo_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- ESTRUCTURA ACADÉMICA
-- Año escolar, bimestres, niveles, grados, secciones, áreas y cursos.
-- =============================================================================
CREATE TABLE IF NOT EXISTS `anio_escolar` (
  `id_anio_escolar` varchar(6) NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date DEFAULT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `tipo` varchar(20) DEFAULT NULL,
  `inicio_inscripcion` date DEFAULT NULL,
  `fin_inscripcion` date DEFAULT NULL,
  PRIMARY KEY (`id_anio_escolar`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `bimestre` (
  `id_bimestre` int(11) NOT NULL AUTO_INCREMENT,
  `id_anio_escolar` varchar(6) NOT NULL,
  `numero` int(11) NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  PRIMARY KEY (`id_bimestre`),
  UNIQUE KEY `uq_bimestre_anio_numero` (`id_anio_escolar`,`numero`),
  CONSTRAINT `bimestre_ibfk_1` FOREIGN KEY (`id_anio_escolar`) REFERENCES `anio_escolar` (`id_anio_escolar`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `nivel` (
  `id_nivel` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(20) NOT NULL,
  PRIMARY KEY (`id_nivel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `grado` (
  `id_grado` int(11) NOT NULL AUTO_INCREMENT,
  `id_nivel` int(11) DEFAULT NULL,
  `nombre` varchar(20) NOT NULL,
  `orden` int(11) NOT NULL,
  PRIMARY KEY (`id_grado`),
  KEY `id_nivel` (`id_nivel`),
  CONSTRAINT `grado_ibfk_1` FOREIGN KEY (`id_nivel`) REFERENCES `nivel` (`id_nivel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `seccion` (
  `id_seccion` int(11) NOT NULL AUTO_INCREMENT,
  `id_grado` int(11) DEFAULT NULL,
  `id_anio_escolar` char(6) NOT NULL,
  `nombre` varchar(30) NOT NULL,
  `vacantes` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_seccion`),
  KEY `id_grado` (`id_grado`),
  KEY `id_anio_escolar` (`id_anio_escolar`),
  CONSTRAINT `seccion_ibfk_1` FOREIGN KEY (`id_grado`) REFERENCES `grado` (`id_grado`),
  CONSTRAINT `seccion_ibfk_2` FOREIGN KEY (`id_anio_escolar`) REFERENCES `anio_escolar` (`id_anio_escolar`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `area` (
  `id_area` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `orden_primaria` int(11) DEFAULT NULL,
  `orden_secundaria` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_area`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `curso` (
  `id_curso` int(11) NOT NULL AUTO_INCREMENT,
  `id_area` int(11) DEFAULT NULL,
  `nombre` varchar(100) NOT NULL,
  `minutos_semanales` int(11) DEFAULT NULL,
  `es_verano` tinyint(1) DEFAULT NULL,
  `tipo_verano` varchar(20) DEFAULT NULL,
  `grupo_verano` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_curso`),
  KEY `id_area` (`id_area`),
  CONSTRAINT `curso_ibfk_1` FOREIGN KEY (`id_area`) REFERENCES `area` (`id_area`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `plan_estudio` (
  `id_plan_estudio` int(11) NOT NULL AUTO_INCREMENT,
  `id_curso` int(11) DEFAULT NULL,
  `id_grado` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_plan_estudio`),
  KEY `id_curso` (`id_curso`),
  KEY `id_grado` (`id_grado`),
  CONSTRAINT `plan_estudio_ibfk_1` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id_curso`),
  CONSTRAINT `plan_estudio_ibfk_2` FOREIGN KEY (`id_grado`) REFERENCES `grado` (`id_grado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- MATRÍCULA
-- En qué sección está cada alumno cada año.
-- =============================================================================
CREATE TABLE IF NOT EXISTS `matricula` (
  `id_matricula` int(11) NOT NULL AUTO_INCREMENT,
  `id_anio_escolar` varchar(6) DEFAULT NULL,
  `id_alumno` int(11) DEFAULT NULL,
  `id_seccion` int(11) DEFAULT NULL,
  `id_grado` int(11) DEFAULT NULL,
  `fecha_matricula` datetime DEFAULT NULL,
  `estado` varchar(20) DEFAULT NULL,
  `tipo_matricula` varchar(20) DEFAULT NULL,
  `condicion` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_matricula`),
  KEY `id_anio_escolar` (`id_anio_escolar`),
  KEY `id_alumno` (`id_alumno`),
  KEY `id_seccion` (`id_seccion`),
  KEY `id_grado` (`id_grado`),
  KEY `ix_matricula_id_matricula` (`id_matricula`),
  CONSTRAINT `matricula_ibfk_1` FOREIGN KEY (`id_anio_escolar`) REFERENCES `anio_escolar` (`id_anio_escolar`),
  CONSTRAINT `matricula_ibfk_2` FOREIGN KEY (`id_alumno`) REFERENCES `alumno` (`id_alumno`),
  CONSTRAINT `matricula_ibfk_3` FOREIGN KEY (`id_seccion`) REFERENCES `seccion` (`id_seccion`),
  CONSTRAINT `matricula_ibfk_4` FOREIGN KEY (`id_grado`) REFERENCES `grado` (`id_grado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `solicitud_matricula` (
  `id_solicitud_matricula` int(11) NOT NULL AUTO_INCREMENT,
  `id_alumno` int(11) NOT NULL,
  `id_anio_escolar_origen` varchar(6) DEFAULT NULL,
  `anio_destino` varchar(6) NOT NULL,
  `grado_destino` varchar(50) DEFAULT NULL,
  `comentario` text DEFAULT NULL,
  `estado` varchar(20) DEFAULT NULL,
  `respuesta_admin` text DEFAULT NULL,
  `fecha_solicitud` datetime DEFAULT NULL,
  PRIMARY KEY (`id_solicitud_matricula`),
  KEY `id_alumno` (`id_alumno`),
  KEY `ix_solicitud_matricula_id_solicitud_matricula` (`id_solicitud_matricula`),
  CONSTRAINT `solicitud_matricula_ibfk_1` FOREIGN KEY (`id_alumno`) REFERENCES `alumno` (`id_alumno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- GESTIÓN ACADÉMICA
-- Carga académica (qué docente dicta qué curso), asistencia y notas.
-- =============================================================================
CREATE TABLE IF NOT EXISTS `carga_academica` (
  `id_carga_academica` int(11) NOT NULL AUTO_INCREMENT,
  `id_anio_escolar` char(6) DEFAULT NULL,
  `id_seccion` int(11) DEFAULT NULL,
  `id_curso` int(11) DEFAULT NULL,
  `id_docente` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_carga_academica`),
  KEY `id_anio_escolar` (`id_anio_escolar`),
  KEY `id_seccion` (`id_seccion`),
  KEY `id_curso` (`id_curso`),
  KEY `id_docente` (`id_docente`),
  CONSTRAINT `carga_academica_ibfk_1` FOREIGN KEY (`id_anio_escolar`) REFERENCES `anio_escolar` (`id_anio_escolar`),
  CONSTRAINT `carga_academica_ibfk_2` FOREIGN KEY (`id_seccion`) REFERENCES `seccion` (`id_seccion`),
  CONSTRAINT `carga_academica_ibfk_3` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id_curso`),
  CONSTRAINT `carga_academica_ibfk_4` FOREIGN KEY (`id_docente`) REFERENCES `docente` (`id_docente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `asistencia` (
  `id_asistencia` int(11) NOT NULL AUTO_INCREMENT,
  `id_matricula` int(11) DEFAULT NULL,
  `fecha` date NOT NULL,
  `estado` varchar(1) NOT NULL,
  `observacion` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id_asistencia`),
  KEY `id_matricula` (`id_matricula`),
  CONSTRAINT `asistencia_ibfk_1` FOREIGN KEY (`id_matricula`) REFERENCES `matricula` (`id_matricula`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `nota` (
  `id_nota` int(11) NOT NULL AUTO_INCREMENT,
  `id_matricula` int(11) DEFAULT NULL,
  `id_curso` int(11) DEFAULT NULL,
  `bimestre` int(11) NOT NULL,
  `tipo_nota` varchar(20) DEFAULT NULL,
  `valor` decimal(4,2) NOT NULL,
  `fecha_registro` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_nota`),
  UNIQUE KEY `uq_nota_alumno_curso_bim` (`id_matricula`,`id_curso`,`bimestre`,`tipo_nota`),
  KEY `id_curso` (`id_curso`),
  CONSTRAINT `nota_ibfk_1` FOREIGN KEY (`id_matricula`) REFERENCES `matricula` (`id_matricula`),
  CONSTRAINT `nota_ibfk_2` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id_curso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `resumen_nota` (
  `id_resumen_notas` int(11) NOT NULL AUTO_INCREMENT,
  `id_matricula` int(11) DEFAULT NULL,
  `id_curso` int(11) DEFAULT NULL,
  `nota_bimestre1` decimal(5,2) DEFAULT NULL,
  `nota_bimestre2` decimal(5,2) DEFAULT NULL,
  `nota_bimestre3` decimal(5,2) DEFAULT NULL,
  `nota_bimestre4` decimal(5,2) DEFAULT NULL,
  `promedio_final` decimal(5,2) DEFAULT NULL,
  `estado_curso` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_resumen_notas`),
  UNIQUE KEY `uq_resumen_alumno_curso` (`id_matricula`,`id_curso`),
  KEY `id_curso` (`id_curso`),
  CONSTRAINT `resumen_nota_ibfk_1` FOREIGN KEY (`id_matricula`) REFERENCES `matricula` (`id_matricula`),
  CONSTRAINT `resumen_nota_ibfk_2` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id_curso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `curso_nota_automatica` (
  `id_curso` int(11) NOT NULL,
  `id_grado` int(11) NOT NULL,
  `valor` decimal(4,2) NOT NULL,
  PRIMARY KEY (`id_curso`,`id_grado`),
  KEY `id_grado` (`id_grado`),
  CONSTRAINT `curso_nota_automatica_ibfk_1` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id_curso`),
  CONSTRAINT `curso_nota_automatica_ibfk_2` FOREIGN KEY (`id_grado`) REFERENCES `grado` (`id_grado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- AULA VIRTUAL Y MENSAJERÍA
-- Material, tareas, entregas y mensajes.
-- =============================================================================
CREATE TABLE IF NOT EXISTS `material_clase` (
  `id_material` int(11) NOT NULL AUTO_INCREMENT,
  `id_carga_academica` int(11) DEFAULT NULL,
  `titulo` varchar(150) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `archivo_url` varchar(255) DEFAULT NULL,
  `bimestre` int(11) NOT NULL,
  `fecha_publicacion` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_material`),
  KEY `id_carga_academica` (`id_carga_academica`),
  CONSTRAINT `material_clase_ibfk_1` FOREIGN KEY (`id_carga_academica`) REFERENCES `carga_academica` (`id_carga_academica`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `tarea` (
  `id_tarea` int(11) NOT NULL AUTO_INCREMENT,
  `id_carga_academica` int(11) DEFAULT NULL,
  `titulo` varchar(150) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `fecha_publicacion` datetime DEFAULT current_timestamp(),
  `fecha_entrega` datetime DEFAULT NULL,
  `archivo_adjunto_url` varchar(255) DEFAULT NULL,
  `estado` varchar(20) DEFAULT NULL,
  `tipo_evaluacion` varchar(30) DEFAULT NULL,
  `bimestre` int(11) NOT NULL,
  `peso` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_tarea`),
  KEY `id_carga_academica` (`id_carga_academica`),
  CONSTRAINT `tarea_ibfk_1` FOREIGN KEY (`id_carga_academica`) REFERENCES `carga_academica` (`id_carga_academica`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `entrega_tarea` (
  `id_entrega` int(11) NOT NULL AUTO_INCREMENT,
  `id_tarea` int(11) DEFAULT NULL,
  `id_alumno` int(11) DEFAULT NULL,
  `archivo_url` varchar(255) DEFAULT NULL,
  `comentario_alumno` text DEFAULT NULL,
  `fecha_envio` datetime DEFAULT current_timestamp(),
  `calificacion` decimal(4,2) DEFAULT NULL,
  `retroalimentacion_docente` text DEFAULT NULL,
  PRIMARY KEY (`id_entrega`),
  KEY `id_tarea` (`id_tarea`),
  KEY `id_alumno` (`id_alumno`),
  CONSTRAINT `entrega_tarea_ibfk_1` FOREIGN KEY (`id_tarea`) REFERENCES `tarea` (`id_tarea`),
  CONSTRAINT `entrega_tarea_ibfk_2` FOREIGN KEY (`id_alumno`) REFERENCES `alumno` (`id_alumno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `conversacion` (
  `id_conversacion` int(11) NOT NULL AUTO_INCREMENT,
  `usuario1_id` int(11) DEFAULT NULL,
  `usuario2_id` int(11) DEFAULT NULL,
  `ultimo_mensaje` text DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_conversacion`),
  KEY `usuario1_id` (`usuario1_id`),
  KEY `usuario2_id` (`usuario2_id`),
  CONSTRAINT `conversacion_ibfk_1` FOREIGN KEY (`usuario1_id`) REFERENCES `usuario` (`id_usuario`),
  CONSTRAINT `conversacion_ibfk_2` FOREIGN KEY (`usuario2_id`) REFERENCES `usuario` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `mensaje` (
  `id_mensaje` int(11) NOT NULL AUTO_INCREMENT,
  `id_conversacion` int(11) DEFAULT NULL,
  `remitente_id` int(11) DEFAULT NULL,
  `contenido` text NOT NULL,
  `leido` tinyint(1) DEFAULT NULL,
  `fecha_envio` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_mensaje`),
  KEY `id_conversacion` (`id_conversacion`),
  KEY `remitente_id` (`remitente_id`),
  CONSTRAINT `mensaje_ibfk_1` FOREIGN KEY (`id_conversacion`) REFERENCES `conversacion` (`id_conversacion`),
  CONSTRAINT `mensaje_ibfk_2` FOREIGN KEY (`remitente_id`) REFERENCES `usuario` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- NOTIFICACIONES
-- Token de notificaciones push de cada celular.
-- =============================================================================
CREATE TABLE IF NOT EXISTS `dispositivo_push` (
  `id_dispositivo` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `token` varchar(255) NOT NULL,
  `plataforma` varchar(20) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `fecha_registro` datetime DEFAULT current_timestamp(),
  `fecha_actualizacion` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_dispositivo`),
  UNIQUE KEY `token` (`token`),
  KEY `ix_dispositivo_push_id_usuario` (`id_usuario`),
  CONSTRAINT `dispositivo_push_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- CLASES VIRTUALES
-- Enlaces (Meet, Zoom...) de las clases en línea de cada curso.
-- =============================================================================
CREATE TABLE IF NOT EXISTS `clase_virtual` (
  `id_clase_virtual` int(11) NOT NULL AUTO_INCREMENT,
  `id_carga_academica` int(11) NOT NULL,
  `tema` varchar(150) DEFAULT NULL,
  `fecha` datetime NOT NULL,
  `enlace` varchar(500) NOT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_clase_virtual`),
  KEY `id_carga_academica` (`id_carga_academica`),
  CONSTRAINT `clase_virtual_ibfk_1` FOREIGN KEY (`id_carga_academica`) REFERENCES `carga_academica` (`id_carga_academica`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- HORARIO ESCOLAR
-- Bloques de clase de cada curso (carga académica) y recesos de la jornada.
-- dia_semana: 1 = lunes ... 5 = viernes.
-- =============================================================================
CREATE TABLE IF NOT EXISTS `horario_escolar` (
  `id_horario` int(11) NOT NULL AUTO_INCREMENT,
  `id_carga_academica` int(11) NOT NULL,
  `dia_semana` tinyint(4) NOT NULL,
  `hora_inicio` time NOT NULL,
  `hora_fin` time NOT NULL,
  PRIMARY KEY (`id_horario`),
  KEY `id_carga_academica` (`id_carga_academica`),
  CONSTRAINT `horario_escolar_ibfk_1` FOREIGN KEY (`id_carga_academica`) REFERENCES `carga_academica` (`id_carga_academica`),
  CONSTRAINT `chk_horario_dia` CHECK (`dia_semana` between 1 and 5),
  CONSTRAINT `chk_horario_horas` CHECK (`hora_inicio` < `hora_fin`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `receso_horario` (
  `id_receso` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(40) NOT NULL DEFAULT 'Recreo',
  `hora_inicio` time NOT NULL,
  `hora_fin` time NOT NULL,
  PRIMARY KEY (`id_receso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- CONDUCTA
-- tipo_falta: Leve, Grave, Muy grave.
-- nivel_conducta: el catálogo de faltas, con los puntos que descuenta cada una.
-- reporte_conducta: un reporte (parte) registrado por el auxiliar. Se ANULA
--   (no se borra): queda el motivo, quién lo anuló y cuándo.
-- La nota de conducta NO se guarda: se calcula como 20 menos los puntos de los
-- reportes vigentes del bimestre.
-- =============================================================================
CREATE TABLE IF NOT EXISTS `tipo_falta` (
  `id_tipo_falta` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(60) NOT NULL,
  PRIMARY KEY (`id_tipo_falta`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `nivel_conducta` (
  `id_nivel_conducta` int(11) NOT NULL AUTO_INCREMENT,
  `id_tipo_falta` int(11) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `puntos` int(11) NOT NULL,
  `descripcion` text DEFAULT NULL,
  PRIMARY KEY (`id_nivel_conducta`),
  KEY `id_tipo_falta` (`id_tipo_falta`),
  CONSTRAINT `nivel_conducta_ibfk_1` FOREIGN KEY (`id_tipo_falta`) REFERENCES `tipo_falta` (`id_tipo_falta`),
  CONSTRAINT `chk_nivel_puntos` CHECK (`puntos` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `reporte_conducta` (
  `id_reporte` int(11) NOT NULL AUTO_INCREMENT,
  `id_alumno` int(11) NOT NULL,
  `id_nivel_conducta` int(11) NOT NULL,
  `registrado_por` int(11) NOT NULL,
  `fecha_reporte` datetime NOT NULL DEFAULT current_timestamp(),
  `descripcion_suceso` text NOT NULL,
  `evidencia_url` varchar(500) DEFAULT NULL,
  `estado` varchar(20) NOT NULL DEFAULT 'REGISTRADO',
  `motivo_anulacion` varchar(300) DEFAULT NULL,
  `anulado_por` int(11) DEFAULT NULL,
  `fecha_anulacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id_reporte`),
  KEY `id_alumno` (`id_alumno`),
  KEY `id_nivel_conducta` (`id_nivel_conducta`),
  KEY `registrado_por` (`registrado_por`),
  KEY `anulado_por` (`anulado_por`),
  CONSTRAINT `reporte_conducta_ibfk_1` FOREIGN KEY (`id_alumno`) REFERENCES `alumno` (`id_alumno`),
  CONSTRAINT `reporte_conducta_ibfk_2` FOREIGN KEY (`id_nivel_conducta`) REFERENCES `nivel_conducta` (`id_nivel_conducta`),
  CONSTRAINT `reporte_conducta_ibfk_3` FOREIGN KEY (`registrado_por`) REFERENCES `usuario` (`id_usuario`),
  CONSTRAINT `reporte_conducta_ibfk_4` FOREIGN KEY (`anulado_por`) REFERENCES `usuario` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- CITAS DE PSICOLOGÍA
-- estado: PENDIENTE (solicitada) → PROGRAMADA → ATENDIDA, o CANCELADA.
-- observacion: lo que anota el psicólogo; el alumno no la ve.
-- =============================================================================
CREATE TABLE IF NOT EXISTS `cita_psicologia` (
  `id_cita` int(11) NOT NULL AUTO_INCREMENT,
  `id_alumno` int(11) NOT NULL,
  `id_psicologo` int(11) DEFAULT NULL,
  `motivo` varchar(200) NOT NULL,
  `disponibilidad` varchar(200) DEFAULT NULL,
  `fecha_cita` datetime DEFAULT NULL,
  `estado` varchar(20) NOT NULL DEFAULT 'PENDIENTE',
  `observacion` text DEFAULT NULL,
  `motivo_cancelacion` varchar(300) DEFAULT NULL,
  `fecha_solicitud` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_cita`),
  KEY `id_alumno` (`id_alumno`),
  KEY `id_psicologo` (`id_psicologo`),
  CONSTRAINT `cita_psicologia_ibfk_1` FOREIGN KEY (`id_alumno`) REFERENCES `alumno` (`id_alumno`),
  CONSTRAINT `cita_psicologia_ibfk_2` FOREIGN KEY (`id_psicologo`) REFERENCES `psicologo` (`id_psicologo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- CIERRE DE BIMESTRE (notas)
-- Cuando el docente cierra un bimestre de un curso, se guarda aquí. Desde ese
-- momento las notas de ese bimestre ya no se pueden cambiar, y su promedio pasa
-- a la libreta (tabla resumen_nota).
-- =============================================================================
CREATE TABLE IF NOT EXISTS `cierre_bimestre` (
  `id_cierre` int(11) NOT NULL AUTO_INCREMENT,
  `id_carga_academica` int(11) NOT NULL,
  `bimestre` tinyint(4) NOT NULL,
  `cerrado_por` int(11) NOT NULL,
  `fecha_cierre` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_cierre`),
  UNIQUE KEY `uq_cierre_carga_bimestre` (`id_carga_academica`,`bimestre`),
  KEY `cerrado_por` (`cerrado_por`),
  CONSTRAINT `cierre_bimestre_ibfk_1` FOREIGN KEY (`id_carga_academica`) REFERENCES `carga_academica` (`id_carga_academica`),
  CONSTRAINT `cierre_bimestre_ibfk_2` FOREIGN KEY (`cerrado_por`) REFERENCES `usuario` (`id_usuario`),
  CONSTRAINT `chk_cierre_bimestre` CHECK (`bimestre` between 1 and 4)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
