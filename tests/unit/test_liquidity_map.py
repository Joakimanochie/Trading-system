"""Test liquidity map."""
from agents.photon.liquidity_map import LiquidityPool, check_sweep, pools_in_path

def test_bsl_sweep():
    pool = LiquidityPool("BSL", 1.085, "equal_highs", None)
    assert check_sweep(pool, 1.086, 1.083, 1.084) is True
    assert pool.swept is False  # check_sweep doesn't mutate

def test_ssl_sweep():
    pool = LiquidityPool("SSL", 1.080, "equal_lows", None)
    assert check_sweep(pool, 1.082, 1.079, 1.081) is True

def test_no_sweep():
    pool = LiquidityPool("BSL", 1.085, "equal_highs", None)
    assert check_sweep(pool, 1.084, 1.082, 1.083) is False

def test_pools_in_path():
    pools = [
        LiquidityPool("BSL", 1.090, "swing_high", None),
        LiquidityPool("BSL", 1.095, "swing_high", None, swept=True),
        LiquidityPool("SSL", 1.075, "swing_low", None),
    ]
    result = pools_in_path(pools, entry=1.085, target=1.100)
    assert len(result) == 1
    assert result[0].price == 1.090
