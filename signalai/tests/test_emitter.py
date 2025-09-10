from datetime import date
from pathlib import Path

from signalai.models import IssueFinal
from signalai.pipeline import emitter


def test_write_creates_markdown_file(tmp_path):
    issue = IssueFinal(markdown="# Hello", word_count=2, links_checked=False)
    emitter.write(issue, Path(tmp_path))
    mdfile = Path(tmp_path) / f"newsletter_{date.today().isoformat()}.md"
    assert mdfile.exists()
    assert mdfile.read_text(encoding="utf-8") == "# Hello"
