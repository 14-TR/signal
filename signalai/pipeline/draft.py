from datetime import date
from typing import List, Tuple, Dict
from signalai.models import Item, IssueDraft

def build(
    top_items: List[Item],
    bullets: List[Tuple[Item, str]],
    impacts_md: str,
    themes: Dict[str, bool],
) -> IssueDraft:
    return IssueDraft(
        date=date.today(),
        top_signals=top_items,
        bullets=bullets,
        impacts_md=impacts_md,
        themes=themes,
    )
