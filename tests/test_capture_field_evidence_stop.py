import importlib.util
import signal
import threading
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "capture_field_evidence.py"
spec = importlib.util.spec_from_file_location("capture_field_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_install_stop_handlers_stops_capture_and_marks_interrupted(monkeypatch):
    stop = threading.Event()
    interrupted = threading.Event()
    handlers = {}
    previous = {signal.SIGINT: object(), signal.SIGTERM: object()}

    monkeypatch.setattr(module.signal, "getsignal", lambda sig: previous[sig])
    monkeypatch.setattr(module.signal, "signal", lambda sig, handler: handlers.setdefault(sig, handler))

    old_sigint, old_sigterm = module.install_stop_handlers(stop, interrupted)

    assert old_sigint is previous[signal.SIGINT]
    assert old_sigterm is previous[signal.SIGTERM]
    assert set(handlers) == {signal.SIGINT, signal.SIGTERM}

    handlers[signal.SIGINT](signal.SIGINT, None)

    assert stop.is_set()
    assert interrupted.is_set()
