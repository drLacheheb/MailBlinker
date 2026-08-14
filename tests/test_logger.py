import logging

from core import TrackerLogger, get_logger


def test_custom_logger_instance():
    log = get_logger("test_service")
    assert isinstance(log, TrackerLogger)
    assert hasattr(log, "success")


def test_json_formatter_output(caplog):
    log = get_logger("json_test_service")
    with caplog.at_level(logging.INFO):
        log.info("Test info message")
        log.success("Test success message")

    records = caplog.records
    assert len(records) >= 2
    assert records[0].levelname == "INFO"
    assert records[1].levelname == "SUCCESS"
