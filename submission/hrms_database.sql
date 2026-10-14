-- MySQL dump 10.13  Distrib 9.6.0, for macos15 (arm64)
--
-- Host: localhost    Database: hrms_db
-- ------------------------------------------------------
-- Server version	9.6.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `attendance`
--

DROP TABLE IF EXISTS `attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `attendance_date` date NOT NULL,
  `check_in` datetime DEFAULT NULL,
  `check_out` datetime DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_employee_attendance_date` (`employee_id`,`attendance_date`),
  KEY `ix_attendance_id` (`id`),
  KEY `ix_attendance_employee_id` (`employee_id`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attendance`
--

LOCK TABLES `attendance` WRITE;
/*!40000 ALTER TABLE `attendance` DISABLE KEYS */;
INSERT INTO `attendance` VALUES (1,1,'2026-10-13','2026-10-13 11:02:38','2026-10-13 11:03:36','present','2026-10-13 11:02:38');
/*!40000 ALTER TABLE `attendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_logs`
--

DROP TABLE IF EXISTS `audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `action` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `entity_type` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `entity_id` int DEFAULT NULL,
  `details` json DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `ix_audit_logs_id` (`id`),
  CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
INSERT INTO `audit_logs` VALUES (1,NULL,'audit.self_test','system',NULL,'{\"test\": true}','2026-10-13 16:47:18'),(2,NULL,'audit.transaction_test','system',NULL,'{\"purpose\": \"verify_commit\"}','2026-10-13 16:59:33'),(3,2,'employee.updated','employee',4,'{\"changed_fields\": [\"department\", \"designation\", \"full_name\", \"joining_date\", \"salary\"]}','2026-10-13 17:09:56'),(4,2,'leave.approved','leave',8,'{\"end_date\": \"2026-10-14\", \"leave_type\": \"casual\", \"start_date\": \"2026-10-14\", \"employee_id\": 4}','2026-10-14 11:25:29');
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `employee_documents`
--

DROP TABLE IF EXISTS `employee_documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employee_documents` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `uploaded_by_user_id` int NOT NULL,
  `original_filename` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stored_filename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `size_bytes` int NOT NULL,
  `uploaded_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `stored_filename` (`stored_filename`),
  KEY `uploaded_by_user_id` (`uploaded_by_user_id`),
  KEY `ix_employee_documents_employee_id` (`employee_id`),
  KEY `ix_employee_documents_id` (`id`),
  CONSTRAINT `employee_documents_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`),
  CONSTRAINT `employee_documents_ibfk_2` FOREIGN KEY (`uploaded_by_user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employee_documents`
--

LOCK TABLES `employee_documents` WRITE;
/*!40000 ALTER TABLE `employee_documents` DISABLE KEYS */;
INSERT INTO `employee_documents` VALUES (1,1,2,'monthly_statement_2026_10 (2).pdf','b94b93af23c64e04a6a4abc83d718e59.pdf','application/pdf',2778,'2026-10-13 14:04:39');
/*!40000 ALTER TABLE `employee_documents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `employees`
--

DROP TABLE IF EXISTS `employees`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employees` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `employee_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `department` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `designation` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `joining_date` date NOT NULL,
  `salary` decimal(12,2) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `employee_code` (`employee_code`),
  KEY `ix_employees_id` (`id`),
  CONSTRAINT `employees_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employees`
--

LOCK TABLES `employees` WRITE;
/*!40000 ALTER TABLE `employees` DISABLE KEYS */;
INSERT INTO `employees` VALUES (1,3,'employee1','dep1','dev','2026-10-13',1000.00,'2026-10-13 10:52:48'),(2,4,'Emp 2','department 2','dev','2026-10-13',2000.00,'2026-10-13 13:12:03'),(3,5,'emp3','Eng','Testing','2026-10-13',2500.00,'2026-10-13 13:32:38'),(4,1,'testuser01','eg','eg','2026-10-13',0.00,'2026-10-13 14:49:35');
/*!40000 ALTER TABLE `employees` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leave_balances`
--

DROP TABLE IF EXISTS `leave_balances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_balances` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `leave_type` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `allocated_days` decimal(7,2) NOT NULL,
  `used_days` decimal(7,2) NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_leave_balance_employee_type` (`employee_id`,`leave_type`),
  KEY `ix_leave_balances_id` (`id`),
  KEY `ix_leave_balances_employee_id` (`employee_id`),
  CONSTRAINT `leave_balances_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leave_balances`
--

LOCK TABLES `leave_balances` WRITE;
/*!40000 ALTER TABLE `leave_balances` DISABLE KEYS */;
INSERT INTO `leave_balances` VALUES (1,1,'sick',4.00,0.00,'2026-10-13 14:10:19'),(2,1,'casual',12.00,1.00,'2026-10-13 14:21:26');
/*!40000 ALTER TABLE `leave_balances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leave_ledger`
--

DROP TABLE IF EXISTS `leave_ledger`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_ledger` (
  `id` int NOT NULL AUTO_INCREMENT,
  `leave_id` int NOT NULL,
  `paid_days` decimal(7,2) NOT NULL,
  `lop_days` decimal(7,2) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `leave_id` (`leave_id`),
  KEY `ix_leave_ledger_id` (`id`),
  CONSTRAINT `leave_ledger_ibfk_1` FOREIGN KEY (`leave_id`) REFERENCES `leaves` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leave_ledger`
--

LOCK TABLES `leave_ledger` WRITE;
/*!40000 ALTER TABLE `leave_ledger` DISABLE KEYS */;
INSERT INTO `leave_ledger` VALUES (1,1,1.00,0.00,'2026-10-13 14:18:17'),(2,3,0.00,1.00,'2026-10-13 14:24:54'),(3,4,0.00,1.00,'2026-10-13 14:51:54'),(4,5,0.00,1.00,'2026-10-13 14:57:24'),(5,6,0.00,1.00,'2026-10-13 15:00:40'),(6,7,0.00,1.00,'2026-10-13 16:11:54'),(7,8,0.00,1.00,'2026-10-14 11:25:29');
/*!40000 ALTER TABLE `leave_ledger` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leaves`
--

DROP TABLE IF EXISTS `leaves`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leaves` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `leave_type` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reason` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reviewed_by` int DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `reviewed_by` (`reviewed_by`),
  KEY `ix_leaves_employee_id` (`employee_id`),
  KEY `ix_leaves_id` (`id`),
  CONSTRAINT `leaves_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`),
  CONSTRAINT `leaves_ibfk_2` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leaves`
--

LOCK TABLES `leaves` WRITE;
/*!40000 ALTER TABLE `leaves` DISABLE KEYS */;
INSERT INTO `leaves` VALUES (1,1,'2026-10-13','2026-10-13','casual','personal','approved',2,'2026-10-13 11:18:18','2026-10-13 11:16:05'),(2,1,'2026-10-20','2026-10-20','sick','Medical appointment','rejected',2,'2026-10-13 11:20:12','2026-10-13 11:20:03'),(3,2,'2026-10-20','2026-10-20','sick','LOP calculation test','approved',2,'2026-10-13 14:24:55','2026-10-13 14:24:19'),(4,4,'2026-10-13','2026-10-13','casual','string','approved',2,'2026-10-13 14:51:54','2026-10-13 14:50:21'),(5,4,'2026-10-13','2026-10-13','casual','string','approved',2,'2026-10-13 14:57:24','2026-10-13 14:56:48'),(6,4,'2026-10-13','2026-10-13','casual','string','approved',2,'2026-10-13 15:00:40','2026-10-13 15:00:12'),(7,4,'2026-10-13','2026-10-13','casual','string','approved',2,'2026-10-13 16:11:55','2026-10-13 16:11:23'),(8,4,'2026-10-14','2026-10-14','casual','string','approved',2,'2026-10-14 11:25:29','2026-10-14 11:17:07');
/*!40000 ALTER TABLE `leaves` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payroll`
--

DROP TABLE IF EXISTS `payroll`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payroll` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `pay_period` date NOT NULL,
  `basic_salary` decimal(12,2) NOT NULL,
  `allowances` decimal(12,2) NOT NULL,
  `deductions` decimal(12,2) NOT NULL,
  `net_salary` decimal(12,2) NOT NULL,
  `created_by` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `is_locked` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_employee_pay_period` (`employee_id`,`pay_period`),
  KEY `created_by` (`created_by`),
  KEY `ix_payroll_employee_id` (`employee_id`),
  KEY `ix_payroll_id` (`id`),
  CONSTRAINT `payroll_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`),
  CONSTRAINT `payroll_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payroll`
--

LOCK TABLES `payroll` WRITE;
/*!40000 ALTER TABLE `payroll` DISABLE KEYS */;
INSERT INTO `payroll` VALUES (1,1,'2026-10-01',25000.00,3000.00,1500.00,26500.00,2,'2026-10-13 12:04:45',0),(2,2,'2026-10-01',2000.00,0.00,64.52,1935.48,2,'2026-10-13 14:26:36',1);
/*!40000 ALTER TABLE `payroll` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `hashed_password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` enum('admin','hr','employee') COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`),
  KEY `ix_users_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'amp eg','testuser@gmail.com','$argon2id$v=19$m=65536,t=3,p=4$l1RrC+nZNHgnhHIN28qLKQ$+KxUVLaQkcVdGs0eW9URxvP4joQSmjhZx4bCC6+MglU','employee',1,'2026-10-13 10:31:14'),(2,'admin','admin@gmail.com','$argon2id$v=19$m=65536,t=3,p=4$Mhqxu2ddw7vDn3hkRvKrwA$cQ/Mx9Cxybt7KvtjEr2t32+dQOgASZ8d0L9pZOCJ8UA','admin',1,'2026-10-13 10:42:21'),(3,'Employee 1','employee1@gmail.com','$argon2id$v=19$m=65536,t=3,p=4$aVvXs8McS73wzR0IsnDQaQ$AVWjzrx7/FygsfshrOXgJVaWvhilSpPBvxH0Fnw+WY0','employee',1,'2026-10-13 10:52:48'),(4,'Employee 2','employee2@gmail.com','$argon2id$v=19$m=65536,t=3,p=4$mHy/rPWgHoiEZdwq24D6Ow$rPuh5xUKaPsBDlbcDjhdW6U8HW1zq3lngAVIhu9OwjI','employee',1,'2026-10-13 13:12:03'),(5,'Employee 3','emp3@gmail.com','$argon2id$v=19$m=65536,t=3,p=4$qjFta0sEFGWE0cTV89qtIA$ss94hwNyvj2M/JpKdOh57p7bJFojRT/H0gYqDBav1qk','employee',1,'2026-10-13 13:32:38');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-14 11:31:05
