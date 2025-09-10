import importlib
import logging

import signalai.logging as slog


def test_get_logger_single_handler():
    root = logging.getLogger()
    root.handlers.clear()
    module = importlib.reload(slog)

    logger1 = module.get_logger("a")
    handlers_after_first = len(root.handlers)
    logger2 = module.get_logger("b")
    handlers_after_second = len(root.handlers)

    assert logger1.name == "a"
    assert logger2.name == "b"
    assert handlers_after_first == handlers_after_second == 1
