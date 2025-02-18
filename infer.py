import importlib
import pathlib

import click
import librosa
import yaml

import inference
from utils.config_utils import print_config
from utils.infer_utils import build_midi_file
from utils.slicer2 import Slicer
import pitch_correction_utils
from functools import partial

@click.command(help='Run inference with a trained model')
@click.option('--model', required=True, metavar='CKPT_PATH', default='pretrained/0918_continuous256_clean_3spk_fixmel/model_steps_64000_simplified.ckpt', help='Path to the model checkpoint (*.ckpt)')
@click.option('--wav', required=True, metavar='WAV_PATH', help='Path to the input wav file (*.wav)')
@click.option('--midi', required=False, metavar='MIDI_PATH', help='Path to the output MIDI file (*.mid)')
@click.option('--tempo', required=False, type=float, default=120, metavar='TEMPO', help='Specify tempo in the output MIDI')
@click.option('--velocity', required=False, is_flag=True, type=bool, default=False, metavar='VELOCITY', help='Enable velocity calculation')
@click.option('--autotune', required=False, is_flag=True, type=bool, default=False, metavar='AUTOTUNE', help='Enable autotune')
@click.option('--autotune-scale', required=False, type=str, default=None, metavar='AUTOTUNE_SCALE', help='Specify autotune scale; Must be in the form TONIC:key. Tonic must be upper case (`CDEFGAB`), key must be lower-case (`maj`, `min`, `ionian`, `dorian`, `phrygian`, `lydian`, `mixolydian`, `aeolian`, `locrian`).')
def infer(model, wav, midi, tempo, velocity, autotune, autotune_scale):
    model_path = pathlib.Path(model)
    with open(model_path.with_name('config.yaml'), 'r', encoding='utf8') as f:
        config = yaml.safe_load(f)
    print_config(config)
    infer_cls = inference.task_inference_mapping[config['task_cls']]

    pkg = ".".join(infer_cls.split(".")[:-1])
    cls_name = infer_cls.split(".")[-1]
    infer_cls = getattr(importlib.import_module(pkg), cls_name)
    assert issubclass(infer_cls, inference.BaseInference), \
        f'Inference class {infer_cls} is not a subclass of {inference.BaseInference}.'
    infer_ins = infer_cls(config=config, model_path=model_path)

    wav_path = pathlib.Path(wav)
    waveform, sr = librosa.load(wav_path, sr=config['audio_sample_rate'], mono=True)
    if autotune:
        if autotune_scale is None:
            correction_function = pitch_correction_utils.closest_pitch
        else:
            correction_function = partial(pitch_correction_utils.aclosest_pitch_from_scale, scale=autotune_scale)
        waveform = pitch_correction_utils.autotune(waveform, sr, correction_function)
        waveform = waveform.astype('float32')

    slicer = Slicer(sr=config['audio_sample_rate'], max_sil_kept=1000)
    chunks = slicer.slice(waveform)
    
    if velocity:
        midis = infer_ins.infer([c['waveform'] for c in chunks], waveform=waveform) # waveform for velocity
    else:
        midis = infer_ins.infer([c['waveform'] for c in chunks])

    midi_file = build_midi_file([c['offset'] for c in chunks], midis, tempo=tempo)

    midi_path = pathlib.Path(midi) if midi is not None else wav_path.with_suffix('.mid')
    midi_file.save(midi_path)
    print(f'MIDI file saved at: \'{midi_path}\'')


if __name__ == '__main__':
    infer()
