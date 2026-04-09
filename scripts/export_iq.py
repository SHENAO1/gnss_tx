"""
[Placeholder] IQ data file export script — not yet implemented.
See docs/next_step_review.md for planned work.

Intended future role:
  Export the pre-generated baseband replay buffer to standard IQ file
  formats (complex64 binary, SigMF, or GNU Radio IQ) for offline analysis
  or import into other tools (MATLAB, SDR#, etc.).

Usage (future):
  PYTHONPATH=src python3 scripts/export_iq.py \
      --config configs/tx_b210.yaml \
      --output results/iq/prn1_40ms.c64
"""
raise NotImplementedError(
    "export_iq.py is not yet implemented. "
    "Use scripts/analyze_prn1_spread.py to export NPY arrays for now."
)
