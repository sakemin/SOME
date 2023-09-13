import random

import torch
import torch.nn.functional as F
from torch import nn

import modules.losses
from utils import build_object_from_class_name, collate_nd
from .base_task import BaseDataset, BaseTask
from utils.infer_utils import decode_gaussian_blurred_probs, decode_bounds_to_sequence
from utils.plot import boundary_to_figure, curve_to_figure


class MIDIExtractionDataset(BaseDataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.midi_min = self.config['midi_min']
        self.midi_max = self.config['midi_max']
        self.num_bins = self.config['midi_num_bins']
        self.midi_deviation = self.config['midi_prob_deviation']
        self.interval = (self.midi_max - self.midi_min) / (self.num_bins - 1)  # align with centers of bins
        self.sigma = self.midi_deviation / self.interval
        self.midi_shift_proportion = self.config['midi_shift_proportion']
        self.midi_shift_min, self.midi_shift_max = self.config['midi_shift_range']

    def midi_to_bin(self, midi):
        return (midi - self.midi_min) / self.interval

    def collater(self, samples):
        batch = super().collater(samples)
        midi_shifts = [
            random.random() * (self.midi_shift_max - self.midi_shift_min) + self.midi_shift_min
            if self.allow_aug and random.random() < self.midi_shift_proportion else 0
            for _ in range(len(samples))
        ]
        batch['units'] = collate_nd([s['units'] for s in samples])  # [B, T_s, C]
        batch['pitch'] = collate_nd([s['pitch'] + d for s, d in zip(samples, midi_shifts)])  # [B, T_s]
        batch['note_midi'] = collate_nd([s['note_midi'] + d for s, d in zip(samples, midi_shifts)])  # [B, T_n]
        batch['note_rest'] = collate_nd([s['note_rest'] for s in samples])  # [B, T_n]
        batch['note_dur'] = collate_nd([s['note_dur'] for s in samples])  # [B, T_n]

        miu = self.midi_to_bin(batch['note_midi'])[:, :, None]  # [B, T_n, 1]
        x = torch.arange(self.num_bins).float().reshape(1, 1, -1).to(miu.device)  # [1, 1, N]
        probs = ((x - miu) / self.sigma).pow(2).div(-2).exp()  # gaussian blur, [B, T_n, N]
        note_mask = collate_nd([torch.ones_like(s['note_rest']) for s in samples], pad_value=False)
        probs *= (note_mask[..., None] & ~batch['note_rest'][..., None])
        probs = F.pad(probs, [0, 0, 1, 0])

        unit2note = collate_nd([s['unit2note'] for s in samples])
        unit2note_ = unit2note[..., None].repeat([1, 1, self.num_bins])
        probs = torch.gather(probs, 1, unit2note_)
        batch['probs'] = probs  # [B, T_s, N]
        batch['unit2note'] = unit2note
        bounds = torch.diff(
            unit2note, dim=1, prepend=unit2note.new_zeros((batch['size'], 1))
        ) > 0
        batch['bounds'] = bounds.float()  # [B, T_s]

        return batch


# todo
class MIDIExtractionTask(BaseTask):
    def __init__(self, config: dict):
        super().__init__(config)
        self.midiloss = None
        self.dataset_cls = MIDIExtractionDataset
        self.midi_min = self.config['midi_min']
        self.midi_max = self.config['midi_max']
        self.midi_deviation = self.config['midi_prob_deviation']
        self.rest_threshold = self.config['rest_threshold']

    def build_model(self):

        model = build_object_from_class_name(self.config['model_cls'], nn.Module, config=self.config)

        return model

    def build_losses_and_metrics(self):
        self.midi_loss = nn.BCELoss()
        self.bound_loss = modules.losses.BinaryEMDLoss()

    def run_model(self, sample, infer=False):
        """
        steps:
            1. run the full model
            2. calculate losses if not infer
        """
        spec = sample['units']  # [B, T_ph]
        # target = (sample['probs'],sample['bounds'])  # [B, T_s, M]
        mask = sample['unit2note'] > 0

        f0 = sample['pitch']
        probs, bounds = self.model(x=spec, f0=f0, mask=mask)

        if infer:
            return probs, bounds
        else:
            losses = {}
            midi_loss = self.midi_loss(probs, sample['probs'])
            bound_loss = self.bound_loss(bounds, sample['bounds'])

            losses['bound_loss'] = bound_loss

            losses['midi_loss'] = midi_loss

            return losses

        # raise NotImplementedError()

    def _validation_step(self, sample, batch_idx):
        losses = self.run_model(sample, infer=False)
        if batch_idx < self.config['num_valid_plots']:
            probs, bounds = self.run_model(sample, infer=True)
            unit2note_gt = sample['unit2note']
            masks = unit2note_gt > 0
            probs *= masks[..., None]
            bounds *= masks

            unit2note_pred = decode_bounds_to_sequence(bounds) * masks
            dur_pred = unit2note_pred.new_zeros(1, unit2note_pred.max() + 1).scatter_add(
                dim=1, index=unit2note_pred, src=unit2note_pred
            )[:, 1:]
            self.plot_boundary(
                batch_idx, bounds_gt=sample['bounds'], bounds_pred=bounds,
                dur_gt=sample['note_dur'], dur_pred=dur_pred
            )

            midi_pred, rest_pred = decode_gaussian_blurred_probs(
                probs, vmin=self.midi_min, vmax=self.midi_max,
                deviation=self.midi_deviation, threshold=self.rest_threshold
            )
            midi_pred[rest_pred] = -1  # rest part is set to -1
            note_midi_gt = sample['note_midi'].clone()
            note_midi_gt[sample['note_rest']] = -1
            midi_gt = torch.gather(note_midi_gt, 1, unit2note_gt)
            self.plot_midi_curve(
                batch_idx, midi_gt=midi_gt, midi_pred=midi_pred, pitch=sample['pitch']
            )

        return losses, sample['size']

    ############
    # validation plots
    ############
    def plot_boundary(self, batch_idx, bounds_gt, bounds_pred, dur_gt, dur_pred):
        name = f'boundary_{batch_idx}'
        bounds_gt = bounds_gt[0].cpu().numpy()
        bounds_pred = bounds_pred[0].cpu().numpy()
        dur_gt = dur_gt[0].cpu().numpy()
        dur_pred = dur_pred[0].cpu().numpy()
        self.logger.experiment.add_figure(name, boundary_to_figure(
            bounds_gt, bounds_pred, dur_gt, dur_pred
        ), self.global_step)

    def plot_midi_curve(self, batch_idx, midi_gt, midi_pred, pitch):
        name = f'midi_{batch_idx}'
        midi_gt = midi_gt[0].cpu().numpy()
        midi_pred = midi_pred[0].cpu().numpy()
        pitch = pitch[0].cpu().numpy()
        self.logger.experiment.add_figure(name, curve_to_figure(
            midi_gt, midi_pred, curve_base=pitch, grid=1, base_label='pitch'
        ), self.global_step)
