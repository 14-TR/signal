from typing import Protocol, List, Dict, Any
from signalai.models import Item

class SourceFetcher(Protocol):
    def fetch(self, feed_cfg: Dict[str, Any]) -> List[Item]:
        ...
