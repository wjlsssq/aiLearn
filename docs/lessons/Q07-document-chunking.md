# Q07：文档为什么要切分，chunk size 和 overlap 如何选择？

本课进入 RAG 的文档准备阶段：把合成售后规则变成可以定位原文、区分版本的分块。Q08 学 Embedding 和检索，Q09 才把证据接入回答；当前聊天不会因为导入规则就自动知道其中内容。

## 1. 先运行，再观察

在仓库根目录执行：

```powershell
# 同步新增的 langchain-text-splitters，仍使用 E 盘环境。
uv sync --locked
# 新电脑先执行；只初始化原有五张基线表和教学账号，不清空已有数据。
uv run --locked python -m scripts.init_db
# 老电脑和新电脑都执行；新增三张知识表及迁移版本记录，重复执行不重复建表。
uv run --locked alembic -c backend/alembic.ini upgrade head
uv run --locked alembic -c backend/alembic.ini current
```

由用户停止旧 Debug，再重新 Debug `backend/run.py`，刷新前端。登录 alice，打开“规则知识库”。没有模型密钥也能完成本课，全程不访问模型或 Embedding 服务。

1. 初次打开加载 `datasets/shop-rules-demo.md` 合成规则，也可选择 UTF-8 `.txt` / `.md` 文件或粘贴文本。
2. 用 A=160/30、B=300/60 点击“对比预览”，观察块数、正文与来源行。展开原文高亮，核对块是否真来自这份原文。
3. 修改 A 参数或正文后，旧预览消失，需要重新比较。“导入 A”保存当前 A 方案；B 只是实验对照。
4. 连续导入两次相同内容及参数：第二次复用当前有效版本。改变参数再导入：新版本变成当前有效，旧版本标成历史，仍能查看。
5. 刷新、重新打开文档，验证来源仍来自 MySQL。切换 bob 后，看不到 alice 的文档；同标题导入的是 bob 自己的独立文档。

“上传”在浏览器读取并解码纯文本，传给服务端的仍是 JSON 正文，不接收服务器文件路径，不保存本机文件名对应的原始文件。客户端限制 128 KB，服务端限制 20000 个 Unicode 码点；只换扩展名不等于完成 PDF 或 Word 解析。

## 2. 一句话回答面试题

切分用于在有限上下文预算中检索、组合相关证据。块过大可能混入无关内容，块过小可能切断条件和结论；overlap 尝试保留边界上下文，但会增加冗余。参数应结合文档结构、检索和回答效果验证，不能把某个固定值当作通用最优解。

Java 对照：原文像源记录，chunk 像可检索的派生记录；版本号和来源位置帮助找到当时依据。只保存一段字符串而没有文档、版本和位置，后续就难以解释答案来自哪里。

## 3. RecursiveCharacterTextSplitter 在做什么？

本项目从较大的边界开始尝试：空行 → 换行 → 中文句末标点 → 中文逗号 → 空格 → 单字符。只在当前片段仍太长时向更细粒度递归，不是先用模型总结文档，也不是固定每 N 个字无条件切一刀。

| 参数 | 本课语义 | 常见误解 |
| --- | --- | --- |
| chunk_size | `length_function=len` 下的最大字符数 | 不是 token 数，也不是每块必然恰好这么长 |
| chunk_overlap | 合并片段时尝试保留的重叠目标 | 不是每对相邻块必然精确重叠 N 字 |
| keep_separator="end" | 标点保留在前面的源片段 | 不删除标点再编造一个新正文 |
| strip_whitespace=False | 保留源空白，便于逐字追溯 | 与用于检索的清洗文本不是同一个目的 |
| add_start_index=True | 为 Document 加入来源起点元数据 | 不能脱离保存的规范化原文解释偏移 |

默认 A/B 仅用于观察差异，尚未证明哪组检索质量更好。实际 overlap 会受到段落长度和切分边界影响，可能小于目标甚至为零；严格连续字符文本则容易观察到精确重叠。

## 4. 来源元数据怎样解释？

服务端先去掉开头一个 BOM，把 CRLF / CR 统一为 LF，得到 `normalized_text`；不删除其余空白。每个块记录 ordinal、start/end、start_line/end_line、起点之前最近的 Markdown 标题。

`normalized_text[start:end] == chunk.text` 是可执行的不变量。start 从 0 开始，end 不包含在范围内；行号从 1 开始。后端按 Python Unicode 码点计数，前端用 `Array.from(text)` 切片，高亮不会因为 emoji 占两个 UTF-16 单元而错位。

标题标签只是块起点前最近的 `# 标题`，不是完整 Markdown 语法树；超长标题仅展示前 2000 字符。一个块可能跨多个标题，标题文字仍在原文中。表格、代码、PDF 页码和复杂层级尚未专门解析，不能声称当前切分保持了所有结构语义。

## 5. 沿代码逐行读与打断点

```text
KnowledgePanel / ChunkPreview
  → useKnowledge → api/knowledge
  → /api/knowledge/preview → Service → splitter
  → /api/knowledge/import → Service → Repository → MySQL
```

1. `schemas/knowledge.py`：输入上限、字符预算与 overlap 校验。每组最多 512 块，防止过大的重叠生成大量派生记录。
2. `ai/rag/splitter.py`：在 `create_documents([text])` 后打断点，观察真实 LangChain Document 的 page_content 和 metadata；再逐个核对 `text[start:end]`。
3. 同文件的 content_hash 和 fingerprint：前者只描述规范化内容，后者还包含 A 参数和算法版本；相同内容换参数，内容摘要相同但导入指纹不同。
4. `services/knowledge.import_document`：先计算、校验，再结束认证读取的旧快照，进入导入事务。此处 rollback 只释放只读快照，避免 MySQL 并发锁等待后还使用旧版本视图。
5. `repositories/knowledge.lock_document`：MySQL 唯一键 `(user_id, document_key)` 加 upsert / 行锁，串行处理同一文档导入。不是只靠“先查没有再插入”，后者在并发中会竞争。
6. `add_version`：写不可变原文版本和所有块，再切换 active_revision，最后由 Service commit。中途失败回滚，旧版本继续有效。
7. `read_version`：必须先确认当前用户归属，再读取版本与分块。不能只按别人给的 version ID 直接返回内容。
8. 前端 `ChunkPreview.vue`：选择块后显示源片段与原文高亮；`useKnowledge.ts` 在身份变化时清空并拒收旧响应。

## 6. 版本规则与 MySQL 表

| 表 | 保存什么 |
| --- | --- |
| knowledge_documents | 归属用户、标题、文档键、唯一当前有效版本号 |
| knowledge_document_versions | 不可变规范化原文、哈希、指纹、算法与参数、版本号 |
| knowledge_chunks | 版本 ID、块序号、正文与来源位置 |

同一用户的标题经过首尾去空白、NFKC 和 casefold 后计算文档键。标题只作为该用户的文档标识，不是服务器路径；不同标题即不同文档，相同正文跨标题不会全局去重。

只对比“当前有效版本”的 fingerprint：A → A 复用，A → B 新增版本；A → B → A 再次新增一个版本，不偷偷恢复旧版号。旧数据保留供追溯。后续检索必须限定当前用户与 active_revision；当前只完成版本与默认读取语义，还没有检索器或向量索引。

Alembic 首个 revision 为 `0001_knowledge`，仅管理新增三张表；原有五张表仍用 `init_db` 建基线。配置从同一根目录 `.env` 读取，迁移文件不包含密码。MySQL DDL 不保证整组事务回滚，迁移中途失败需核对实际表与 alembic_version 后修复，不盲目删表、stamp 或降级。正常学习只执行 upgrade，不执行会删除知识数据的 downgrade。

## 7. 三个实验与追问

1. **边界实验**：令 size=64，输入 160 个“甲”，比较 overlap=0 和 12；观察第二块起点前移。再用真实段落文本，解释为何 overlap 不一定精确达到 12。
2. **语义实验**：把“满足条件时可申请，以下情况除外”的例外紧接在条件后，比较小块和大块；切分结果完整保留文字，也可能拆散业务含义，后续要用检索和回答评估。
3. **追溯实验**：在原文插入 emoji 与 CRLF，核对规范化后位置；修改一个字再导入，看 content_hash、版本号与旧版正文。

| 面试追问 | 结合本项目回答 |
| --- | --- |
| 为什么不把整篇放进 Prompt？ | 小文档可以，但大文档会增加成本和无关上下文；切分为检索准备单位。 |
| overlap 越大越好吗？ | 不是；会放大块数、存储、重复召回及上下文成本。 |
| 只保存 content_hash 够吗？ | 不够；参数与算法变更也要跟踪，引用还需要版本及位置。 |
| 旧规则怎样撤下？ | 切换当前有效版本，后续检索按有效指针筛选；旧记录可留作审计追溯。 |
| 断点暂停时重复请求安全吗？ | 同文档导入会等锁；本课只保证当前指纹复用和事务一致，不承诺任意网络故障下所有操作 exactly-once。 |

验收命令：`uv run --locked python -m pytest tests -q`，包含真实 MySQL 的隔离、重复导入、版本切换、写入回滚和并发实验。浏览器验证了双参数预览、有效/历史版本、原文高亮与 375px 布局；没有调用付费模型。

官方依据：[递归文本切分器](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter)、[TextSplitter 来源起点](https://reference.langchain.com/python/langchain-text-splitters/base/TextSplitter)、[Alembic 迁移环境](https://alembic.sqlalchemy.org/en/latest/tutorial.html)。下一课 Q08 学 Embedding、向量相似度与 Top-K。
