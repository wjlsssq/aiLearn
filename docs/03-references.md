# 检索资料与版本依据

检索日期：2026-11-05。题目是为 ShopMind 场景重新组织的学习问题，技术事实以官方文档和实现仓库为准。

## 1. 公开面经主题

| 来源 | 用途 | 使用边界 |
| --- | --- | --- |
| [Datawhale Hello-Agents：面试问题总结](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra01-%E9%9D%A2%E8%AF%95%E9%97%AE%E9%A2%98%E6%80%BB%E7%BB%93.md) | 参考 Agent、记忆、工具、RAG 和评估的面试主题 | 作者整理的公开经历；不等同所有公司的频率统计 |
| [LLMInterviewQuestions](https://github.com/llmgenai/LLMInterviewQuestions) | 交叉参考 Prompt、切分、Embedding、检索和工程问题 | 开源题目汇集；问题覆盖度不能直接换算成出现概率 |

选题方法：从公开资料的共同主题中挑出能在项目中实现、观察和测试的内容，再按知识依赖与实现难度排序。Q01～Q20 是学习顺序。RAG、切分、Embedding、工具、记忆和评估优先安排；MCP、Text-to-SQL、多 Agent 等作为主线后的扩展。

## 2. 官方技术依据

| 资料 | 对应计划 |
| --- | --- |
| [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview) | 模型、工具、`create_agent` 与框架职责 |
| [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1) | 新旧 API、简化命名空间与 `langchain-classic` 辨析 |
| [Retrieval / RAG](https://docs.langchain.com/oss/python/deepagents/retrieval) | 文档、Embedding、检索与生成流程；原 LangChain retrieval 地址目前重定向至此，本文只参考通用检索概念 |
| [LangChain streaming](https://docs.langchain.com/oss/python/langchain/streaming) | 模型文本与执行事件流 |
| [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) | checkpoint 与 store 的职责、thread 状态与长期数据 |
| [LangGraph checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers) | 持久化、恢复与 checkpoint 接口 |
| [MySQL ngram 全文解析器](https://dev.mysql.com/doc/refman/8.4/en/fulltext-search-ngram.html) | 中文全文检索、粒度、停用词与 FULLTEXT 配置 |

官方文档可能继续变化。实际开始每个模块时，按项目锁定版本核对 API；课程代码、锁文件与讲义同步维护。

## 3. MySQL checkpoint 实现依据

[tjni/langgraph-checkpoint-mysql](https://github.com/tjni/langgraph-checkpoint-mysql) 是社区实现，提供 MySQL checkpoint saver。其 README 列出 MySQL 最低版本要求、驱动选项及首次 setup 等用法。

计划先验证后采用，不承诺它与任意未来版本的 LangGraph 都兼容。Q15 的重启、隔离、暂停恢复与副作用测试是完成条件。业务表迁移与 saver 自己管理的表要区分清楚。

## 4. 本计划的判断与假设

- 选择售后客服、Python FastAPI、Vue 与 20 个模块，是针对用户背景和目标做的教学设计，不是任何来源给出的统一最佳方案。
- MySQL JSON + NumPy 是小语料教学基线，不将其描述成具备原生 ANN 索引的数据库方案。
- 约 8～10 周建立在每周 8～10 小时的假设上，实际以理解和验收为准。
- 尚未选择具体模型供应商、模型型号或付费套餐；真实调用能力在环境阶段核对。
- 公开面经用于确定覆盖主题，最终回答必须能由自己的代码和测试支持。
