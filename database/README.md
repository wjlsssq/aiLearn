# 本地开发库全量 SQL

用户于 2026-11-16 明确要求通过 Git 交接数据库，当前快照为 `snapshots/langchain_lab.sql`，约 3.35 MB，UTF-8，可直接用 MySQL 8 客户端恢复。它包含完整表结构、索引、外键、自增状态与全部数据，不是只导出建表语句或重新随机生成的数据。

| 表 | 行数 |
| --- | ---: |
| users | 1,002 |
| orders | 20,002 |
| chat_sessions | 11 |
| chat_messages | 44 |
| access_tokens | 9 |
| alembic_version | 1 |
| knowledge_documents | 0 |
| knowledge_document_versions | 0 |
| knowledge_chunks | 0 |

身份表保留原密码摘要和令牌摘要；它们不是明文密码或可直接使用的原令牌。快照不含 MySQL 系统账号库、数据库连接密码、模型密钥或 `runtime` 中的数据集明文密码文件。恢复后原有应用密码保持不变，新合成用户密码仍需保留原电脑的本机凭据文件；不能从 SQL 反解出明文。不要把真实生产数据或明文密钥加入后续快照。

## 在另一台电脑恢复

先 `git pull --ff-only` 并阅读交接文档。下面命令在仓库根目录执行，密码由 MySQL 客户端交互输入；本机客户端不在 PATH 时使用安装目录下的 mysql.exe。按自己机器的实际数据库账号和端口调整。

```powershell
# 新建空库；故意不使用 IF NOT EXISTS，库已存在时先停止，不覆盖已有内容。
mysql.exe --host=127.0.0.1 --port=3306 --user=root -p --execute="CREATE DATABASE langchain_lab CHARACTER SET utf8mb4"

# 仅在上一步成功创建空库后导入。source 避免 PowerShell 的重定向编码问题。
mysql.exe --host=127.0.0.1 --port=3306 --user=root -p --default-character-set=utf8mb4 --database=langchain_lab --execute="source database/snapshots/langchain_lab.sql"

# 检查主要数据与迁移版本。
mysql.exe --host=127.0.0.1 --port=3306 --user=root -p --database=langchain_lab --execute="SELECT COUNT(*) AS users FROM users; SELECT COUNT(*) AS orders FROM orders; SELECT version_num FROM alembic_version;"

# 使用本机 .env 和 E 盘依赖；有后续迁移时继续正常升级。
uv run --locked alembic -c backend/alembic.ini upgrade head
```

SQL 含 DROP TABLE IF EXISTS，只应导入新建空库；已有同名库时先自行备份并使用另一空库验证，不直接覆盖。文件不含 CREATE DATABASE / USE / DROP DATABASE，导入目标由客户端 `--database` 决定。本次未改动原业务库，恢复验证只使用临时库。

恢复后无需再次运行初始化或样本生成器来重建同一批数据。把本机 `.env` 指向恢复库，启动应用后重新登录即可；Git 拉取本身不会自动导入 SQL，也不会自动同步之后产生的订单和会话。

## 更新快照

仅在需要交接数据库时明确执行，普通功能提交不自动导出：

```powershell
uv run --locked python -X utf8 -m scripts.export_database
# 如果 mysqldump 未加入 PATH，可指定本机工具位置。
uv run --locked python -X utf8 -m scripts.export_database --mysqldump 'D:\soft\mysql\bin\mysqldump.exe'
```

脚本使用原生 mysqldump 的单事务快照，包含所有表、触发器、存储例程与事件（本次后三者均为 0），关闭 GTID 和表空间输出。每行 INSERT 使用完整列名，便于审查差异；恢复时按表批量提交，避免两万次逐行落盘。输出成功且未发现明显密钥特征后才替换共享快照。连接密码仅通过子进程环境传递，不写进命令行、脚本或 SQL。

本次在 MySQL 8.0.35 的独立临时库恢复，逐表核对建表结构、全部行数据指纹和行数；验证库完成后删除。快照 SHA256：`5be4ed6541938631d2755e830251e6af020025ba23b2104989b420a1459c7072`。后续更新快照时同步更新本文件的数量、校验和与交接记录，不能仅凭导出命令成功就宣称恢复验证通过。
