# Spectrum Analyzer Observation Guide

This project currently transmits a buffered replay of the PRN1 GPS L1 C/A spread-spectrum baseband signal through the B210.

## Recommended profiles

- Safe baseline: [`configs/tx_b210.yaml`](/home/shen/projects/gnss_tx/configs/tx_b210.yaml)
- Visible-spectrum checkpoint: [`configs/tx_b210_visible_spectrum.yaml`](/home/shen/projects/gnss_tx/configs/tx_b210_visible_spectrum.yaml)

The baseline profile should remain conservative. Use the visible-spectrum profile when you want to reproduce the already observed wideband envelope.

## Recommended troubleshooting order

If the analyzer still shows only noise in spread-spectrum mode, switch to a single-tone calibration mode first:

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
  --config configs/tx_b210.yaml \
  --signal-mode tone \
  --tone-offset-hz 500000 \
  --duration 5
```

With `center_freq = 100 MHz` and `tone_offset_hz = 500 kHz`, look for a narrow tone near `100.5 MHz`.
If the tone is visible but the spread signal is not, the RF chain is fine and the remaining problem is analyzer sensitivity / viewing settings for a noise-like signal.

## First RF observation

1. Do not start transmission while the analyzer is still in an unknown state.
2. Configure the analyzer input for `50 ohm`.
3. Keep front-end protection enabled:
   - high reference level
   - input attenuation on
4. Connect the B210 `TX/RX` port to the analyzer with a coax cable.
5. Use the low-risk transmit profile from [`configs/tx_b210.yaml`](/home/shen/projects/gnss_tx/configs/tx_b210.yaml):
   - `center_freq = 100 MHz`
   - `sample_rate = 4.092 Msps`
   - `samples_per_chip = 4`
   - `tx_gain = 0.0`
   - `amplitude = 0.25`

## Analyzer settings

- Center frequency: `100 MHz`
- Start with a wide span: `20 MHz` or `10 MHz`
- After the signal is found, narrow the span to `5 MHz`, then `2 MHz` if needed
- Start with wider `RBW/VBW`
- Reduce `RBW` only after the signal is clearly visible

## What success looks like

- A continuous wideband spectrum appears near `100 MHz` during transmission
- The spectrum is not a narrow single-tone spike
- The signal disappears when transmission stops
- In tone-calibration mode, a narrow peak appears near `100.5 MHz` and disappears when transmission stops

## Safety reminder

- Analyzer input max: `30 dBm`
- Analyzer DC max: `50 V`
- Without an external attenuator, do not increase `tx_gain` or `amplitude` until the first low-power observation is confirmed safe

## Experiment logging

- Checkpoint record: [`experiments/2026-03-22_prn1_visible_spectrum_checkpoint.md`](/home/shen/projects/gnss_tx/experiments/2026-03-22_prn1_visible_spectrum_checkpoint.md)
- Observation template: [`experiments/observation_log_template.md`](/home/shen/projects/gnss_tx/experiments/observation_log_template.md)
- Sweep template: [`experiments/tx_visibility_sweep_template.csv`](/home/shen/projects/gnss_tx/experiments/tx_visibility_sweep_template.csv)
