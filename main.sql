/*
 Navicat Premium Dump SQL

 Source Server         : gift
 Source Server Type    : SQLite
 Source Server Version : 3045000 (3.45.0)
 Source Schema         : main

 Target Server Type    : SQLite
 Target Server Version : 3045000 (3.45.0)
 File Encoding         : 65001

 Date: 19/11/2026 11:34:43
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
INSERT INTO "expenses" ("id", "name", "amount", "date", "relation_id", "cate_id") VALUES (1, '张三', 100, '2026-11-11', 1, 1);
COMMIT;

-- ----------------------------
-- Table structure for gift
-- ----------------------------
DROP TABLE IF EXISTS "gift";
CREATE TABLE "gift" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "name" TEXT,
  "date" DATE
);

-- ----------------------------
-- Records of gift
-- ----------------------------
BEGIN;
INSERT INTO "gift" ("id", "name", "date") VALUES (1, '礼单名称', '2026-1-1');
INSERT INTO "gift" ("id", "name", "date") VALUES (2, '礼单2', '2026-11-19');
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
INSERT INTO "income" ("id", "name", "amount", "relation_id", "desc", "gift_id") VALUES (3, '王二', '100', '1', '', 2);
INSERT INTO "income" ("id", "name", "amount", "relation_id", "desc", "gift_id") VALUES (4, '麻子', '200', '2', '', 2);
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
INSERT INTO "sqlite_sequence" ("name", "seq") VALUES ('income', 4);
INSERT INTO "sqlite_sequence" ("name", "seq") VALUES ('gift', 2);
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
UPDATE "main"."sqlite_sequence" SET seq = 2 WHERE name = 'gift';

-- ----------------------------
-- Auto increment value for income
-- ----------------------------
UPDATE "main"."sqlite_sequence" SET seq = 4 WHERE name = 'income';

-- ----------------------------
-- Auto increment value for relation
-- ----------------------------
UPDATE "main"."sqlite_sequence" SET seq = 4 WHERE name = 'relation';

PRAGMA foreign_keys = true;
