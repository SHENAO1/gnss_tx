"""
[Placeholder] Timebase management — not yet implemented.
See docs/next_step_review.md for planned work.

Intended future role:
  Manage GPS time-of-week, sub-frame timing, and USRP timed commands
  so that transmitted signal timing matches a real GPS epoch.
"""
raise NotImplementedError(
    "timebase is not yet implemented. "
    "Current transmitter uses GNU Radio's internal clock without GPS time alignment."
)
