# Docker Deployment for SOME

This guide explains how to run SOME (Singing-Oriented MIDI Extractor) in a Docker container.

## Prerequisites

- Docker installed on your system

## Quick Start

### 1. Build the Docker image

```bash
docker build -t some .
```

This will download and include the pretrained model checkpoints automatically.

### 2. Prepare directories

Create directories for input and output files:

```bash
mkdir -p input output
```

### 3. Run inference

```bash
docker run --rm \
  -v "$(pwd)/input:/app/input" \
  -v "$(pwd)/output:/app/output" \
  some \
  --model pretrained/0918_continuous256_clean_3spk_fixmel/model_steps_64000_simplified.ckpt \
  --wav input/your_audio_file.wav \
  --midi output/result.mid \
  --autotune --scale-detection
```

Replace `your_audio_file.wav` with your input file (placed in the `input` directory).

## Using Custom File Paths

### Method 1: Specifying Different Filenames Within Mounted Volumes

You can specify different filenames within the input and output directories:

```bash
docker run --rm \
  -v "$(pwd)/input:/app/input" \
  -v "$(pwd)/output:/app/output" \
  some \
  --model pretrained/0918_continuous256_clean_3spk_fixmel/model_steps_64000_simplified.ckpt \
  --wav input/custom_filename.wav \
  --midi output/custom_result.mid \
  --autotune --scale-detection
```

### Method 2: Mounting Different Host Directories

You can mount different host directories to the container's input and output paths:

```bash
docker run --rm \
  -v "/path/to/my/audio/files:/app/input" \
  -v "/path/to/my/midi/results:/app/output" \
  some \
  --model pretrained/0918_continuous256_clean_3spk_fixmel/model_steps_64000_simplified.ckpt \
  --wav input/song.wav \
  --midi output/song.mid \
  --autotune --scale-detection
```

### Method 3: Using Additional Volumes for Custom Paths

You can also mount additional volumes for specific files:

```bash
docker run --rm \
  -v "/path/to/specific/audio.wav:/app/custom/audio.wav" \
  -v "/path/to/save/result.mid:/app/custom/result.mid" \
  some \
  --model pretrained/0918_continuous256_clean_3spk_fixmel/model_steps_64000_simplified.ckpt \
  --wav /app/custom/audio.wav \
  --midi /app/custom/result.mid \
  --autotune --scale-detection
```

## Included Models

The Docker image includes the following pretrained models:

1. SOMEv0.0.1 (3 speakers): 
   ```
   pretrained/0918_continuous256_clean_3spk_fixmel/model_steps_64000_simplified.ckpt
   ```

2. SOMEv1 (5 speakers): 
   ```
   pretrained/0119_continuous128_5spk/model_ckpt_steps_100000_simplified.ckpt
   ```

3. RMVPE Pitch Extraction model:
   ```
   pretrained/rmvpe.pt
   ```
   This model enhances the pitch extraction results.

## Using docker-compose

Alternatively, you can use docker-compose for easier management:

1. Edit the `command` in `docker-compose.yml` to match your desired parameters.
2. Run:

```bash
docker-compose up
```

## Available Options

The container accepts all the same parameters as the original SOME application:

- `--model`: Path to the model checkpoint file (*.ckpt)
- `--wav`: Path to the input WAV file to analyze
- `--midi`: Path where the output MIDI file will be saved (*.mid)
- `--tempo`: Set the tempo for the output MIDI file (default: 120 BPM)
- `--velocity`: Enable velocity calculation in the output MIDI
- `--autotune`: Enable automatic pitch correction
- `--autotune-scale`: Specify the scale for autotuning (format: `TONIC:key`)
- `--scale-detection`: Enable auto scale detection
- `--compress`: Enable compressor applied to the input wav 