from app.monetization.config import CAP_CONFIG, cap_after_unlocks


def test_default_free_cap():
    assert CAP_CONFIG.free_cap == 25


def test_cap_progression():
    # 25 (free) -> 50 -> 75 -> 100 ...
    assert cap_after_unlocks(0) == 25
    assert cap_after_unlocks(1) == 50
    assert cap_after_unlocks(2) == 75
    assert cap_after_unlocks(3) == 100
