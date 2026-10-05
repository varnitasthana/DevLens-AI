from dataclasses import dataclass


@dataclass(frozen=True)
class ContextChunk:
    file: str
    content: str


def build_context(files: dict[str, str], max_file_chars: int = 12_000, max_total_chars: int = 40_000) -> list[ContextChunk]:
    chunks: list[ContextChunk] = []
    total = 0
    for file_name, content in files.items():
        if not file_name.endswith((".py", ".js", ".jsx", ".ts", ".tsx")):
            continue
        if total >= max_total_chars:
            break
        remaining = max_total_chars - total
        excerpt = content[: min(max_file_chars, remaining)]
        chunks.append(ContextChunk(file_name, excerpt))
        total += len(excerpt)
    return chunks


def render_context(chunks: list[ContextChunk]) -> str:
    return "\n\n".join(f"FILE: {chunk.file}\n```text\n{chunk.content}\n```" for chunk in chunks)
