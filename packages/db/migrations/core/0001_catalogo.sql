CREATE TABLE `assets` (
	`id` text PRIMARY KEY NOT NULL,
	`part_id` text,
	`replica_id` text,
	`view` text NOT NULL,
	`level` text NOT NULL,
	`license_status` text NOT NULL,
	`license_text` text,
	`source_url` text,
	`r2_key` text,
	`sha256` text,
	`publishable` integer DEFAULT false NOT NULL,
	`is_demo` integer NOT NULL,
	FOREIGN KEY (`part_id`) REFERENCES `parts`(`id`),
	FOREIGN KEY (`replica_id`) REFERENCES `replicas`(`id`),
	CONSTRAINT "assets_view_ck" CHECK("assets"."view" IN ('2d','3d')),
	CONSTRAINT "assets_level_ck" CHECK("assets"."level" IN ('T0','T1','T2','T3')),
	CONSTRAINT "assets_license_ck" CHECK("assets"."license_status" IN ('own','ceded','cc0','cc-by','third-party-reference')),
	CONSTRAINT "assets_one_owner_ck" CHECK(("assets"."part_id" IS NULL) <> ("assets"."replica_id" IS NULL)),
	CONSTRAINT "assets_publishable_ck" CHECK("assets"."publishable" = 0 OR ("assets"."license_status" <> 'third-party-reference' AND "assets"."is_demo" = 0))
);
--> statement-breakpoint
CREATE INDEX `assets_part_idx` ON `assets` (`part_id`);--> statement-breakpoint
CREATE INDEX `assets_replica_idx` ON `assets` (`replica_id`);--> statement-breakpoint
CREATE TABLE `brands` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`is_demo` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `brands_name_unique` ON `brands` (`name`);--> statement-breakpoint
CREATE TABLE `categories` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`parent_id` text,
	`is_demo` integer NOT NULL,
	FOREIGN KEY (`parent_id`) REFERENCES `categories`(`id`)
);
--> statement-breakpoint
CREATE INDEX `categories_parent_idx` ON `categories` (`parent_id`);--> statement-breakpoint
CREATE TABLE `dimensions` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`subject_type` text NOT NULL,
	`subject_id` text NOT NULL,
	`key` text NOT NULL,
	`value` real,
	`value_min` real,
	`value_max` real,
	`unit` text NOT NULL,
	`status` text NOT NULL,
	`sources` text NOT NULL,
	`confidence` text,
	`checked_on` text,
	`note` text,
	`is_demo` integer NOT NULL,
	CONSTRAINT "dimensions_subject_type_ck" CHECK("dimensions"."subject_type" IN ('interface','platform','part_family','part','replica')),
	CONSTRAINT "dimensions_unit_ck" CHECK("dimensions"."unit" IN ('mm','count')),
	CONSTRAINT "dimensions_status_ck" CHECK("dimensions"."status" IN ('verified','cited','pending')),
	CONSTRAINT "dimensions_confidence_ck" CHECK("dimensions"."confidence" IS NULL OR "dimensions"."confidence" IN ('high','medium','low')),
	CONSTRAINT "dimensions_nonnegative_ck" CHECK(("dimensions"."value" IS NULL OR "dimensions"."value" >= 0) AND ("dimensions"."value_min" IS NULL OR "dimensions"."value_min" >= 0) AND ("dimensions"."value_max" IS NULL OR "dimensions"."value_max" >= 0)),
	CONSTRAINT "dimensions_honest_ck" CHECK(("dimensions"."status" = 'pending' AND "dimensions"."value" IS NULL AND "dimensions"."value_min" IS NULL AND "dimensions"."value_max" IS NULL AND "dimensions"."confidence" IS NULL AND "dimensions"."checked_on" IS NULL AND json_array_length("dimensions"."sources") = 0)
        OR ("dimensions"."status" <> 'pending' AND ("dimensions"."value" IS NOT NULL OR "dimensions"."value_min" IS NOT NULL OR "dimensions"."value_max" IS NOT NULL) AND "dimensions"."confidence" IS NOT NULL AND "dimensions"."checked_on" IS NOT NULL AND json_array_length("dimensions"."sources") > 0)),
	CONSTRAINT "dimensions_range_ck" CHECK("dimensions"."value_min" IS NULL OR "dimensions"."value_max" IS NULL OR "dimensions"."value_min" <= "dimensions"."value_max")
);
--> statement-breakpoint
CREATE UNIQUE INDEX `dimensions_subject_key_uq` ON `dimensions` (`subject_type`,`subject_id`,`key`);--> statement-breakpoint
CREATE TABLE `interfaces` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`kind` text,
	`description` text,
	`status` text NOT NULL,
	`source_url` text,
	`source_checked_on` text,
	`confidence` text,
	`notes` text,
	`is_demo` integer NOT NULL,
	CONSTRAINT "interfaces_status_ck" CHECK("interfaces"."status" IN ('verified','pending','proposed')),
	CONSTRAINT "interfaces_confidence_ck" CHECK("interfaces"."confidence" IS NULL OR "interfaces"."confidence" IN ('high','medium','low')),
	CONSTRAINT "interfaces_verified_has_source_ck" CHECK("interfaces"."status" <> 'verified' OR ("interfaces"."source_url" IS NOT NULL AND "interfaces"."source_checked_on" IS NOT NULL AND "interfaces"."confidence" IS NOT NULL))
);
--> statement-breakpoint
CREATE TABLE `part_families` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`category_id` text NOT NULL,
	`expected_level` text NOT NULL,
	`applies_to_all` integer NOT NULL,
	`parameters` text NOT NULL,
	`example_brands` text NOT NULL,
	`status` text NOT NULL,
	`source_url` text,
	`source_checked_on` text,
	`confidence` text,
	`notes` text,
	`is_demo` integer NOT NULL,
	FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`),
	CONSTRAINT "part_families_level_ck" CHECK("part_families"."expected_level" IN ('T0','T1','T2','T3')),
	CONSTRAINT "part_families_status_ck" CHECK("part_families"."status" IN ('verified','pending')),
	CONSTRAINT "part_families_confidence_ck" CHECK("part_families"."confidence" IS NULL OR "part_families"."confidence" IN ('high','medium','low')),
	CONSTRAINT "part_families_verified_has_source_ck" CHECK("part_families"."status" <> 'verified' OR ("part_families"."source_url" IS NOT NULL AND "part_families"."source_checked_on" IS NOT NULL AND "part_families"."confidence" IS NOT NULL))
);
--> statement-breakpoint
CREATE INDEX `part_families_category_idx` ON `part_families` (`category_id`);--> statement-breakpoint
CREATE TABLE `part_family_interfaces` (
	`part_family_id` text NOT NULL,
	`interface_id` text NOT NULL,
	`role` text NOT NULL,
	PRIMARY KEY(`part_family_id`, `interface_id`, `role`),
	FOREIGN KEY (`part_family_id`) REFERENCES `part_families`(`id`),
	FOREIGN KEY (`interface_id`) REFERENCES `interfaces`(`id`),
	CONSTRAINT "part_family_interfaces_role_ck" CHECK("part_family_interfaces"."role" IN ('offers','requires','unspecified'))
);
--> statement-breakpoint
CREATE INDEX `part_family_interfaces_iface_idx` ON `part_family_interfaces` (`interface_id`);--> statement-breakpoint
CREATE TABLE `part_family_platform_families` (
	`part_family_id` text NOT NULL,
	`platform_family_id` text NOT NULL,
	PRIMARY KEY(`part_family_id`, `platform_family_id`),
	FOREIGN KEY (`part_family_id`) REFERENCES `part_families`(`id`),
	FOREIGN KEY (`platform_family_id`) REFERENCES `platform_families`(`id`)
);
--> statement-breakpoint
CREATE TABLE `part_interfaces` (
	`part_id` text NOT NULL,
	`interface_id` text NOT NULL,
	`role` text NOT NULL,
	PRIMARY KEY(`part_id`, `interface_id`, `role`),
	FOREIGN KEY (`part_id`) REFERENCES `parts`(`id`),
	FOREIGN KEY (`interface_id`) REFERENCES `interfaces`(`id`),
	CONSTRAINT "part_interfaces_role_ck" CHECK("part_interfaces"."role" IN ('offers','requires'))
);
--> statement-breakpoint
CREATE INDEX `part_interfaces_iface_idx` ON `part_interfaces` (`interface_id`);--> statement-breakpoint
CREATE TABLE `parts` (
	`id` text PRIMARY KEY NOT NULL,
	`part_family_id` text,
	`generator_family` text,
	`name` text NOT NULL,
	`kind` text NOT NULL,
	`brand_id` text,
	`level` text DEFAULT 'T0' NOT NULL,
	`parameters` text,
	`notes` text,
	`is_demo` integer NOT NULL,
	FOREIGN KEY (`part_family_id`) REFERENCES `part_families`(`id`),
	FOREIGN KEY (`brand_id`) REFERENCES `brands`(`id`),
	CONSTRAINT "parts_kind_ck" CHECK("parts"."kind" IN ('part','accessory','consumable')),
	CONSTRAINT "parts_level_ck" CHECK("parts"."level" IN ('T0','T1','T2','T3'))
);
--> statement-breakpoint
CREATE INDEX `parts_family_idx` ON `parts` (`part_family_id`);--> statement-breakpoint
CREATE TABLE `platform_brands` (
	`platform_id` text NOT NULL,
	`brand_id` text NOT NULL,
	PRIMARY KEY(`platform_id`, `brand_id`),
	FOREIGN KEY (`platform_id`) REFERENCES `platforms`(`id`),
	FOREIGN KEY (`brand_id`) REFERENCES `brands`(`id`)
);
--> statement-breakpoint
CREATE TABLE `platform_families` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`is_demo` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `platform_interfaces` (
	`platform_id` text NOT NULL,
	`interface_id` text NOT NULL,
	PRIMARY KEY(`platform_id`, `interface_id`),
	FOREIGN KEY (`platform_id`) REFERENCES `platforms`(`id`),
	FOREIGN KEY (`interface_id`) REFERENCES `interfaces`(`id`)
);
--> statement-breakpoint
CREATE INDEX `platform_interfaces_iface_idx` ON `platform_interfaces` (`interface_id`);--> statement-breakpoint
CREATE TABLE `platforms` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`family_id` text NOT NULL,
	`mechanisms` text NOT NULL,
	`variants` text NOT NULL,
	`magazine_well_interface_id` text,
	`status` text NOT NULL,
	`source_url` text,
	`source_checked_on` text,
	`confidence` text,
	`notes` text,
	`is_demo` integer NOT NULL,
	FOREIGN KEY (`family_id`) REFERENCES `platform_families`(`id`),
	FOREIGN KEY (`magazine_well_interface_id`) REFERENCES `interfaces`(`id`),
	CONSTRAINT "platforms_status_ck" CHECK("platforms"."status" IN ('verified','pending')),
	CONSTRAINT "platforms_confidence_ck" CHECK("platforms"."confidence" IS NULL OR "platforms"."confidence" IN ('high','medium','low')),
	CONSTRAINT "platforms_verified_has_source_ck" CHECK("platforms"."status" <> 'verified' OR ("platforms"."source_url" IS NOT NULL AND "platforms"."source_checked_on" IS NOT NULL AND "platforms"."confidence" IS NOT NULL))
);
--> statement-breakpoint
CREATE INDEX `platforms_family_idx` ON `platforms` (`family_id`);--> statement-breakpoint
CREATE TABLE `replicas` (
	`id` text PRIMARY KEY NOT NULL,
	`platform_id` text NOT NULL,
	`brand_id` text NOT NULL,
	`model` text NOT NULL,
	`mechanism` text,
	`level` text DEFAULT 'T0' NOT NULL,
	`source_url` text,
	`source_checked_on` text,
	`notes` text,
	`is_demo` integer NOT NULL,
	FOREIGN KEY (`platform_id`) REFERENCES `platforms`(`id`),
	FOREIGN KEY (`brand_id`) REFERENCES `brands`(`id`),
	CONSTRAINT "replicas_level_ck" CHECK("replicas"."level" IN ('T0','T1','T2','T3'))
);
--> statement-breakpoint
CREATE UNIQUE INDEX `replicas_brand_model_uq` ON `replicas` (`brand_id`,`model`);--> statement-breakpoint
CREATE INDEX `replicas_platform_idx` ON `replicas` (`platform_id`);