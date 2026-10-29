-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: 127.0.0.1    Database: amancio_app_movil
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `amancio_app_movil`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `amancio_app_movil` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;

USE `amancio_app_movil`;

--
-- Table structure for table `administrador`
--

DROP TABLE IF EXISTS `administrador`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `administrador` (
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `administrador`
--

LOCK TABLES `administrador` WRITE;
/*!40000 ALTER TABLE `administrador` DISABLE KEYS */;
INSERT INTO `administrador` VALUES (1,1,'11111111','Ana','Torres Ruiz','911111111','admin@example.com',NULL,'[\"*\"]');
/*!40000 ALTER TABLE `administrador` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alumno`
--

DROP TABLE IF EXISTS `alumno`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `alumno` (
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
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alumno`
--

LOCK TABLES `alumno` WRITE;
/*!40000 ALTER TABLE `alumno` DISABLE KEYS */;
INSERT INTO `alumno` VALUES (1,6,'33333333','Lucía','Quispe Flores',NULL,'F','Av. Los Próceres 123, Lima',NULL,NULL,NULL,NULL,1,'ESTUDIANTE',NULL,NULL,NULL,NULL,NULL,1),(2,7,'44444444','Mateo','Quispe Flores',NULL,'M','Av. Los Próceres 123, Lima',NULL,NULL,NULL,NULL,1,'ESTUDIANTE',NULL,NULL,NULL,NULL,NULL,1),(3,8,'71111111','Sofía','Ramírez Torres',NULL,'F','Av. Los Próceres 123, Lima',NULL,NULL,NULL,NULL,0,'ESTUDIANTE',NULL,NULL,NULL,NULL,NULL,NULL),(4,9,'72222222','Diego','Castillo León',NULL,'M','Av. Los Próceres 123, Lima',NULL,NULL,NULL,NULL,0,'ESTUDIANTE',NULL,NULL,NULL,NULL,NULL,NULL),(5,10,'73333333','Valeria','Huamán Rojas',NULL,'F','Av. Los Próceres 123, Lima',NULL,NULL,NULL,NULL,0,'ESTUDIANTE',NULL,NULL,NULL,NULL,NULL,NULL),(6,11,'74444444','Andrés','Paredes Silva',NULL,'M','Av. Los Próceres 123, Lima',NULL,NULL,NULL,NULL,0,'ESTUDIANTE',NULL,NULL,NULL,NULL,NULL,NULL),(7,12,'75555555','Camila','Soto Medina',NULL,'F','Av. Los Próceres 123, Lima',NULL,NULL,NULL,NULL,0,'ESTUDIANTE',NULL,NULL,NULL,NULL,NULL,NULL),(8,13,'76666666','Joaquín','Vargas Ríos',NULL,'M','Av. Los Próceres 123, Lima',NULL,NULL,NULL,NULL,0,'ESTUDIANTE',NULL,NULL,NULL,NULL,NULL,NULL),(9,14,'79999999','Renata','Flores Cárdenas',NULL,'F','Av. Los Próceres 123, Lima',NULL,NULL,NULL,NULL,0,'ESTUDIANTE',NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `alumno` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `anio_escolar`
--

DROP TABLE IF EXISTS `anio_escolar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `anio_escolar` (
  `id_anio_escolar` varchar(6) NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date DEFAULT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `tipo` varchar(20) DEFAULT NULL,
  `inicio_inscripcion` date DEFAULT NULL,
  `fin_inscripcion` date DEFAULT NULL,
  PRIMARY KEY (`id_anio_escolar`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `anio_escolar`
--

LOCK TABLES `anio_escolar` WRITE;
/*!40000 ALTER TABLE `anio_escolar` DISABLE KEYS */;
INSERT INTO `anio_escolar` VALUES ('2026','2026-03-09','2026-12-18',1,'REGULAR',NULL,NULL);
/*!40000 ALTER TABLE `anio_escolar` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `area`
--

DROP TABLE IF EXISTS `area`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `area` (
  `id_area` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `orden_primaria` int(11) DEFAULT NULL,
  `orden_secundaria` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_area`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `area`
--

LOCK TABLES `area` WRITE;
/*!40000 ALTER TABLE `area` DISABLE KEYS */;
INSERT INTO `area` VALUES (1,'Matemática',NULL,NULL),(2,'Comunicación',NULL,NULL),(3,'Ciencia y Tecnología',NULL,NULL);
/*!40000 ALTER TABLE `area` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `asistencia`
--

DROP TABLE IF EXISTS `asistencia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `asistencia` (
  `id_asistencia` int(11) NOT NULL AUTO_INCREMENT,
  `id_matricula` int(11) DEFAULT NULL,
  `fecha` date NOT NULL,
  `estado` varchar(1) NOT NULL,
  `observacion` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id_asistencia`),
  KEY `id_matricula` (`id_matricula`),
  CONSTRAINT `asistencia_ibfk_1` FOREIGN KEY (`id_matricula`) REFERENCES `matricula` (`id_matricula`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asistencia`
--

LOCK TABLES `asistencia` WRITE;
/*!40000 ALTER TABLE `asistencia` DISABLE KEYS */;
INSERT INTO `asistencia` VALUES (1,1,'2026-10-05','P',NULL),(2,3,'2026-10-05','P',NULL),(3,4,'2026-10-05','T',NULL),(4,5,'2026-10-05','P',NULL),(5,6,'2026-10-05','P',NULL),(6,7,'2026-10-05','P',NULL),(7,8,'2026-10-05','F',NULL),(8,9,'2026-10-05','P',NULL),(9,1,'2026-10-06','F',NULL),(10,3,'2026-10-06','P',NULL),(11,4,'2026-10-06','P',NULL),(12,5,'2026-10-06','P',NULL),(13,6,'2026-10-06','T',NULL),(14,7,'2026-10-06','P',NULL),(15,8,'2026-10-06','P',NULL),(16,9,'2026-10-06','P',NULL),(17,1,'2026-10-07','P',NULL),(18,3,'2026-10-07','J',NULL),(19,4,'2026-10-07','P',NULL),(20,5,'2026-10-07','P',NULL),(21,6,'2026-10-07','P',NULL),(22,7,'2026-10-07','P',NULL),(23,8,'2026-10-07','F',NULL),(24,9,'2026-10-07','P',NULL);
/*!40000 ALTER TABLE `asistencia` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auxiliar`
--

DROP TABLE IF EXISTS `auxiliar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auxiliar` (
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auxiliar`
--

LOCK TABLES `auxiliar` WRITE;
/*!40000 ALTER TABLE `auxiliar` DISABLE KEYS */;
INSERT INTO `auxiliar` VALUES (1,4,'77777777','Jorge','Ramos Díaz','977777777','jorge@example.com');
/*!40000 ALTER TABLE `auxiliar` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bimestre`
--

DROP TABLE IF EXISTS `bimestre`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bimestre` (
  `id_bimestre` int(11) NOT NULL AUTO_INCREMENT,
  `id_anio_escolar` varchar(6) NOT NULL,
  `numero` int(11) NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  PRIMARY KEY (`id_bimestre`),
  UNIQUE KEY `uq_bimestre_anio_numero` (`id_anio_escolar`,`numero`),
  CONSTRAINT `bimestre_ibfk_1` FOREIGN KEY (`id_anio_escolar`) REFERENCES `anio_escolar` (`id_anio_escolar`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bimestre`
--

LOCK TABLES `bimestre` WRITE;
/*!40000 ALTER TABLE `bimestre` DISABLE KEYS */;
INSERT INTO `bimestre` VALUES (1,'2026',1,'2026-03-09','2026-05-08'),(2,'2026',2,'2026-05-18','2026-07-24'),(3,'2026',3,'2026-08-10','2026-10-09'),(4,'2026',4,'2026-10-19','2026-12-18');
/*!40000 ALTER TABLE `bimestre` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `carga_academica`
--

DROP TABLE IF EXISTS `carga_academica`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `carga_academica` (
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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `carga_academica`
--

LOCK TABLES `carga_academica` WRITE;
/*!40000 ALTER TABLE `carga_academica` DISABLE KEYS */;
INSERT INTO `carga_academica` VALUES (1,'2026',1,1,1),(2,'2026',1,2,2),(3,'2026',1,3,2),(4,'2026',2,1,1),(5,'2026',2,2,2),(6,'2026',2,3,2);
/*!40000 ALTER TABLE `carga_academica` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cierre_bimestre`
--

DROP TABLE IF EXISTS `cierre_bimestre`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cierre_bimestre` (
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cierre_bimestre`
--

LOCK TABLES `cierre_bimestre` WRITE;
/*!40000 ALTER TABLE `cierre_bimestre` DISABLE KEYS */;
INSERT INTO `cierre_bimestre` VALUES (1,4,1,2,'2026-10-29 00:32:04'),(2,4,2,2,'2026-10-29 00:32:04'),(3,5,1,3,'2026-10-29 00:32:04'),(4,5,2,3,'2026-10-29 00:32:04');
/*!40000 ALTER TABLE `cierre_bimestre` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cita_psicologia`
--

DROP TABLE IF EXISTS `cita_psicologia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cita_psicologia` (
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cita_psicologia`
--

LOCK TABLES `cita_psicologia` WRITE;
/*!40000 ALTER TABLE `cita_psicologia` DISABLE KEYS */;
INSERT INTO `cita_psicologia` VALUES (1,1,1,'Me cuesta concentrarme en clase','Mañanas','2026-10-01 10:00:00','ATENDIDA','Se recomienda organizar horarios de estudio. Seguimiento en un mes.',NULL,'2026-09-25 08:00:00'),(2,2,NULL,'Quiero conversar sobre problemas con mis compañeros','Martes o jueves',NULL,'PENDIENTE',NULL,NULL,'2026-10-29 00:32:04');
/*!40000 ALTER TABLE `cita_psicologia` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clase_virtual`
--

DROP TABLE IF EXISTS `clase_virtual`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clase_virtual` (
  `id_clase_virtual` int(11) NOT NULL AUTO_INCREMENT,
  `id_carga_academica` int(11) NOT NULL,
  `tema` varchar(150) DEFAULT NULL,
  `fecha` datetime NOT NULL,
  `enlace` varchar(500) NOT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_clase_virtual`),
  KEY `id_carga_academica` (`id_carga_academica`),
  CONSTRAINT `clase_virtual_ibfk_1` FOREIGN KEY (`id_carga_academica`) REFERENCES `carga_academica` (`id_carga_academica`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clase_virtual`
--

LOCK TABLES `clase_virtual` WRITE;
/*!40000 ALTER TABLE `clase_virtual` DISABLE KEYS */;
INSERT INTO `clase_virtual` VALUES (1,4,'Repaso para el examen bimestral','2026-10-20 16:00:00','https://meet.google.com/abc-defg-hij','2026-10-29 00:32:04');
/*!40000 ALTER TABLE `clase_virtual` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `conversacion`
--

DROP TABLE IF EXISTS `conversacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `conversacion` (
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `conversacion`
--

LOCK TABLES `conversacion` WRITE;
/*!40000 ALTER TABLE `conversacion` DISABLE KEYS */;
INSERT INTO `conversacion` VALUES (1,2,6,'Gracias, profesor. Ya me salió.','2026-10-04 19:10:00');
/*!40000 ALTER TABLE `conversacion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `curso`
--

DROP TABLE IF EXISTS `curso`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `curso` (
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `curso`
--

LOCK TABLES `curso` WRITE;
/*!40000 ALTER TABLE `curso` DISABLE KEYS */;
INSERT INTO `curso` VALUES (1,1,'Matemática',270,0,NULL,NULL),(2,2,'Comunicación',270,0,NULL,NULL),(3,3,'Ciencia y Tecnología',270,0,NULL,NULL);
/*!40000 ALTER TABLE `curso` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `curso_nota_automatica`
--

DROP TABLE IF EXISTS `curso_nota_automatica`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `curso_nota_automatica` (
  `id_curso` int(11) NOT NULL,
  `id_grado` int(11) NOT NULL,
  `valor` decimal(4,2) NOT NULL,
  PRIMARY KEY (`id_curso`,`id_grado`),
  KEY `id_grado` (`id_grado`),
  CONSTRAINT `curso_nota_automatica_ibfk_1` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id_curso`),
  CONSTRAINT `curso_nota_automatica_ibfk_2` FOREIGN KEY (`id_grado`) REFERENCES `grado` (`id_grado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `curso_nota_automatica`
--

LOCK TABLES `curso_nota_automatica` WRITE;
/*!40000 ALTER TABLE `curso_nota_automatica` DISABLE KEYS */;
/*!40000 ALTER TABLE `curso_nota_automatica` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dispositivo_push`
--

DROP TABLE IF EXISTS `dispositivo_push`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dispositivo_push` (
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dispositivo_push`
--

LOCK TABLES `dispositivo_push` WRITE;
/*!40000 ALTER TABLE `dispositivo_push` DISABLE KEYS */;
/*!40000 ALTER TABLE `dispositivo_push` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `docente`
--

DROP TABLE IF EXISTS `docente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `docente` (
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `docente`
--

LOCK TABLES `docente` WRITE;
/*!40000 ALTER TABLE `docente` DISABLE KEYS */;
INSERT INTO `docente` VALUES (1,2,'22222222','Carlos','Mendoza Paz','Matemática',NULL,'922222222','carlos@example.com',NULL,1),(2,3,'66666666','María','Salazar Vega','Comunicación',NULL,'966666666','maria@example.com',NULL,1);
/*!40000 ALTER TABLE `docente` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `entrega_tarea`
--

DROP TABLE IF EXISTS `entrega_tarea`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `entrega_tarea` (
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entrega_tarea`
--

LOCK TABLES `entrega_tarea` WRITE;
/*!40000 ALTER TABLE `entrega_tarea` DISABLE KEYS */;
INSERT INTO `entrega_tarea` VALUES (1,1,1,'https://drive.google.com/lucia-ecuaciones','Adjunto mis ejercicios.','2026-10-04 19:30:00',17.00,'Buen trabajo, revisa el ejercicio 8.'),(2,1,3,'https://drive.google.com/sofia-ecuaciones',NULL,'2026-10-06 10:15:00',NULL,NULL);
/*!40000 ALTER TABLE `entrega_tarea` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `familiar`
--

DROP TABLE IF EXISTS `familiar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `familiar` (
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `familiar`
--

LOCK TABLES `familiar` WRITE;
/*!40000 ALTER TABLE `familiar` DISABLE KEYS */;
INSERT INTO `familiar` VALUES (1,'55555555','Rosa','Quispe Flores','955555555','rosa.quispe@example.com','Av. Los Próceres 123, Lima');
/*!40000 ALTER TABLE `familiar` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grado`
--

DROP TABLE IF EXISTS `grado`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `grado` (
  `id_grado` int(11) NOT NULL AUTO_INCREMENT,
  `id_nivel` int(11) DEFAULT NULL,
  `nombre` varchar(20) NOT NULL,
  `orden` int(11) NOT NULL,
  PRIMARY KEY (`id_grado`),
  KEY `id_nivel` (`id_nivel`),
  CONSTRAINT `grado_ibfk_1` FOREIGN KEY (`id_nivel`) REFERENCES `nivel` (`id_nivel`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grado`
--

LOCK TABLES `grado` WRITE;
/*!40000 ALTER TABLE `grado` DISABLE KEYS */;
INSERT INTO `grado` VALUES (1,1,'1ro',1),(2,1,'2do',2),(3,1,'3ro',3),(4,1,'4to',4),(5,1,'5to',5),(6,1,'6to',6),(7,2,'1ro',7),(8,2,'2do',8),(9,2,'3ro',9),(10,2,'4to',10),(11,2,'5to',11);
/*!40000 ALTER TABLE `grado` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `horario_escolar`
--

DROP TABLE IF EXISTS `horario_escolar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `horario_escolar` (
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
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `horario_escolar`
--

LOCK TABLES `horario_escolar` WRITE;
/*!40000 ALTER TABLE `horario_escolar` DISABLE KEYS */;
INSERT INTO `horario_escolar` VALUES (1,5,1,'08:00:00','09:00:00'),(2,6,1,'09:00:00','10:00:00'),(3,4,1,'10:20:00','11:20:00'),(4,5,2,'08:00:00','09:00:00'),(5,6,2,'09:00:00','10:00:00'),(6,4,2,'10:20:00','11:20:00'),(7,5,3,'08:00:00','09:00:00'),(8,6,3,'09:00:00','10:00:00'),(9,4,3,'10:20:00','11:20:00'),(10,5,4,'08:00:00','09:00:00'),(11,6,4,'09:00:00','10:00:00'),(12,4,4,'10:20:00','11:20:00'),(13,5,5,'08:00:00','09:00:00'),(14,6,5,'09:00:00','10:00:00'),(15,4,5,'10:20:00','11:20:00'),(16,1,1,'08:00:00','09:00:00'),(17,2,1,'10:20:00','11:20:00'),(18,3,1,'11:20:00','12:20:00'),(19,1,2,'08:00:00','09:00:00'),(20,2,2,'10:20:00','11:20:00'),(21,3,2,'11:20:00','12:20:00'),(22,1,3,'08:00:00','09:00:00'),(23,2,3,'10:20:00','11:20:00'),(24,3,3,'11:20:00','12:20:00'),(25,1,4,'08:00:00','09:00:00'),(26,2,4,'10:20:00','11:20:00'),(27,3,4,'11:20:00','12:20:00'),(28,1,5,'08:00:00','09:00:00'),(29,2,5,'10:20:00','11:20:00'),(30,3,5,'11:20:00','12:20:00');
/*!40000 ALTER TABLE `horario_escolar` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `material_clase`
--

DROP TABLE IF EXISTS `material_clase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `material_clase` (
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `material_clase`
--

LOCK TABLES `material_clase` WRITE;
/*!40000 ALTER TABLE `material_clase` DISABLE KEYS */;
INSERT INTO `material_clase` VALUES (1,4,'Ecuaciones de primer grado','Teoría y 10 ejercicios resueltos.','https://example.com/ecuaciones.pdf',1,'2026-10-29 00:32:04'),(2,4,'Sistemas de ecuaciones','Video explicativo del método de sustitución.','https://example.com/sistemas',2,'2026-10-29 00:32:04');
/*!40000 ALTER TABLE `material_clase` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `matricula`
--

DROP TABLE IF EXISTS `matricula`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `matricula` (
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
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `matricula`
--

LOCK TABLES `matricula` WRITE;
/*!40000 ALTER TABLE `matricula` DISABLE KEYS */;
INSERT INTO `matricula` VALUES (1,'2026',1,2,9,'2026-10-29 00:32:04','MATRICULADO','REGULAR','NORMAL'),(2,'2026',2,1,7,'2026-10-29 00:32:04','MATRICULADO','REGULAR','NORMAL'),(3,'2026',3,2,9,'2026-10-29 00:32:04','MATRICULADO','REGULAR','NORMAL'),(4,'2026',4,2,9,'2026-10-29 00:32:04','MATRICULADO','REGULAR','NORMAL'),(5,'2026',5,2,9,'2026-10-29 00:32:04','MATRICULADO','REGULAR','NORMAL'),(6,'2026',6,2,9,'2026-10-29 00:32:04','MATRICULADO','REGULAR','NORMAL'),(7,'2026',7,2,9,'2026-10-29 00:32:04','MATRICULADO','REGULAR','NORMAL'),(8,'2026',8,2,9,'2026-10-29 00:32:04','MATRICULADO','REGULAR','NORMAL'),(9,'2026',9,2,9,'2026-10-29 00:32:04','MATRICULADO','REGULAR','NORMAL');
/*!40000 ALTER TABLE `matricula` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mensaje`
--

DROP TABLE IF EXISTS `mensaje`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mensaje` (
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mensaje`
--

LOCK TABLES `mensaje` WRITE;
/*!40000 ALTER TABLE `mensaje` DISABLE KEYS */;
INSERT INTO `mensaje` VALUES (1,1,6,'Profesor, ¿el ejercicio 8 de la tarea se resuelve por sustitución?',1,'2026-10-04 18:05:00'),(2,1,2,'Sí, Lucía. Despeja x en la primera ecuación y reemplázala en la segunda.',1,'2026-10-04 18:40:00'),(3,1,6,'Gracias, profesor. Ya me salió.',0,'2026-10-04 19:10:00');
/*!40000 ALTER TABLE `mensaje` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `nivel`
--

DROP TABLE IF EXISTS `nivel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nivel` (
  `id_nivel` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(20) NOT NULL,
  PRIMARY KEY (`id_nivel`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nivel`
--

LOCK TABLES `nivel` WRITE;
/*!40000 ALTER TABLE `nivel` DISABLE KEYS */;
INSERT INTO `nivel` VALUES (1,'Primaria'),(2,'Secundaria');
/*!40000 ALTER TABLE `nivel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `nivel_conducta`
--

DROP TABLE IF EXISTS `nivel_conducta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nivel_conducta` (
  `id_nivel_conducta` int(11) NOT NULL AUTO_INCREMENT,
  `id_tipo_falta` int(11) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `puntos` int(11) NOT NULL,
  `descripcion` text DEFAULT NULL,
  PRIMARY KEY (`id_nivel_conducta`),
  KEY `id_tipo_falta` (`id_tipo_falta`),
  CONSTRAINT `nivel_conducta_ibfk_1` FOREIGN KEY (`id_tipo_falta`) REFERENCES `tipo_falta` (`id_tipo_falta`),
  CONSTRAINT `chk_nivel_puntos` CHECK (`puntos` > 0)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nivel_conducta`
--

LOCK TABLES `nivel_conducta` WRITE;
/*!40000 ALTER TABLE `nivel_conducta` DISABLE KEYS */;
INSERT INTO `nivel_conducta` VALUES (1,1,'Tardanza injustificada',1,NULL),(2,1,'No portar el uniforme completo',2,NULL),(3,2,'Uso del celular en clase',3,NULL),(4,2,'Falta de respeto a un compañero',5,NULL),(5,3,'Agresión física',10,NULL);
/*!40000 ALTER TABLE `nivel_conducta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `nota`
--

DROP TABLE IF EXISTS `nota`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nota` (
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
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nota`
--

LOCK TABLES `nota` WRITE;
/*!40000 ALTER TABLE `nota` DISABLE KEYS */;
INSERT INTO `nota` VALUES (1,1,1,1,'Práctica 1',15.00,'2026-10-29 00:32:04'),(2,3,1,1,'Práctica 1',12.00,'2026-10-29 00:32:04'),(3,4,1,1,'Práctica 1',9.00,'2026-10-29 00:32:04'),(4,5,1,1,'Práctica 1',17.00,'2026-10-29 00:32:04'),(5,6,1,1,'Práctica 1',11.00,'2026-10-29 00:32:04'),(6,7,1,1,'Práctica 1',14.00,'2026-10-29 00:32:04'),(7,8,1,1,'Práctica 1',8.00,'2026-10-29 00:32:04'),(8,9,1,1,'Práctica 1',13.00,'2026-10-29 00:32:04'),(9,1,1,1,'Examen',16.00,'2026-10-29 00:32:04'),(10,3,1,1,'Examen',13.00,'2026-10-29 00:32:04'),(11,4,1,1,'Examen',10.00,'2026-10-29 00:32:04'),(12,5,1,1,'Examen',18.00,'2026-10-29 00:32:04'),(13,6,1,1,'Examen',12.00,'2026-10-29 00:32:04'),(14,7,1,1,'Examen',15.00,'2026-10-29 00:32:04'),(15,8,1,1,'Examen',9.00,'2026-10-29 00:32:04'),(16,9,1,1,'Examen',14.00,'2026-10-29 00:32:04'),(17,1,1,2,'Práctica 1',16.00,'2026-10-29 00:32:04'),(18,3,1,2,'Práctica 1',13.00,'2026-10-29 00:32:04'),(19,4,1,2,'Práctica 1',10.00,'2026-10-29 00:32:04'),(20,5,1,2,'Práctica 1',18.00,'2026-10-29 00:32:04'),(21,6,1,2,'Práctica 1',12.00,'2026-10-29 00:32:04'),(22,7,1,2,'Práctica 1',15.00,'2026-10-29 00:32:04'),(23,8,1,2,'Práctica 1',9.00,'2026-10-29 00:32:04'),(24,9,1,2,'Práctica 1',14.00,'2026-10-29 00:32:04'),(25,1,1,2,'Examen',17.00,'2026-10-29 00:32:04'),(26,3,1,2,'Examen',14.00,'2026-10-29 00:32:04'),(27,4,1,2,'Examen',11.00,'2026-10-29 00:32:04'),(28,5,1,2,'Examen',19.00,'2026-10-29 00:32:04'),(29,6,1,2,'Examen',13.00,'2026-10-29 00:32:04'),(30,7,1,2,'Examen',16.00,'2026-10-29 00:32:04'),(31,8,1,2,'Examen',10.00,'2026-10-29 00:32:04'),(32,9,1,2,'Examen',15.00,'2026-10-29 00:32:04'),(33,1,1,3,'Práctica 1',17.00,'2026-10-29 00:32:04'),(34,3,1,3,'Práctica 1',14.00,'2026-10-29 00:32:04'),(35,4,1,3,'Práctica 1',11.00,'2026-10-29 00:32:04'),(36,5,1,3,'Práctica 1',19.00,'2026-10-29 00:32:04'),(37,6,1,3,'Práctica 1',13.00,'2026-10-29 00:32:04'),(38,7,1,3,'Práctica 1',16.00,'2026-10-29 00:32:04'),(39,8,1,3,'Práctica 1',10.00,'2026-10-29 00:32:04'),(40,9,1,3,'Práctica 1',15.00,'2026-10-29 00:32:04'),(41,1,1,3,'Examen',18.00,'2026-10-29 00:32:04'),(42,3,1,3,'Examen',15.00,'2026-10-29 00:32:04'),(43,4,1,3,'Examen',12.00,'2026-10-29 00:32:04'),(44,5,1,3,'Examen',20.00,'2026-10-29 00:32:04'),(45,6,1,3,'Examen',14.00,'2026-10-29 00:32:04'),(46,7,1,3,'Examen',17.00,'2026-10-29 00:32:04'),(47,8,1,3,'Examen',11.00,'2026-10-29 00:32:04'),(48,9,1,3,'Examen',16.00,'2026-10-29 00:32:04'),(49,1,2,1,'Práctica 1',14.00,'2026-10-29 00:32:04'),(50,3,2,1,'Práctica 1',11.00,'2026-10-29 00:32:04'),(51,4,2,1,'Práctica 1',8.00,'2026-10-29 00:32:04'),(52,5,2,1,'Práctica 1',16.00,'2026-10-29 00:32:04'),(53,6,2,1,'Práctica 1',10.00,'2026-10-29 00:32:04'),(54,7,2,1,'Práctica 1',13.00,'2026-10-29 00:32:04'),(55,8,2,1,'Práctica 1',7.00,'2026-10-29 00:32:04'),(56,9,2,1,'Práctica 1',12.00,'2026-10-29 00:32:04'),(57,1,2,1,'Examen',15.00,'2026-10-29 00:32:04'),(58,3,2,1,'Examen',12.00,'2026-10-29 00:32:04'),(59,4,2,1,'Examen',9.00,'2026-10-29 00:32:04'),(60,5,2,1,'Examen',17.00,'2026-10-29 00:32:04'),(61,6,2,1,'Examen',11.00,'2026-10-29 00:32:04'),(62,7,2,1,'Examen',14.00,'2026-10-29 00:32:04'),(63,8,2,1,'Examen',8.00,'2026-10-29 00:32:04'),(64,9,2,1,'Examen',13.00,'2026-10-29 00:32:04'),(65,1,2,2,'Práctica 1',15.00,'2026-10-29 00:32:04'),(66,3,2,2,'Práctica 1',12.00,'2026-10-29 00:32:04'),(67,4,2,2,'Práctica 1',9.00,'2026-10-29 00:32:04'),(68,5,2,2,'Práctica 1',17.00,'2026-10-29 00:32:04'),(69,6,2,2,'Práctica 1',11.00,'2026-10-29 00:32:04'),(70,7,2,2,'Práctica 1',14.00,'2026-10-29 00:32:04'),(71,8,2,2,'Práctica 1',8.00,'2026-10-29 00:32:04'),(72,9,2,2,'Práctica 1',13.00,'2026-10-29 00:32:04'),(73,1,2,2,'Examen',16.00,'2026-10-29 00:32:04'),(74,3,2,2,'Examen',13.00,'2026-10-29 00:32:04'),(75,4,2,2,'Examen',10.00,'2026-10-29 00:32:04'),(76,5,2,2,'Examen',18.00,'2026-10-29 00:32:04'),(77,6,2,2,'Examen',12.00,'2026-10-29 00:32:04'),(78,7,2,2,'Examen',15.00,'2026-10-29 00:32:04'),(79,8,2,2,'Examen',9.00,'2026-10-29 00:32:04'),(80,9,2,2,'Examen',14.00,'2026-10-29 00:32:04'),(81,1,2,3,'Práctica 1',16.00,'2026-10-29 00:32:04'),(82,3,2,3,'Práctica 1',13.00,'2026-10-29 00:32:04'),(83,4,2,3,'Práctica 1',10.00,'2026-10-29 00:32:04'),(84,5,2,3,'Práctica 1',18.00,'2026-10-29 00:32:04'),(85,6,2,3,'Práctica 1',12.00,'2026-10-29 00:32:04'),(86,7,2,3,'Práctica 1',15.00,'2026-10-29 00:32:04'),(87,8,2,3,'Práctica 1',9.00,'2026-10-29 00:32:04'),(88,9,2,3,'Práctica 1',14.00,'2026-10-29 00:32:04'),(89,1,2,3,'Examen',17.00,'2026-10-29 00:32:04'),(90,3,2,3,'Examen',14.00,'2026-10-29 00:32:04'),(91,4,2,3,'Examen',11.00,'2026-10-29 00:32:04'),(92,5,2,3,'Examen',19.00,'2026-10-29 00:32:04'),(93,6,2,3,'Examen',13.00,'2026-10-29 00:32:04'),(94,7,2,3,'Examen',16.00,'2026-10-29 00:32:04'),(95,8,2,3,'Examen',10.00,'2026-10-29 00:32:04'),(96,9,2,3,'Examen',15.00,'2026-10-29 00:32:04');
/*!40000 ALTER TABLE `nota` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notificacion`
--

DROP TABLE IF EXISTS `notificacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notificacion` (
  `id_notificacion` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `tipo` varchar(30) NOT NULL,
  `titulo` varchar(150) NOT NULL,
  `mensaje` varchar(300) NOT NULL,
  `id_referencia` int(11) DEFAULT NULL,
  `leida` tinyint(1) NOT NULL DEFAULT 0,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_notificacion`),
  KEY `ix_notificacion_usuario_leida` (`id_usuario`,`leida`),
  CONSTRAINT `notificacion_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notificacion`
--

LOCK TABLES `notificacion` WRITE;
/*!40000 ALTER TABLE `notificacion` DISABLE KEYS */;
INSERT INTO `notificacion` VALUES (1,6,'CONDUCTA','Nuevo reporte de conducta','No portar el uniforme completo (−2 puntos)',2,1,'2026-10-02 08:00:00'),(2,6,'CALIFICACION','Tu tarea fue calificada','Ejercicios de ecuaciones: 17',1,1,'2026-10-06 09:00:00'),(3,2,'MENSAJE','Mensaje de Lucía Quispe Flores','Gracias, profesor. Ya me salió.',1,0,'2026-10-04 19:10:00'),(4,6,'TAREA','Nueva tarea de Matemática','Proyecto: sistemas de ecuaciones · entrega hasta el 20/11 23:59',2,0,'2026-10-13 08:00:00'),(5,8,'TAREA','Nueva tarea de Matemática','Proyecto: sistemas de ecuaciones · entrega hasta el 20/11 23:59',2,0,'2026-10-13 08:00:00'),(6,9,'TAREA','Nueva tarea de Matemática','Proyecto: sistemas de ecuaciones · entrega hasta el 20/11 23:59',2,0,'2026-10-13 08:00:00'),(7,10,'TAREA','Nueva tarea de Matemática','Proyecto: sistemas de ecuaciones · entrega hasta el 20/11 23:59',2,0,'2026-10-13 08:00:00'),(8,11,'TAREA','Nueva tarea de Matemática','Proyecto: sistemas de ecuaciones · entrega hasta el 20/11 23:59',2,0,'2026-10-13 08:00:00'),(9,12,'TAREA','Nueva tarea de Matemática','Proyecto: sistemas de ecuaciones · entrega hasta el 20/11 23:59',2,0,'2026-10-13 08:00:00'),(10,13,'TAREA','Nueva tarea de Matemática','Proyecto: sistemas de ecuaciones · entrega hasta el 20/11 23:59',2,0,'2026-10-13 08:00:00'),(11,14,'TAREA','Nueva tarea de Matemática','Proyecto: sistemas de ecuaciones · entrega hasta el 20/11 23:59',2,0,'2026-10-13 08:00:00');
/*!40000 ALTER TABLE `notificacion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operacion_offline`
--

DROP TABLE IF EXISTS `operacion_offline`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `operacion_offline` (
  `id_operacion` varchar(64) NOT NULL,
  `id_usuario` int(11) NOT NULL,
  `metodo` varchar(10) NOT NULL,
  `ruta` varchar(255) NOT NULL,
  `codigo` smallint(6) NOT NULL,
  `respuesta` longtext NOT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_operacion`),
  KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `operacion_offline_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operacion_offline`
--

LOCK TABLES `operacion_offline` WRITE;
/*!40000 ALTER TABLE `operacion_offline` DISABLE KEYS */;
INSERT INTO `operacion_offline` VALUES ('demo-offline-sofia-0001',8,'POST','/tareas/item/1/entregar',201,'{\"fuera_de_plazo\":true,\"message\":\"Tarea entregada\"}','2026-10-06 10:15:05');
/*!40000 ALTER TABLE `operacion_offline` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `plan_estudio`
--

DROP TABLE IF EXISTS `plan_estudio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `plan_estudio` (
  `id_plan_estudio` int(11) NOT NULL AUTO_INCREMENT,
  `id_curso` int(11) DEFAULT NULL,
  `id_grado` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_plan_estudio`),
  KEY `id_curso` (`id_curso`),
  KEY `id_grado` (`id_grado`),
  CONSTRAINT `plan_estudio_ibfk_1` FOREIGN KEY (`id_curso`) REFERENCES `curso` (`id_curso`),
  CONSTRAINT `plan_estudio_ibfk_2` FOREIGN KEY (`id_grado`) REFERENCES `grado` (`id_grado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `plan_estudio`
--

LOCK TABLES `plan_estudio` WRITE;
/*!40000 ALTER TABLE `plan_estudio` DISABLE KEYS */;
/*!40000 ALTER TABLE `plan_estudio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `psicologo`
--

DROP TABLE IF EXISTS `psicologo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `psicologo` (
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `psicologo`
--

LOCK TABLES `psicologo` WRITE;
/*!40000 ALTER TABLE `psicologo` DISABLE KEYS */;
INSERT INTO `psicologo` VALUES (1,5,'88888888','Elena','Castro Rivas','988888888','elena@example.com');
/*!40000 ALTER TABLE `psicologo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `receso_horario`
--

DROP TABLE IF EXISTS `receso_horario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `receso_horario` (
  `id_receso` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(40) NOT NULL DEFAULT 'Recreo',
  `hora_inicio` time NOT NULL,
  `hora_fin` time NOT NULL,
  PRIMARY KEY (`id_receso`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `receso_horario`
--

LOCK TABLES `receso_horario` WRITE;
/*!40000 ALTER TABLE `receso_horario` DISABLE KEYS */;
INSERT INTO `receso_horario` VALUES (1,'Recreo','10:00:00','10:20:00');
/*!40000 ALTER TABLE `receso_horario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reporte_conducta`
--

DROP TABLE IF EXISTS `reporte_conducta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reporte_conducta` (
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reporte_conducta`
--

LOCK TABLES `reporte_conducta` WRITE;
/*!40000 ALTER TABLE `reporte_conducta` DISABLE KEYS */;
INSERT INTO `reporte_conducta` VALUES (1,1,3,4,'2026-09-15 10:20:00','Usaba el celular durante el examen de Matemática.','https://example.com/evidencia-celular.jpg','REGISTRADO',NULL,NULL,NULL),(2,1,2,4,'2026-10-02 07:50:00','Llegó sin la corbata del uniforme.',NULL,'REGISTRADO',NULL,NULL,NULL);
/*!40000 ALTER TABLE `reporte_conducta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resumen_nota`
--

DROP TABLE IF EXISTS `resumen_nota`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `resumen_nota` (
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
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `resumen_nota`
--

LOCK TABLES `resumen_nota` WRITE;
/*!40000 ALTER TABLE `resumen_nota` DISABLE KEYS */;
INSERT INTO `resumen_nota` VALUES (1,4,1,9.50,10.50,NULL,NULL,10.00,'EN CURSO'),(2,9,1,13.50,14.50,NULL,NULL,14.00,'EN CURSO'),(3,5,1,17.50,18.50,NULL,NULL,18.00,'EN CURSO'),(4,6,1,11.50,12.50,NULL,NULL,12.00,'EN CURSO'),(5,1,1,15.50,16.50,NULL,NULL,16.00,'EN CURSO'),(6,3,1,12.50,13.50,NULL,NULL,13.00,'EN CURSO'),(7,7,1,14.50,15.50,NULL,NULL,15.00,'EN CURSO'),(8,8,1,8.50,9.50,NULL,NULL,9.00,'EN CURSO'),(17,4,2,8.50,9.50,NULL,NULL,9.00,'EN CURSO'),(18,9,2,12.50,13.50,NULL,NULL,13.00,'EN CURSO'),(19,5,2,16.50,17.50,NULL,NULL,17.00,'EN CURSO'),(20,6,2,10.50,11.50,NULL,NULL,11.00,'EN CURSO'),(21,1,2,14.50,15.50,NULL,NULL,15.00,'EN CURSO'),(22,3,2,11.50,12.50,NULL,NULL,12.00,'EN CURSO'),(23,7,2,13.50,14.50,NULL,NULL,14.00,'EN CURSO'),(24,8,2,7.50,8.50,NULL,NULL,8.00,'EN CURSO');
/*!40000 ALTER TABLE `resumen_nota` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seccion`
--

DROP TABLE IF EXISTS `seccion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `seccion` (
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seccion`
--

LOCK TABLES `seccion` WRITE;
/*!40000 ALTER TABLE `seccion` DISABLE KEYS */;
INSERT INTO `seccion` VALUES (1,7,'2026','A',30),(2,9,'2026','A',30),(3,9,'2026','B',30);
/*!40000 ALTER TABLE `seccion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `solicitud_matricula`
--

DROP TABLE IF EXISTS `solicitud_matricula`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `solicitud_matricula` (
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `solicitud_matricula`
--

LOCK TABLES `solicitud_matricula` WRITE;
/*!40000 ALTER TABLE `solicitud_matricula` DISABLE KEYS */;
/*!40000 ALTER TABLE `solicitud_matricula` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tarea`
--

DROP TABLE IF EXISTS `tarea`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tarea` (
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tarea`
--

LOCK TABLES `tarea` WRITE;
/*!40000 ALTER TABLE `tarea` DISABLE KEYS */;
INSERT INTO `tarea` VALUES (1,4,'Ejercicios de ecuaciones','Resolver los 10 ejercicios de la página 45.','2026-09-28 08:00:00','2026-10-05 23:59:00','https://example.com/ejercicios-ecuaciones.pdf','ACTIVO','TAREA',3,0),(2,4,'Proyecto: sistemas de ecuaciones','Video de 3 minutos explicando un problema real.','2026-10-29 00:32:04','2026-11-20 23:59:00',NULL,'ACTIVO','TAREA',4,0);
/*!40000 ALTER TABLE `tarea` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tipo_falta`
--

DROP TABLE IF EXISTS `tipo_falta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tipo_falta` (
  `id_tipo_falta` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(60) NOT NULL,
  PRIMARY KEY (`id_tipo_falta`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tipo_falta`
--

LOCK TABLES `tipo_falta` WRITE;
/*!40000 ALTER TABLE `tipo_falta` DISABLE KEYS */;
INSERT INTO `tipo_falta` VALUES (2,'Grave'),(1,'Leve'),(3,'Muy grave');
/*!40000 ALTER TABLE `tipo_falta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `usuario` (
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
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario`
--

LOCK TABLES `usuario` WRITE;
/*!40000 ALTER TABLE `usuario` DISABLE KEYS */;
INSERT INTO `usuario` VALUES (1,'ADM-11111111','$2b$12$cC8t1YmaFnn30Xk.uYg.Mu47EsKaSqiWjUiTyyzxPcVAUR0den41S','ADMIN',1,0,'2026-10-29 00:32:02'),(2,'DOC-22222222','$2b$12$SmOJFDxnPqob75DYjPZStOjn3DJ.Rwzsdtj.re5NeCORjPcimzVxK','DOCENTE',1,0,'2026-10-29 00:32:02'),(3,'DOC-66666666','$2b$12$nJxuHO5ScnSwTC3ZfkxT6uBoXzo39AZ7BB668CGIdfoxtSCAR90gS','DOCENTE',1,0,'2026-10-29 00:32:02'),(4,'AUX-77777777','$2b$12$jnAoMuiAIlv.wcyuVuuKauiBo9GD0pUxXFQVW42Q5NqRwridmohk6','AUXILIAR',1,0,'2026-10-29 00:32:02'),(5,'PSI-88888888','$2b$12$vrMm1cmdkZQKhifohzhCaOr.TtzTM6UMPnQAng6PHLreL8yZHy4O2','PSICOLOGO',1,0,'2026-10-29 00:32:02'),(6,'ALU-33333333','$2b$12$hUNPkC7VEUPhvJ2TTL226OY/uLennmwCuX.xrtV1x2UVrKvDbyRTy','ALUMNO',1,0,'2026-10-29 00:32:03'),(7,'ALU-44444444','$2b$12$GvNrk.IUaHfE54jq04/uf.VeLSh3G6k.Ztzo18Zlpc/qqA1iaoJCW','ALUMNO',1,1,'2026-10-29 00:32:03'),(8,'ALU-71111111','$2b$12$CVYaENL8Vr810qRoCTbPgep1EamiwvdAtZXajmuk.uy4ZuX5pDwK6','ALUMNO',1,0,'2026-10-29 00:32:03'),(9,'ALU-72222222','$2b$12$fOZzlC0sKhZKsdUs.W2lnuRKkZOtatkYxdc1gFcg206TjHKcE44mK','ALUMNO',1,0,'2026-10-29 00:32:03'),(10,'ALU-73333333','$2b$12$TrBeAEqW6w6XjauJJuHMe.puXCXOWgWWyLlawsZ7GauVheJRJAqEW','ALUMNO',1,0,'2026-10-29 00:32:03'),(11,'ALU-74444444','$2b$12$EGT50M8TVjNrJpUh/5ei8.POFli/KR9/KQStzao9Q/qp1hFU92CBq','ALUMNO',1,0,'2026-10-29 00:32:03'),(12,'ALU-75555555','$2b$12$0jM94Wp1RDob1lSs8oon6egqsZZA1b6kUxtoX4Dc/CylqbI4BpMOC','ALUMNO',1,0,'2026-10-29 00:32:04'),(13,'ALU-76666666','$2b$12$r2vI0Lt.2MPyXg1h/0BMr.kglPNp7Zj9KlC1fluddupMR3EKgZLKq','ALUMNO',1,0,'2026-10-29 00:32:04'),(14,'ALU-79999999','$2b$12$Q/qRsNvidyxUYRkETBa1Z.UuCFOqJcXyzyP9YYX9G.kdpQgwHrBK6','ALUMNO',1,0,'2026-10-29 00:32:04');
/*!40000 ALTER TABLE `usuario` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed
