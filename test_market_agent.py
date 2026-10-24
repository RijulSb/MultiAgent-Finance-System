"""Deterministic Batch 2 fixtures.

These tests avoid live provider calls. Run with:
    pytest -q test_market_agent.py
"""

from datetime import date, datetime, timedelta, timezone

import market_agent as app


UTC = timezone.utc


def bars(count: int) -> list[app.PriceBar]:
    start = date(2026, 1, 2)
    return [app.PriceBar(start + timedelta(days=i), float(100 + i), float(100 + i)) for i in range(count)]


def test_five_session_change_uses_six_valid_closes() -> None:
    result = app.compute_metrics(bars(6))
    assert result.observation_count == 6
    assert result.five_session_start == date(2026, 1, 2)
    assert result.end_date == date(2026, 1, 7)
    assert result.five_session_change_pct == (105 / 100 - 1) * 100
    assert result.twenty_session_change_pct is None


def test_twenty_session_change_uses_twenty_one_valid_closes() -> None:
    result = app.compute_metrics(bars(21))
    assert result.twenty_session_start == date(2026, 1, 2)
    assert result.twenty_session_change_pct == (120 / 100 - 1) * 100


def test_boundary_lengths_leave_unavailable_metrics_null() -> None:
    five_boundary = app.compute_metrics(bars(5))
    twenty_boundary = app.compute_metrics(bars(20))
    assert five_boundary.five_session_change_pct is None
    assert five_boundary.twenty_session_change_pct is None
    assert twenty_boundary.five_session_change_pct is not None
    assert twenty_boundary.twenty_session_change_pct is None


def test_unsorted_bars_are_sorted_before_session_comparison() -> None:
    ordered = bars(6)
    result = app.compute_metrics(list(reversed(ordered)))
    assert result.five_session_start == ordered[0].session_date
    assert result.end_date == ordered[-1].session_date


def test_flat_adjusted_prices_produce_exact_zero_return() -> None:
    flat = [app.PriceBar(date(2026, 1, 2) + timedelta(days=i), 100.0, 101.0) for i in range(21)]
    result = app.compute_metrics(flat)
    assert result.five_session_change_pct == 0.0
    assert result.twenty_session_change_pct == 0.0
    assert result.latest_close == 101.0


def test_returns_use_adjusted_close_not_quoted_close() -> None:
    fixture = [
        app.PriceBar(date(2026, 1, 2), 100.0, 200.0),
        *[app.PriceBar(date(2026, 1, 3) + timedelta(days=i), 100.0, 200.0) for i in range(5)],
    ]
    result = app.compute_metrics(fixture)
    assert result.five_session_change_pct == 0.0
    assert result.latest_close == 200.0
    assert "adjusted_close" in (result.return_basis or "")


def test_non_finite_prices_are_rejected() -> None:
    invalid = bars(6)
    invalid[-1] = app.PriceBar(invalid[-1].session_date, float("nan"))
    try:
        app.compute_metrics(invalid)
    except ValueError as exc:
        assert "invalid" in str(exc)
    else:
        raise AssertionError("non-finite close was accepted")


def test_invalid_or_duplicate_history_is_rejected() -> None:
    duplicate = bars(6)
    duplicate[-1] = app.PriceBar(duplicate[-2].session_date, 105.0)
    try:
        app.compute_metrics(duplicate)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate session was accepted")

    invalid = bars(6)
    invalid[-1] = app.PriceBar(invalid[-1].session_date, 0.0)
    try:
        app.compute_metrics(invalid)
    except ValueError as exc:
        assert "invalid" in str(exc)
    else:
        raise AssertionError("non-positive close was accepted")


def test_news_results_are_bounded_deduplicated_and_time_filtered(monkeypatch) -> None:
    class FakeDDGS:
        def text(self, query: str, max_results: int):
            assert "MSFT" in query
            assert max_results == 10
            return [
                {"title": "Recent result", "href": "https://Example.com/news#fragment", "date": "2026-10-20T10:00:00+00:00", "body": "A <b>bounded</b> snippet."},
                {"title": "Recent result", "href": "https://example.com/news", "date": "2026-10-20T10:00:00+00:00", "body": "duplicate"},
                {"title": "Old result", "href": "https://example.com/old", "date": "2020-01-01T00:00:00+00:00", "body": "old"},
                {"title": "Undated result", "href": "https://example.com/undated", "body": "undated"},
            ]

    monkeypatch.setattr(app, "DDGS", FakeDDGS)
    result = app.search_company_news("MSFT", "MSFT", 7)
    assert result.status == "ok"
    assert len(result.items) == 1
    assert result.items[0].url == "https://example.com/news"
    assert result.items[0].snippet == "A bounded snippet."


def test_review_rejects_unknown_ids_and_causal_assertions() -> None:
    registry = app.EvidenceRegistry("req_fixture")
    registry.register(app.Source(
        source_id="src_1",
        provider="fixture",
        retrieved_at=datetime.now(UTC),
        evidence_granularity="fixture",
        content_hash="hash",
    ))
    result = app.review_claims(registry, [
        app.Claim(text="The news caused the price rise", source_ids=["src_1"], evidence_level="interpretation"),
        app.Claim(text="Unsupported", source_ids=["invented"], evidence_level="reported"),
    ])
    assert result.status == "rejected"
    assert any("unknown evidence" in issue for issue in result.issues)
    assert any("causal" in issue for issue in result.issues)


def test_filter_reviewed_claims_removes_rejected_claims() -> None:
    registry = app.EvidenceRegistry("req_filter")
    registry.register(app.Source(
        source_id="src_valid",
        provider="fixture",
        retrieved_at=datetime.now(UTC),
        evidence_granularity="fixture",
        content_hash="hash",
    ))
    accepted, review = app.filter_reviewed_claims(registry, [
        app.Claim(text="Valid reported fact", source_ids=["src_valid"], evidence_level="reported"),
        app.Claim(text="The event caused the rise", source_ids=["src_valid"], evidence_level="interpretation"),
        app.Claim(text="Invented source", source_ids=["unknown"], evidence_level="reported"),
    ])
    assert [claim.text for claim in accepted] == ["Valid reported fact"]
    assert review.status == "rejected"


def test_synthesis_validation_filters_claims_again() -> None:
    registry = app.EvidenceRegistry("req_synthesis")
    registry.register(app.Source(
        source_id="src_valid",
        provider="fixture",
        retrieved_at=datetime.now(UTC),
        evidence_granularity="fixture",
        content_hash="hash",
    ))
    synthesis = app.SynthesisResponse(
        summary="Grounded summary",
        reported_developments=[
            app.Claim(text="Grounded fact", source_ids=["src_valid"], evidence_level="reported"),
            app.Claim(text="Unsupported", source_ids=["invented"], evidence_level="reported"),
        ],
    )
    filtered, review = app.validate_synthesis(registry, synthesis)
    assert [claim.text for claim in filtered.reported_developments] == ["Grounded fact"]
    assert review.status == "rejected"


def test_specialist_receipts_require_all_three_framework_names() -> None:
    complete = {"member_responses": [
        {"agent_name": "Market Analyst"},
        {"agent_name": "News Researcher"},
        {"agent_name": "Evidence Reviewer"},
    ]}
    receipts = app.extract_specialist_receipts(complete)
    assert [receipt.status for receipt in receipts] == ["observed", "observed", "observed"]

    incomplete = {"member_responses": [{"agent_name": "Market Analyst"}]}
    receipts = app.extract_specialist_receipts(incomplete)
    assert [receipt.status for receipt in receipts] == ["observed", "missing", "missing"]
