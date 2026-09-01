import pytest
from ai.retrieval.product_resolver import ProductResolver, resolve_product


def test_product_resolver_exact_match():
    res = resolve_product("tmt bars")
    assert res is not None
    assert res["standard_number"] == "IS 1786"
    assert res["confidence"] >= 0.95


def test_product_resolver_subphrase_match():
    res = resolve_product("Which standard specifies ceiling fans for household use?")
    assert res is not None
    assert res["standard_number"] == "IS 374"


def test_product_resolver_ranked_candidates():
    resolver = ProductResolver.get_instance()
    cands = resolver.resolve_candidates("steel bars and concrete reinforcement", top_k=3)
    assert len(cands) >= 1
    assert any(c["standard_number"] == "IS 1786" for c in cands)
