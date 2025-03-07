import numpy as np
import librosa

def vocal_compressor(y, sr, threshold=-20.0, ratio=4.0, attack=0.005, release=0.05, makeup_gain=0.0):
    """
    Apply a compressor effect optimized for vocals
    Parameters:
    - y: Input audio signal (numpy array loaded with librosa)
    - sr: Sample rate
    - threshold: Threshold level in dB above which compression starts
    - ratio: Compression ratio (e.g., 4.0 means 4:1)
    - attack: Attack time in seconds
    - release: Release time in seconds
    - makeup_gain: Output gain compensation in dB
    """
    
    # Convert signal to dB scale (take absolute value and apply log)
    y_abs = np.abs(y)
    y_db = 20 * np.log10(y_abs + 1e-10)  # Add small value to avoid log(0)
    
    # Initialize array for gain reduction
    gain_reduction = np.zeros_like(y_db)
    
    # Variables for envelope follower
    env = np.zeros_like(y_db)
    attack_coef = np.exp(-1.0 / (attack * sr))  # Attack smoothing coefficient
    release_coef = np.exp(-1.0 / (release * sr))  # Release smoothing coefficient
    
    # Calculate envelope and apply gain reduction
    for i in range(1, len(y)):
        # Envelope follower: track signal level with attack/release
        env[i] = max(y_db[i], release_coef * env[i-1] + (1 - attack_coef) * y_db[i])
        
        # Apply compression to levels exceeding threshold
        if env[i] > threshold:
            excess = env[i] - threshold
            gain_reduction[i] = excess * (1 - 1/ratio)
    
    # Convert gain reduction from dB to linear scale and apply makeup gain
    gain = np.power(10, -gain_reduction / 20.0)  # Convert dB reduction to amplitude
    gain = gain * np.power(10, makeup_gain / 20.0)  # Apply makeup gain
    
    # Apply gain to original signal
    y_compressed = y * gain
    
    # Prevent clipping by normalizing if needed
    max_val = np.max(np.abs(y_compressed))
    if max_val > 1.0:
        y_compressed = y_compressed / max_val
        
    return y_compressed
