# SOME
SOME: Singing-Oriented MIDI Extractor.
Autotune and velocity implemented by sakemin.

> WARNING
>
> This project is under beta version now. No backward compatibility is guaranteed.

## Quick Start - MIDI Extraction

### Download Pretrained Model
Download one of the following pretrained models from [releases](https://github.com/openvpi/SOME/releases):
- SOMEv0.0.1: `pretrained/0918_continuous256_clean_3spk_fixmel/model_steps_64000_simplified.ckpt`
- SOMEv1: `pretrained/0119_continuous256_5spk/model_ckpt_steps_100000_simplified.ckpt`

### Basic Usage
Run inference using the following command:
```bash
python infer.py --model [CHECKPOINT_PATH] --wav [WAV_FILE]
```

### Required Arguments
- `--model`: Path to the model checkpoint file (*.ckpt)
- `--wav`: Path to the input WAV file to analyze

### Optional Arguments
- `--midi`: Path where the output MIDI file will be saved (*.mid)
- `--tempo`: Set the tempo for the output MIDI file (default: 120 BPM)
- `--velocity`: Enable velocity calculation in the output MIDI
- `--autotune`: Enable automatic pitch correction
- `--autotune-scale`: Specify the scale for autotuning in the format `TONIC:key`
  - Tonic must be uppercase (`C`, `D`, `E`, `F`, `G`, `A`, `B`)
  - Available keys:
    - Major/Minor: `maj`, `min`
    - Modes: `ionian`, `dorian`, `phrygian`, `lydian`, `mixolydian`, `aeolian`, `locrian`
- `--scale-detection`: Enable auto scale detection

### Examples
Basic usage:
```bash
python infer.py --model pretrained/model.ckpt --wav input.wav
```

With MIDI output and custom tempo:
```bash
python infer.py --model pretrained/model.ckpt --wav input.wav --midi output.mid --tempo 140
```

With autotuning to C major:
```bash
python infer.py --model pretrained/model.ckpt --wav input.wav --autotune --autotune-scale C:maj
```

## Overview

SOME is a MIDI extractor that can convert singing voice to MIDI sequence, with the following advantages:

1. Speed: 9x faster than real-time on an i5 12400 CPU, and 300x on a 3080Ti GPU.
2. Low resource dependency: SOME can be trained on custom dataset, and can achieve good results with only 3 hours of training data.
3. Functionality: SOME can produce non-integer MIDI values, which is specially suitable for DiffSinger variance labeling.

## Installation

> 中文教程 / Chinese Tutorials: [Text](https://openvpi-docs.feishu.cn/wiki/RaHSwdMQvisdcKkRFpqclhM7ndc), [Video](https://www.bilibili.com/video/BV1my4y1N7VR)

SOME requires Python 3.8 or later. We strongly recommend you create a virtual environment via Conda or venv before installing dependencies.

1. Install PyTorch 2.1 or later following the [official instructions](https://pytorch.org/get-started/locally/) according to your OS and hardware.

2. Install other dependencies via the following command:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) For better pitch extraction results, please download the RMVPE pretrained model from [here](https://github.com/yxlllc/RMVPE/releases) and extract it into `pretrained/` directory.

## Additional Features

### Web UI Interface
To use the web interface instead of command line:
```bash
python webui.py --work_dir WORK_DIR
```
Then follow the instructions on the web page to use models under WORK_DIR.

### DiffSinger Dataset Processing
For processing DiffSinger datasets:
```bash
python batch_infer.py --model CKPT_PATH --dataset RAW_DATA_DIR --overwrite
```
This will extract MIDI sequences and update the transcriptions.csv file. Back up your files before using this feature.

### Training
_Training scripts are uploaded but may not be well-organized yet. For the best compatibility, we suggest training your own model after a stable release in the future._

## Disclaimer

Any organization or individual is prohibited from using any recordings obtained without consent from the provider as training data. If you do not comply with this item, you could be in violation of copyright laws or software EULAs.

## License

SOME is licensed under the [MIT License](LICENSE).