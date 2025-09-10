from pathlib import Path
from datetime import date

from signalai.logging import get_logger
from signalai.models import IssueFinal


logger = get_logger(__name__)

def write(issue: IssueFinal, out_dir: Path):
    today = date.today().isoformat()
    mdpath = out_dir / f"newsletter_{today}.md"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(mdpath, "w", encoding="utf-8") as f:
        f.write(issue.markdown)

    logger.info("Wrote newsletter to %s with %d words.", mdpath, issue.word_count)
