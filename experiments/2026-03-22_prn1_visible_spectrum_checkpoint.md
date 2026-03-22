# PRN1 Visible Spectrum Checkpoint

- Date: `2026-03-22`
- Signal mode: `spread`
- Result: `visible wideband PRN1 envelope observed on the spectrum analyzer`

## TX configuration

- Config profile: [`configs/tx_b210_visible_spectrum.yaml`](/home/shen/projects/gnss_tx/configs/tx_b210_visible_spectrum.yaml)
- `center_freq = 100 MHz`
- `sample_rate = 4.092 Msps`
- `samples_per_chip = 4`
- `tx_gain = 10.0`
- `amplitude = 0.5`
- `antenna = TX/RX`

## Spectrum analyzer settings observed

- `Center = 100 MHz`
- `Span = 5 MHz`
- `RBW = 1 kHz`
- `VBW = 1 kHz`
- `Att = 10 dB`
- `Ref Level = -66 dBm`

## Observation summary

- A stable wideband envelope became visible around `100 MHz`
- The result confirms the B210-to-analyzer RF chain is working for the PRN1 spread replay
- This profile is suitable as a reproducible visibility checkpoint before finer sweeps

## Screenshot

- External analyzer screenshot captured in this session
- Recommended local filename: `results/figs/2026-03-22_prn1_visible_spectrum.png`

## Next step

- Sweep `tx_gain` over `6, 8, 10, 12`
- Sweep `amplitude` over `0.30, 0.40, 0.50, 0.60`
- Keep `center_freq`, `sample_rate`, cable path, and analyzer settings fixed for comparability
