"""
[Placeholder] True GPS NAV subframe construction — not yet implemented.
See docs/next_step_review.md for planned work.

Intended future role:
  Build real GPS L1 C/A NAV subframes (300 bits / 6 s) from broadcast
  ephemeris + almanac data, replacing the cyclic bit pattern in nav_bits.py.
"""
raise NotImplementedError(
    "subframe_builder is not yet implemented. "
    "Use nav.nav_bits.CyclicNavBitSource for the current cyclic-pattern source."
)
