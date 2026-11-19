/*
 Navicat Premium Dump SQL

 Source Server         : gift
 Source Server Type    : SQLite
 Source Server Version : 3045000 (3.45.0)
 Source Schema         : main

 Target Server Type    : SQLite
 Target Server Version : 3045000 (3.45.0)
 File Encoding         : 65001

 Date: 19/11/2026 08:36:49
*/

PRAGMA foreign_keys = false;

-- ----------------------------
-- Table structure for cate
-- ----------------------------
DROP TABLE IF EXISTS "cate";
CREATE TABLE "cate" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "name" TEXT
);

-- ----------------------------
-- Records of cate
-- ----------------------------
BEGIN;
INSERT INTO "cate" ("id", "name") VALUES (1, '结婚');
INSERT INTO "cate" ("id", "name") VALUES (2, '其他');
COMMIT;

-- ----------------------------
-- Table structure for expenses
-- ----------------------------
DROP TABLE IF EXISTS "expenses";
CREATE TABLE "expenses" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "name" TEXT,
  "amount" integer,
  "date" DATE,
  "relation_id" INTEGER NOT NULL DEFAULT 1,
  "cate_id" INTEGER NOT NULL DEFAULT 1
);

-- ----------------------------
-- Records of expenses
-- ----------------------------
BEGIN;
INSERT INTO "expenses" ("id", "name", "amount", "date", "relation_id", "cate_id") VALUES (1, '白孟楠', 188, '2021-10-4', 3, 1);
INSERT INTO "expenses" ("id", "name", "amount", "date", "relation_id", "cate_id") VALUES (2, '王赏', 188, '2022-10-3', 3, 1);
INSERT INTO "expenses" ("id", "name", "amount", "date", "relation_id", "cate_id") VALUES (3, '志刚', 200, '2022-10-4', 2, 1);
INSERT INTO "expenses" ("id", "name", "amount", "date", "relation_id", "cate_id") VALUES (4, '范彩霞', 188, '2023-11-21', 3, 1);
INSERT INTO "expenses" ("id", "name", "amount", "date", "relation_id", "cate_id") VALUES (5, '朱一飞', 500, '2024-6-15', 3, 1);
INSERT INTO "expenses" ("id", "name", "amount", "date", "relation_id", "cate_id") VALUES (6, '张迪', 300, '2025-10-18', 2, 1);
INSERT INTO "expenses" ("id", "name", "amount", "date", "relation_id", "cate_id") VALUES (7, '赵子星', 200, '2026-5-4', 3, 1);
INSERT INTO "expenses" ("id", "name", "amount", "date", "relation_id", "cate_id") VALUES (8, '刘伟贤', 1000, '2026-9-19', 3, 1);
INSERT INTO "expenses" ("id", "name", "amount", "date", "relation_id", "cate_id") VALUES (9, '刘志峰', 200, '2026-10-6', 3, 1);
COMMIT;

-- ----------------------------
-- Table structure for gift
-- ----------------------------
DROP TABLE IF EXISTS "gift";
CREATE TABLE "gift" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "name" TEXT,
  "amount" TEXT,
  "date" DATE
);

-- ----------------------------
-- Records of gift
-- ----------------------------
BEGIN;
INSERT INTO "gift" ("id", "name", "amount", "date") VALUES (1, '礼单名称', '100', '2026-1-1');
COMMIT;

-- ----------------------------
-- Table structure for income
-- ----------------------------
DROP TABLE IF EXISTS "income";
CREATE TABLE "income" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "name" TEXT,
  "amount" TEXT,
  "relation_id" TEXT,
  "desc" TEXT,
  "gift_id" INTEGER NOT NULL
);

-- ----------------------------
-- Records of income
-- ----------------------------
BEGIN;
INSERT INTO "income" ("id", "name", "amount", "relation_id", "desc", "gift_id") VALUES (1, '张三', '30', '1', NULL, 1);
INSERT INTO "income" ("id", "name", "amount", "relation_id", "desc", "gift_id") VALUES (2, '李四', '70', '2', NULL, 1);
COMMIT;

-- ----------------------------
-- Table structure for relation
-- ----------------------------
DROP TABLE IF EXISTS "relation";
CREATE TABLE "relation" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "name" TEXT
);

-- ----------------------------
-- Records of relation
-- ----------------------------
BEGIN;
INSERT INTO "relation" ("id", "name") VALUES (1, '亲戚');
INSERT INTO "relation" ("id", "name") VALUES (2, '朋友');
INSERT INTO "relation" ("id", "name") VALUES (3, '同学');
INSERT INTO "relation" ("id", "name") VALUES (4, '其他');
COMMIT;

-- ----------------------------
-- Table structure for sqlite_sequence
-- ----------------------------
DROP TABLE IF EXISTS "sqlite_sequence";
CREATE TABLE sqlite_sequence(name,seq);

-- ----------------------------
-- Records of sqlite_sequence
-- ----------------------------
BEGIN;
INSERT INTO "sqlite_sequence" ("name", "seq") VALUES ('relation', 4);
INSERT INTO "sqlite_sequence" ("name", "seq") VALUES ('cate', 2);
INSERT INTO "sqlite_sequence" ("name", "seq") VALUES ('expenses', 9);
INSERT INTO "sqlite_sequence" ("name", "seq") VALUES ('income', 2);
INSERT INTO "sqlite_sequence" ("name", "seq") VALUES ('gift', 1);
COMMIT;

-- ----------------------------
-- Auto increment value for cate
-- ----------------------------
UPDATE "main"."sqlite_sequence" SET seq = 2 WHERE name = 'cate';

-- ----------------------------
-- Auto increment value for expenses
-- ----------------------------
UPDATE "main"."sqlite_sequence" SET seq = 9 WHERE name = 'expenses';

-- ----------------------------
-- Auto increment value for gift
-- ----------------------------
UPDATE "main"."sqlite_sequence" SET seq = 1 WHERE name = 'gift';

-- ----------------------------
-- Auto increment value for income
-- ----------------------------
UPDATE "main"."sqlite_sequence" SET seq = 2 WHERE name = 'income';

-- ----------------------------
-- Auto increment value for relation
-- ----------------------------
UPDATE "main"."sqlite_sequence" SET seq = 4 WHERE name = 'relation';

PRAGMA foreign_keys = true;
