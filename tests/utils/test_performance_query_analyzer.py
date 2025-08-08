import types


def _fake_query(sql: str):
    class Compiled:
        def __init__(self, s: str):
            self._s = s

        def __str__(self) -> str:
            return self._s

    class Q:
        def compile(self, compile_kwargs):  # type: ignore[no-untyped-def]
            return Compiled(sql)

    return Q()


def test_query_analyzer_select_star_high_cost_and_suggestion():
    from app.utils.performance import QueryAnalyzer

    qa = QueryAnalyzer(session=types.SimpleNamespace())
    q = _fake_query("SELECT * FROM users")
    out = qa.analyze_query(q)
    assert out["estimated_cost"].startswith("HIGH")
    assert any("SELECT *" in s for s in out["suggestions"])  # suggest column names


def test_query_analyzer_order_by_without_limit_medium_cost_and_suggestion():
    from app.utils.performance import QueryAnalyzer

    qa = QueryAnalyzer(session=types.SimpleNamespace())
    q = _fake_query("SELECT id FROM users ORDER BY created_at DESC")
    out = qa.analyze_query(q)
    assert out["estimated_cost"].startswith("MEDIUM")
    assert any("LIMIT" in s for s in out["suggestions"])  # suggest adding LIMIT


def test_query_analyzer_join_without_where_medium_cost_and_suggestion():
    from app.utils.performance import QueryAnalyzer

    qa = QueryAnalyzer(session=types.SimpleNamespace())
    q = _fake_query("SELECT u.id FROM users u JOIN posts p ON p.user_id = u.id")
    out = qa.analyze_query(q)
    assert out["estimated_cost"].startswith("MEDIUM")
    assert any("WHERE" in s for s in out["suggestions"])  # suggest WHERE clause


def test_query_analyzer_like_leading_wildcard_suggestion_only():
    from app.utils.performance import QueryAnalyzer

    qa = QueryAnalyzer(session=types.SimpleNamespace())
    q = _fake_query("SELECT id FROM users WHERE name LIKE '%pattern'")
    out = qa.analyze_query(q)
    assert any("leading wildcards" in s for s in out["suggestions"])  # LIKE suggestion


def test_query_analyzer_low_cost_default():
    from app.utils.performance import QueryAnalyzer

    qa = QueryAnalyzer(session=types.SimpleNamespace())
    q = _fake_query("SELECT id FROM users LIMIT 10")
    out = qa.analyze_query(q)
    assert out["estimated_cost"].startswith("LOW")
