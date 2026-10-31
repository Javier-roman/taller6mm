CREATE TABLE `meta` (
	`key` text PRIMARY KEY NOT NULL,
	`value` text NOT NULL
);
--> statement-breakpoint
-- Identifica la base: el test y la página de estado comprueban que cada binding apunta a la suya.
INSERT INTO `meta` (`key`, `value`) VALUES ('base', 'core'), ('migracion', '0000_meta');
