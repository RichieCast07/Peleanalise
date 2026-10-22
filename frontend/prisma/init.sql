-- PeleAnálise · Esquema MySQL generado desde prisma/schema.prisma
-- (prisma migrate diff --from-empty --to-schema-datamodel --script)
-- Uso: mysql -u root -p < prisma/init.sql
CREATE DATABASE IF NOT EXISTS `peleanalise` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `peleanalise`;

-- CreateTable
CREATE TABLE `users` (
    `id` VARCHAR(191) NOT NULL,
    `email` VARCHAR(191) NOT NULL,
    `password` VARCHAR(191) NOT NULL,
    `firstName` VARCHAR(100) NOT NULL,
    `lastName` VARCHAR(100) NOT NULL,
    `role` ENUM('ADMIN', 'DOCTOR', 'CAPTURISTA') NOT NULL DEFAULT 'CAPTURISTA',
    `isActive` BOOLEAN NOT NULL DEFAULT true,
    `avatarUrl` VARCHAR(500) NULL,
    `lastLoginAt` DATETIME(3) NULL,
    `deletedAt` DATETIME(3) NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL,

    UNIQUE INDEX `users_email_key`(`email`),
    INDEX `users_email_idx`(`email`),
    INDEX `users_role_idx`(`role`),
    INDEX `users_deletedAt_idx`(`deletedAt`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `refresh_tokens` (
    `id` VARCHAR(191) NOT NULL,
    `token` VARCHAR(512) NOT NULL,
    `userId` VARCHAR(191) NOT NULL,
    `expiresAt` DATETIME(3) NOT NULL,
    `isRevoked` BOOLEAN NOT NULL DEFAULT false,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    UNIQUE INDEX `refresh_tokens_token_key`(`token`),
    INDEX `refresh_tokens_userId_idx`(`userId`),
    INDEX `refresh_tokens_token_idx`(`token`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `patients` (
    `id` VARCHAR(191) NOT NULL,
    `firstName` VARCHAR(100) NOT NULL,
    `lastName` VARCHAR(100) NOT NULL,
    `sex` ENUM('MASCULINO', 'FEMENINO', 'OTRO') NOT NULL,
    `birthDate` DATE NOT NULL,
    `curp` VARCHAR(18) NULL,
    `phone` VARCHAR(20) NULL,
    `email` VARCHAR(255) NULL,
    `address` TEXT NULL,
    `observations` TEXT NULL,
    `isActive` BOOLEAN NOT NULL DEFAULT true,
    `deletedAt` DATETIME(3) NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL,

    UNIQUE INDEX `patients_curp_key`(`curp`),
    INDEX `patients_lastName_firstName_idx`(`lastName`, `firstName`),
    INDEX `patients_curp_idx`(`curp`),
    INDEX `patients_deletedAt_idx`(`deletedAt`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `medical_records` (
    `id` VARCHAR(191) NOT NULL,
    `patientId` VARCHAR(191) NOT NULL,
    `doctorId` VARCHAR(191) NOT NULL,
    `consultationReason` TEXT NOT NULL,
    `preliminaryDiagnosis` TEXT NULL,
    `observations` TEXT NULL,
    `consultationDate` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `deletedAt` DATETIME(3) NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL,

    INDEX `medical_records_patientId_idx`(`patientId`),
    INDEX `medical_records_doctorId_idx`(`doctorId`),
    INDEX `medical_records_consultationDate_idx`(`consultationDate`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `studies` (
    `id` VARCHAR(191) NOT NULL,
    `patientId` VARCHAR(191) NOT NULL,
    `recordId` VARCHAR(191) NULL,
    `capturedById` VARCHAR(191) NOT NULL,
    `studyDate` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `lesionType` ENUM('MELANOMA', 'NEVUS', 'CARCINOMA_BASOCELULAR', 'CARCINOMA_ESPINOCELULAR', 'QUERATOSIS_ACTINCA', 'DERMATOFIBROMA', 'LESION_VASCULAR', 'OTRO') NOT NULL DEFAULT 'OTRO',
    `anatomicLocation` VARCHAR(200) NOT NULL,
    `clinicalComments` TEXT NULL,
    `riskLevel` ENUM('BENIGNO', 'SOSPECHOSO', 'MALIGNO') NULL,
    `isProcessed` BOOLEAN NOT NULL DEFAULT false,
    `deletedAt` DATETIME(3) NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL,

    INDEX `studies_patientId_idx`(`patientId`),
    INDEX `studies_recordId_idx`(`recordId`),
    INDEX `studies_studyDate_idx`(`studyDate`),
    INDEX `studies_riskLevel_idx`(`riskLevel`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `images` (
    `id` VARCHAR(191) NOT NULL,
    `studyId` VARCHAR(191) NOT NULL,
    `type` ENUM('ORIGINAL', 'CLEANED', 'MASK', 'GRADCAM', 'OVERLAY') NOT NULL DEFAULT 'ORIGINAL',
    `filename` VARCHAR(255) NOT NULL,
    `storagePath` VARCHAR(500) NOT NULL,
    `mimeType` VARCHAR(50) NOT NULL,
    `sizeBytes` INTEGER NOT NULL,
    `width` INTEGER NULL,
    `height` INTEGER NULL,
    `deletedAt` DATETIME(3) NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL,

    INDEX `images_studyId_idx`(`studyId`),
    INDEX `images_type_idx`(`type`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `analyses` (
    `id` VARCHAR(191) NOT NULL,
    `studyId` VARCHAR(191) NOT NULL,
    `processedAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `deletedAt` DATETIME(3) NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL,

    UNIQUE INDEX `analyses_studyId_key`(`studyId`),
    INDEX `analyses_studyId_idx`(`studyId`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `abcde_metrics` (
    `id` VARCHAR(191) NOT NULL,
    `analysisId` VARCHAR(191) NOT NULL,
    `asymmetryScore` DOUBLE NOT NULL,
    `asymmetryH` DOUBLE NOT NULL,
    `asymmetryV` DOUBLE NOT NULL,
    `huMoments` JSON NOT NULL,
    `borderScore` DOUBLE NOT NULL,
    `perimeter` DOUBLE NOT NULL,
    `area` DOUBLE NOT NULL,
    `compactness` DOUBLE NOT NULL,
    `rugosity` DOUBLE NOT NULL,
    `colorScore` DOUBLE NOT NULL,
    `colorVariance` DOUBLE NOT NULL,
    `meanR` DOUBLE NOT NULL,
    `meanG` DOUBLE NOT NULL,
    `meanB` DOUBLE NOT NULL,
    `stdR` DOUBLE NOT NULL,
    `stdG` DOUBLE NOT NULL,
    `stdB` DOUBLE NOT NULL,
    `colorHistogram` JSON NOT NULL,
    `diameterScore` DOUBLE NOT NULL,
    `diameterPx` DOUBLE NOT NULL,
    `diameterMm` DOUBLE NOT NULL,
    `pixelPerMm` DOUBLE NOT NULL,
    `evolutionDelta` DOUBLE NULL,
    `totalScore` DOUBLE NOT NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL,

    UNIQUE INDEX `abcde_metrics_analysisId_key`(`analysisId`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `predictions` (
    `id` VARCHAR(191) NOT NULL,
    `analysisId` VARCHAR(191) NOT NULL,
    `prediction` ENUM('BENIGNO', 'SOSPECHOSO', 'MALIGNO') NOT NULL,
    `probability` DOUBLE NOT NULL,
    `probBenigno` DOUBLE NOT NULL,
    `probSospechoso` DOUBLE NOT NULL,
    `probMaligno` DOUBLE NOT NULL,
    `modelVersion` VARCHAR(50) NOT NULL,
    `gradcamPath` VARCHAR(500) NULL,
    `inferenceTimeMs` INTEGER NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL,

    UNIQUE INDEX `predictions_analysisId_key`(`analysisId`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `audit_logs` (
    `id` VARCHAR(191) NOT NULL,
    `userId` VARCHAR(191) NULL,
    `action` ENUM('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'EXPORT', 'ANALYZE') NOT NULL,
    `resource` VARCHAR(100) NOT NULL,
    `resourceId` VARCHAR(100) NULL,
    `metadata` JSON NULL,
    `ipAddress` VARCHAR(45) NULL,
    `userAgent` VARCHAR(500) NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    INDEX `audit_logs_userId_idx`(`userId`),
    INDEX `audit_logs_action_idx`(`action`),
    INDEX `audit_logs_resource_idx`(`resource`),
    INDEX `audit_logs_createdAt_idx`(`createdAt`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- AddForeignKey
ALTER TABLE `refresh_tokens` ADD CONSTRAINT `refresh_tokens_userId_fkey` FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `medical_records` ADD CONSTRAINT `medical_records_patientId_fkey` FOREIGN KEY (`patientId`) REFERENCES `patients`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `medical_records` ADD CONSTRAINT `medical_records_doctorId_fkey` FOREIGN KEY (`doctorId`) REFERENCES `users`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `studies` ADD CONSTRAINT `studies_patientId_fkey` FOREIGN KEY (`patientId`) REFERENCES `patients`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `studies` ADD CONSTRAINT `studies_recordId_fkey` FOREIGN KEY (`recordId`) REFERENCES `medical_records`(`id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `studies` ADD CONSTRAINT `studies_capturedById_fkey` FOREIGN KEY (`capturedById`) REFERENCES `users`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `images` ADD CONSTRAINT `images_studyId_fkey` FOREIGN KEY (`studyId`) REFERENCES `studies`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `analyses` ADD CONSTRAINT `analyses_studyId_fkey` FOREIGN KEY (`studyId`) REFERENCES `studies`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `abcde_metrics` ADD CONSTRAINT `abcde_metrics_analysisId_fkey` FOREIGN KEY (`analysisId`) REFERENCES `analyses`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `predictions` ADD CONSTRAINT `predictions_analysisId_fkey` FOREIGN KEY (`analysisId`) REFERENCES `analyses`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `audit_logs` ADD CONSTRAINT `audit_logs_userId_fkey` FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE SET NULL ON UPDATE CASCADE;

