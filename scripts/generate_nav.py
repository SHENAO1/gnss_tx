"""
[Placeholder] NAV message generation script — not yet implemented.
See docs/next_step_review.md for planned work.

Intended future role:
  Generate real GPS L1 C/A NAV subframes from ephemeris/almanac input
  (RINEX or manual entry) and write the resulting bit stream to a file
  for injection into the transmit chain.

Usage (future):
  PYTHONPATH=src python3 scripts/generate_nav.py \
      --rinex path/to/broadcast.rnx \
      --prn 1 \
      --output results/nav/prn1_nav_bits.npy
"""
raise NotImplementedError(
    "generate_nav.py is not yet implemented. "
    "The transmitter currently uses CyclicNavBitSource (nav/nav_bits.py) "
    "as a repeating bit-pattern placeholder."
)
