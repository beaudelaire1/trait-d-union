from io import StringIO
from unittest.mock import Mock, patch

import pytest

from apps.portfolio.services.audit import CategoryScore, ProjectAudit, _audit_pagespeed
from apps.portfolio.management.commands.audit_portfolio_projects import Command


def response(score):
    return Mock(status_code=200, json=Mock(return_value={
        "loadingExperience": {
            "overall_category": "AVERAGE",
            "metrics": {"lcp": {}, "cls": {}, "inp": {}},
        },
        "lighthouseResult": {"categories": {
            "performance": {"score": score},
            "seo": {"score": score},
        }},
    }))


def test_best_lighthouse_score_overrides_crux_and_median():
    session = Mock()
    session.get.side_effect = [response(.75), response(.98), response(.85)]
    with patch("apps.portfolio.services.audit._Session", return_value=session):
        result = _audit_pagespeed("https://example.com")
    assert result["performance"].score == 98
    assert result["seo"].score == 85
    assert session.get.call_count == 3


def test_partial_failure_preserves_successful_maximum():
    session = Mock()
    session.get.side_effect = [response(.98), TimeoutError(), response(.75)]
    with patch("apps.portfolio.services.audit._Session", return_value=session):
        result = _audit_pagespeed("https://example.com")
    assert result["performance"].score == 98


@pytest.mark.parametrize("previous,current,expected", [
    (98, 75, 98), (75, 98, 98), (98, None, 98), (None, 98, 98), (0, None, 0),
])
def test_command_keeps_record_and_updates_other_categories(previous, current, expected):
    old = {"score": previous, "measured_at": "2026-01-01"} if previous is not None else {}
    project = Mock(audit_results={"performance": old, "ui_ux": {"score": 90}})
    projects = Mock()
    projects.count.return_value = 1
    projects.__iter__ = Mock(return_value=iter([project]))
    audit = ProjectAudit(
        performance=CategoryScore(score=current, measured_at="2026-09-10"),
        seo=CategoryScore(score=80),
    )
    with patch("apps.portfolio.models.Project.objects") as manager, patch(
        "apps.portfolio.services.audit.audit_project", return_value=audit
    ):
        manager.filter.return_value.exclude.return_value = projects
        Command(stdout=StringIO()).handle(slug=None, only_missing=False, no_ssl=True)
    assert project.audit_results["performance"]["score"] == expected
    if previous is not None and (current is None or previous > current):
        assert project.audit_results["performance"] == old
    assert project.audit_results["seo"]["score"] == 80
    assert project.audit_results["ui_ux"]["score"] == 90
    project.save.assert_called_once()
