"""Q07：纯函数切分，不访问模型、数据库或用户文件路径。"""

import hashlib
import json
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ...core.errors import BusinessError
from ...schemas.knowledge import KnowledgeInput, ChunkPreview, SplitPreview

SPLITTER_VERSION = "recursive-zh/1.0.0"  # 分隔符或规范化行为变动时递增。


def preview_document(body: KnowledgeInput) -> SplitPreview:
    text = body.text.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip() or "\x00" in text:
        raise BusinessError(422, "请提供非空、无 NUL 字符的 UTF-8 纯文本")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=body.options.chunk_size,
        chunk_overlap=body.options.chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        length_function=len,  # 显式字符预算，避免把它称为 token 预算。
        keep_separator="end",  # 标点与标题仍留在原文片段内，不改写内容。
        strip_whitespace=False,
        add_start_index=True,  # 使用 LangChain 的来源偏移元数据。
    )
    documents = splitter.create_documents([text])
    if len(documents) > 512:
        raise BusinessError(422, "分块超过 512 个，请增大块大小或减小重叠量")
    headings = list(re.finditer(r"^#{1,6} +(.+)$", text, flags=re.MULTILINE))
    chunks = []
    for ordinal, document in enumerate(documents, 1):
        start = document.metadata["start_index"]
        end = start + len(document.page_content)
        if start < 0 or text[start:end] != document.page_content:
            raise BusinessError(422, "无法可靠定位分块原文，请调整切分参数")
        previous = [match.group(1) for match in headings if match.start() <= start]
        chunks.append(
            ChunkPreview(
                ordinal=ordinal,
                text=document.page_content,
                start=start,
                end=end,
                start_line=text.count("\n", 0, start) + 1,
                end_line=text.count("\n", 0, max(start, end - 1)) + 1,
                heading=previous[-1][:2000]
                if previous
                else None,  # 超长标题只保留阅读标签前缀。
            )
        )  # 每块都能用原文 [start:end] 逐字核对。
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    identity = json.dumps(
        [content_hash, body.options.model_dump(), SPLITTER_VERSION], sort_keys=True
    )
    fingerprint = hashlib.sha256(
        identity.encode()
    ).hexdigest()  # 参数变化也产生新版本。
    return SplitPreview(
        title=body.title.strip(),
        normalized_text=text,
        content_hash=content_hash,
        fingerprint=fingerprint,
        splitter_version=SPLITTER_VERSION,
        options=body.options,
        chunks=chunks,
    )
