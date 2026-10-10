import math
import re
from collections import Counter

import tiktoken

from app.schemas import KnowledgeNode, KnowledgeTree, SourceDocument

TOKENIZER = tiktoken.get_encoding("o200k_base")


def tokens(text: str):
    return len(TOKENIZER.encode(text, disallowed_special=()))


def words(text):
    return re.findall(r"\w{2,}", text.lower())


def unit_text(unit):
    return f"[{unit.id} | trang {unit.page} | {unit.kind}]\n{unit.content}"


def select_context(source: SourceDocument, query: str, limit: int, mandatory_ids=(), mode="retrieved"):
    units = source.units
    full = "\n\n".join(unit_text(u) for u in units)
    full_tokens = tokens(full)
    if mode == "full":
        return full, full_tokens, full_tokens
    if full_tokens <= limit:
        return full, full_tokens, full_tokens
    query_words = set(words(query))
    counts = Counter(w for u in units for w in set(words(u.content)))
    scores = {u.id: sum(math.log(1 + len(units) / counts[w]) for w in query_words & set(words(u.content)))
              + (2 if u.kind == "heading" else 0) for u in units}
    # Keep cited evidence intact; never silently exceed the retrieval budget.
    mandatory = set(mandatory_ids)
    order = [u for u in units if u.id in mandatory]
    required = "\n\n".join(unit_text(u) for u in order)
    if tokens(required) > limit:
        raise ValueError("Tập nguồn bắt buộc vượt ngân sách context; hãy giảm phạm vi hoặc tăng MAIC_CONTEXT_TOKENS")
    order.extend(sorted(units, key=lambda u: scores[u.id], reverse=True))
    picked = {u.id: u for u in order if u.id in mandatory}
    for unit in order:
        if unit.id in picked:
            continue
        candidate = "\n\n".join(unit_text(u) for u in units if u.id in picked or u.id == unit.id)
        if tokens(candidate) <= limit:
            picked[unit.id] = unit
    selected = "\n\n".join(unit_text(u) for u in units if u.id in picked)
    if units and not selected:
        raise ValueError("Không có đoạn nguồn nào vừa ngân sách context; hãy tăng MAIC_CONTEXT_TOKENS")
    return selected, full_tokens, tokens(selected)


def build_tree(source: SourceDocument):
    nodes = []
    active = None
    for unit in source.units:
        if unit.kind == "heading" or active is None:
            active = KnowledgeNode(id=f"k{len(nodes)+1:03}", parent_id=None,
                                   title=unit.content[:150] if unit.kind == "heading" else f"Nội dung từ trang {unit.page}",
                                   summary=unit.content[:400], source_unit_ids=[],
                                   confidence=0.9 if unit.kind == "heading" else 0.45)
            nodes.append(active)
        active.source_unit_ids.append(unit.id)
    # Cross-links preserve many-to-many relationships without inventing source pages.
    for unit in source.units:
        if unit.kind in {"table", "figure"}:
            for node in nodes:
                if unit.id not in node.source_unit_ids and len(set(words(unit.content)) & set(words(node.title))) >= 3:
                    node.source_unit_ids.append(unit.id)
    return KnowledgeTree(nodes=nodes)
