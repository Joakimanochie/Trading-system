"""CRT high-probability filters: PD array, session macro, premium/discount, nested LTF, MSS+FVG."""
from __future__ import annotations

from dataclasses import dataclass

from agents.crt.anchor import AnchorCandle
from agents.crt.nested_crt import NestedCRTResult
from agents.crt.mss_detector import MSSResult


@dataclass
class CRTFilterResult:
    pd_array: bool
    session_macro: bool
    premium_discount: bool
    nested_ltf: bool
    mss_fvg: bool
    passed_count: int

    @property
    def all_passed(self) -> bool:
        return self.passed_count == 5


def evaluate_filters(
    anchor: AnchorCandle,
    direction: str,
    entry_price: float,
    nested: NestedCRTResult,
    mss: MSSResult,
    in_session: bool = True,
) -> CRTFilterResult:
    """Evaluate all 5 CRT filters."""
    # 1. PD Array: is entry near a key level (anchor high/low/eq)?
    rng = anchor.crt_high - anchor.crt_low
    if direction == "LONG":
        pd_array = entry_price <= anchor.crt_low + rng * 0.25
    else:
        pd_array = entry_price >= anchor.crt_high - rng * 0.25

    # 2. Session macro: is the signal during a key session window?
    session_macro = in_session

    # 3. Premium/discount: LONG entries should be in discount (below EQ), SHORT in premium
    if direction == "LONG":
        premium_discount = entry_price < anchor.crt_eq
    else:
        premium_discount = entry_price > anchor.crt_eq

    # 4. Nested LTF CRT detected?
    nested_ltf = nested.detected

    # 5. MSS with FVG confirmed on LTF?
    mss_fvg = mss.detected and mss.fvg_high is not None

    passed = sum([pd_array, session_macro, premium_discount, nested_ltf, mss_fvg])

    return CRTFilterResult(
        pd_array=pd_array,
        session_macro=session_macro,
        premium_discount=premium_discount,
        nested_ltf=nested_ltf,
        mss_fvg=mss_fvg,
        passed_count=passed,
    )
