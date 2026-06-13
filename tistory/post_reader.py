"""posts/ 폴더의 마크다운 글을 읽어 (제목, 본문) 으로 변환한다.

규칙:
- 파일의 첫 번째 '# 제목' 줄을 글 제목으로 사용
- 나머지 줄을 본문으로 사용
- 발행이 끝난 파일은 호출자가 posts/done/ 으로 이동시킨다
"""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

POSTS_DIR = Path(__file__).parent / "posts"
DONE_DIR = POSTS_DIR / "done"


@dataclass(frozen=True)
class Post:
    """발행 단위. 불변."""

    title: str
    body: str
    source: Path


def _parse(path: Path) -> Post:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    title = ""
    body_start = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            body_start = index + 1
            break

    if not title:
        raise ValueError(f"{path.name}: '# 제목' 형식의 제목 줄을 찾지 못했습니다.")

    body = "\n".join(lines[body_start:]).strip()
    if not body:
        raise ValueError(f"{path.name}: 본문이 비어 있습니다.")

    return Post(title=title, body=body, source=path)


def load_posts(limit: int) -> list[Post]:
    """발행 대기 중인 글을 최대 limit 개 읽어 반환한다."""
    if not POSTS_DIR.exists():
        raise FileNotFoundError(f"posts 폴더가 없습니다: {POSTS_DIR}")

    candidates = sorted(p for p in POSTS_DIR.glob("*.md") if p.is_file())

    posts: list[Post] = []
    for path in candidates[:limit]:
        try:
            posts.append(_parse(path))
        except ValueError as error:
            logger.warning("건너뜀 - %s", error)

    return posts


def mark_done(post: Post) -> None:
    """발행 완료된 원본 파일을 done 폴더로 이동한다."""
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    target = DONE_DIR / post.source.name
    post.source.rename(target)
    logger.info("이동 완료: %s -> %s", post.source.name, target)
