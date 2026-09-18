import logging
import signal
from threading import Event

from english7.core.settings import get_settings

logger = logging.getLogger(__name__)


def run_worker(stop_event: Event, poll_interval_seconds: float) -> None:
    if poll_interval_seconds <= 0:
        raise ValueError("Worker poll interval must be positive")
    logger.info("ingestion_worker_started")
    while not stop_event.wait(poll_interval_seconds):
        logger.debug("ingestion_worker_poll")


def main() -> None:
    settings = get_settings()
    interval = settings.worker_poll_interval_seconds
    if interval is None:
        raise RuntimeError("ENGLISH7_WORKER_POLL_INTERVAL_SECONDS is required")
    stop_event = Event()
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    run_worker(stop_event, interval)


if __name__ == "__main__":
    main()
