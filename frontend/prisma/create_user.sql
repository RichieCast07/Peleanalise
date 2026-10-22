-- Usuario de aplicación (coincide con DATABASE_URL de frontend/.env). Ejecutar como root.
CREATE USER IF NOT EXISTS 'cesar'@'localhost' IDENTIFIED BY 'cesar123';
GRANT ALL PRIVILEGES ON `peleanalise`.* TO 'cesar'@'localhost';
FLUSH PRIVILEGES;
