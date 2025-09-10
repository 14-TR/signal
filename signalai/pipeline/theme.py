from typing import List, Dict
from signalai.models import Item

THEME_KEYWORDS = {
    "Agents & Orchestration": ["agent", "orchestr"],
    "Model Efficiency (Pruning/Distill/Latency)": ["pruning", "distill", "latency", "throughput"],
    "Evaluation & QA": ["evaluation", "eval", "benchmark"],
    "Multimodal & VLM": ["multimodal", "vision", "vlm", "image"],
    "Safety & Alignment": ["safety", "alignment", "rlhf", "dpo"],
}

def detect(items: List[Item]) -> Dict[str, bool]:
    text_join = lambda it: (it.title + " " + it.summary).lower()
    cat = lambda keys: any(any(k in text_join(it) for k in keys) for it in items)
    
    themes = {
        name: cat(keywords) for name, keywords in THEME_KEYWORDS.items()
    }
    return themes
