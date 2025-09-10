from pathlib import Path
from datetime import date
from signalai.models import IssueFinal

def write(issue: IssueFinal, out_dir: Path):
    today = date.today().isoformat()
    mdpath = out_dir / f"newsletter_{today}.md"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(mdpath, "w", encoding="utf-8") as f:
        f.write(issue.markdown)
    
    print(f"Wrote newsletter to {mdpath} with {issue.word_count} words.")
