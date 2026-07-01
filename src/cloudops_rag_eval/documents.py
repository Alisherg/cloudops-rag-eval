import re
from dataclasses import dataclass
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)]\([^)]+\)")
MARKDOWN_TOKEN_RE = re.compile(r"[*_`|]")


@dataclass(frozen=True, slots=True)
class Section:
    title: str
    content: str


@dataclass(frozen=True, slots=True)
class SourceDocument:
    document_id: str
    title: str
    path: Path
    sections: tuple[Section, ...]


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    document_title: str
    section_title: str
    text: str


def load_documents(docs_path: Path) -> list[SourceDocument]:
    if not docs_path.exists():
        raise FileNotFoundError(f"Document path does not exist: {docs_path}")

    documents = [parse_document(path) for path in sorted(docs_path.glob("*.md"))]
    if not documents:
        raise ValueError(f"No markdown documents found in {docs_path}")

    return documents


def parse_document(path: Path) -> SourceDocument:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    title = _extract_title(lines, path)
    sections = _extract_sections(lines, title)
    return SourceDocument(
        document_id=_document_id(path),
        title=title,
        path=path,
        sections=tuple(sections),
    )


def chunk_documents(documents: list[SourceDocument]) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document in documents:
        for index, section in enumerate(document.sections, start=1):
            text = clean_markdown(section.content)
            if not text:
                continue
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document.document_id}:{index}",
                    document_id=document.document_id,
                    document_title=document.title,
                    section_title=section.title,
                    text=text,
                )
            )
    return chunks


def clean_markdown(value: str) -> str:
    value = MARKDOWN_LINK_RE.sub(r"\1", value)
    value = MARKDOWN_TOKEN_RE.sub("", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _document_id(path: Path) -> str:
    return re.sub(r"^\d+-", "", path.stem).replace("_", "-")


def _extract_title(lines: list[str], path: Path) -> str:
    for line in lines:
        match = HEADING_RE.match(line)
        if match and match.group(1) == "#":
            return match.group(2).strip()
    return path.stem.replace("-", " ").title()


def _extract_sections(lines: list[str], fallback_title: str) -> list[Section]:
    sections: list[Section] = []
    current_title = fallback_title
    current_lines: list[str] = []

    def flush() -> None:
        text = "\n".join(current_lines).strip()
        current_lines.clear()
        if text:
            sections.append(Section(title=current_title, content=text))

    for line in lines:
        match = HEADING_RE.match(line)
        if match:
            level, title = match.groups()
            if level == "#":
                continue
            flush()
            current_title = title.strip()
            continue
        current_lines.append(line)

    flush()
    return sections or [Section(title=fallback_title, content="\n".join(lines))]
