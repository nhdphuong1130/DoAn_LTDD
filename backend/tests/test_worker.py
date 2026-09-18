from english7.worker import run_worker


class TwoPollEvent:
    def __init__(self) -> None:
        self.polls = 0

    def wait(self, _seconds):
        self.polls += 1
        return self.polls > 1


def test_worker_dispatches_one_queued_upload_per_poll() -> None:
    processed = []

    run_worker(TwoPollEvent(), 0.1, process_once=lambda: processed.append(True))

    assert processed == [True]
