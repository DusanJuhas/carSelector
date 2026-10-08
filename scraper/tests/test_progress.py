import json

from scraper.progress import PREFIX, report_progress


def test_report_progress_prints_one_machine_readable_line(capsys) -> None:
    report_progress(7, 20, "skoda", 3, 12)
    report_progress(8, 20, "kia")

    first, second = capsys.readouterr().out.splitlines()
    assert first.startswith(PREFIX)
    assert json.loads(first[len(PREFIX) :]) == {"step": 7, "steps": 20, "item": "skoda", "sub": 3, "subs": 12}
    assert json.loads(second[len(PREFIX) :]) == {"step": 8, "steps": 20, "item": "kia"}
