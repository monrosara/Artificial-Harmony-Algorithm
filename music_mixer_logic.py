import os
import random
import tempfile
from collections import defaultdict
import librosa
import numpy as np
import warnings
import math
from datetime import datetime
import re
from pydub import AudioSegment

# Suppress librosa warnings
warnings.filterwarnings("ignore", category=UserWarning, module='librosa')

# Camelot Wheel System
CAMELOT_WHEEL = {
    "1A": "B", "2A": "F", "3A": "C", "4A": "G", "5A": "D", "6A": "A", 
    "7A": "E", "8A": "B", "9A": "F#", "10A": "C#", "11A": "G#", "12A": "D#",
    "1B": "G#", "2B": "D#", "3B": "A#", "4B": "F", "5B": "C", "6B": "G",
    "7B": "D", "8B": "A", "9B": "E", "10B": "B", "11B": "F#", "12B": "C#"
}

STANDARD_PROBABILITIES = {
    'drums': 0.9, 'bass': 0.8, 'melody': 0.7, 'harmony': 0.6,
    'vocals': 0.4, 'fx': 0.3, 'loops': 0.5, 'other': 0.2
}

EXPERIMENTAL_PROBABILITIES = {
    'drums': 0.6, 'bass': 0.5, 'melody': 0.8, 'harmony': 0.7,
    'vocals': 0.6, 'fx': 0.8, 'loops': 0.4, 'other': 0.9
}

class MusicMixer:
    def __init__(self, samples_dir, target_bpm=128, current_key="8A", experimental_mode=False):
        self.samples_dir = samples_dir
        self.target_bpm = target_bpm
        self.current_key = current_key
        self.experimental_mode = experimental_mode
        
        self.bpm_cache = {}
        self.key_cache = {}
        
        # Temporary directory for processing
        self.temp_dir = tempfile.mkdtemp(prefix="music_mixer_")
        
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @staticmethod
    def extract_key_from_filename(filename):
        """Extract Camelot key from filename"""
        camelot_patterns = [
            r'\b(\d{1,2}[AB])\b',
            r'key[\s_-]*(\d{1,2}[AB])',
            r'(\d{1,2}[AB])[\s_-]*key',
        ]
        
        for pattern in camelot_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                key = match.group(1).upper()
                if key in CAMELOT_WHEEL:
                    return key
        
        musical_keys = {
            'cmaj': '8B', 'c major': '8B', 'c#maj': '3B', 'c# major': '3B',
            'dmaj': '10B', 'd major': '10B', 'd#maj': '5B', 'd# major': '5B',
            'emaj': '12B', 'e major': '12B', 'fmaj': '7B', 'f major': '7B',
            'f#maj': '2B', 'f# major': '2B', 'gmaj': '9B', 'g major': '9B',
            'g#maj': '4B', 'g# major': '4B', 'amaj': '11B', 'a major': '11B',
            'a#maj': '6B', 'a# major': '6B', 'bmaj': '1B', 'b major': '1B',
            'cmin': '5A', 'c minor': '5A', 'c#min': '12A', 'c# minor': '12A',
            'dmin': '7A', 'd minor': '7A', 'd#min': '2A', 'd# minor': '2A',
            'emin': '9A', 'e minor': '9A', 'fmin': '4A', 'f minor': '4A',
            'f#min': '11A', 'f# minor': '11A', 'gmin': '6A', 'g minor': '6A',
            'g#min': '1A', 'g# minor': '1A', 'amin': '8A', 'a minor': '8A',
            'a#min': '3A', 'a# minor': '3A', 'bmin': '10A', 'b minor': '10A',
        }
        
        for key_pattern, camelot_key in musical_keys.items():
            if key_pattern in filename.lower():
                return camelot_key
        
        return None
    
    @staticmethod
    def extract_bpm_from_filename(filename):
        """Extract BPM from filename"""
        patterns = [
            r'(\d{2,3})bpm',
            r'bpm[\s_-]*(\d{2,3})',
            r'[\s_-](\d{2,3})[\s_-]bpm',
            r'^(\d{2,3})[\s_-]',
            r'[\s_-](\d{2,3})$',
            r'\((\d{2,3})\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                bpm = int(match.group(1))
                if 80 <= bpm <= 180:
                    return bpm
        return None
    
    @staticmethod
    def get_compatible_keys(key):
        """Get list of harmonically compatible keys"""
        if key not in CAMELOT_WHEEL:
            return [key]
        
        num = int(key[:-1])
        letter = key[-1]
        
        compatible = [
            key,
            f"{num}{'B' if letter == 'A' else 'A'}",
        ]
        
        next_num = num + 1 if num < 12 else 1
        prev_num = num - 1 if num > 1 else 12
        
        compatible.append(f"{next_num}{letter}")
        compatible.append(f"{prev_num}{letter}")
        
        return compatible
    
    def get_all_samples(self, custom_dir=None):
        """Get all audio files from directory"""
        search_dir = custom_dir if custom_dir else self.samples_dir
        audio_files = []
        
        for root, _, files in os.walk(search_dir):
            for f in files:
                if f.lower().endswith(('.wav', '.mp3', '.flac', '.aiff')):
                    audio_files.append(os.path.join(root, f))
        return audio_files
    
    def get_bpm(self, file_path):
        """Detect BPM with caching"""
        if file_path in self.bpm_cache:
            return self.bpm_cache[file_path]
        
        try:
            filename = os.path.basename(file_path).lower()
            bpm_from_name = self.extract_bpm_from_filename(filename)
            
            if bpm_from_name:
                self.bpm_cache[file_path] = bpm_from_name
                return bpm_from_name
            
            parent_dir = os.path.basename(os.path.dirname(file_path)).lower()
            parent_bpm = self.extract_bpm_from_filename(parent_dir)
            if parent_bpm:
                self.bpm_cache[file_path] = parent_bpm
                return parent_bpm
            
            # Audio analysis (limit duration for speed)
            y, sr = librosa.load(file_path, duration=15, mono=True, sr=22050)
            
            try:
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                bpm = float(tempo)
            except:
                onset_env = librosa.onset.onset_strength(y=y, sr=sr)
                tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
                bpm = float(tempo[0]) if hasattr(tempo, '__iter__') else float(tempo)
            
            if bpm < 80:
                bpm *= 2
            elif bpm > 180:
                bpm /= 2
            
            common_bpms = [80, 85, 90, 95, 100, 105, 110, 115, 120, 
                          122, 124, 126, 128, 130, 132, 135, 138, 
                          140, 145, 150, 155, 160, 165, 170, 175, 180]
            closest_bpm = min(common_bpms, key=lambda x: abs(x - bpm))
            
            self.bpm_cache[file_path] = closest_bpm
            return closest_bpm
            
        except Exception as e:
            self.bpm_cache[file_path] = self.target_bpm
            return self.target_bpm
    
    def get_sample_key(self, file_path):
        """Get musical key for sample"""
        if file_path in self.key_cache:
            return self.key_cache[file_path]
        
        filename = os.path.basename(file_path).lower()
        key = self.extract_key_from_filename(filename)
        
        if not key:
            parent_dir = os.path.basename(os.path.dirname(file_path)).lower()
            key = self.extract_key_from_filename(parent_dir)
        
        self.key_cache[file_path] = key
        return key
    
    @staticmethod
    def optimize_audio_length(audio, target_bpm):
        """Optimize audio length for smooth looping"""
        beat_duration = 60000 / target_bpm
        measure_duration = beat_duration * 4
        ideal_length = measure_duration * 4
        
        current_length = len(audio)
        
        if current_length < ideal_length:
            looped = AudioSegment.empty()
            while len(looped) < ideal_length:
                looped += audio
            return looped[:ideal_length]
        
        return audio
    
    @staticmethod
    def change_tempo(audio_segment, current_bpm, target_bpm):
        """Change audio tempo"""
        if current_bpm == target_bpm or current_bpm <= 0:
            return audio_segment
        
        try:
            speed_factor = target_bpm / current_bpm
            new_sample_rate = int(audio_segment.frame_rate * speed_factor)
            
            tempo_changed = audio_segment._spawn(
                audio_segment.raw_data, 
                overrides={'frame_rate': new_sample_rate}
            ).set_frame_rate(audio_segment.frame_rate)
            
            return tempo_changed
            
        except Exception as e:
            return audio_segment
    
    def classify_samples(self, samples):
        """Classify samples into categories"""
        categories = defaultdict(list)
        
        for sample in samples:
            bpm = self.get_bpm(sample)
            key = self.get_sample_key(sample)
            filename = os.path.basename(sample).lower()
            
            if any(word in filename for word in ['kick', 'drum', 'bd', 'sd', 'snare', 'hat']):
                categories['drums'].append((sample, bpm, key))
            elif any(word in filename for word in ['bass', 'sub', '808', 'low', 'bassline']):
                categories['bass'].append((sample, bpm, key))
            elif any(word in filename for word in ['melody', 'lead', 'synth', 'pluck', 'arp']):
                categories['melody'].append((sample, bpm, key))
            elif any(word in filename for word in ['chord', 'pad', 'string', 'harmony', 'stabs']):
                categories['harmony'].append((sample, bpm, key))
            elif any(word in filename for word in ['fx', 'effect', 'impact', 'sweep', 'rise']):
                categories['fx'].append((sample, bpm, key))
            elif any(word in filename for word in ['vocal', 'voice', 'chant', 'sing', 'vox']):
                categories['vocals'].append((sample, bpm, key))
            elif any(word in filename for word in ['loop', 'groove', 'full', 'mix']):
                categories['loops'].append((sample, bpm, key))
            else:
                categories['other'].append((sample, bpm, key))
        
        return categories
    
    def create_multilayer_composition(self, num_layers=3, custom_samples_dir=None):
        """Create multi-layer composition"""
        # Get samples from specified directory or default
        if custom_samples_dir:
            samples = self.get_all_samples(custom_samples_dir)
        else:
            samples = self.get_all_samples()
        
        if not samples:
            raise ValueError("No audio files found")
        
        categories = self.classify_samples(samples)
        layers = []
        composition_info = {
            'layers': [],
            'bpm': self.target_bpm,
            'key': self.current_key,
            'mode': 'experimental' if self.experimental_mode else 'standard',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        priority_order = ['drums', 'bass', 'melody', 'harmony', 'vocals', 'fx', 'loops', 'other']
        
        if self.experimental_mode:
            probabilities = EXPERIMENTAL_PROBABILITIES
        else:
            probabilities = STANDARD_PROBABILITIES
        
        available_categories = []
        for category in priority_order:
            if category in categories and categories[category]:
                if random.random() < probabilities[category]:
                    available_categories.append(category)
        
        if not available_categories:
            available_categories = [cat for cat in priority_order 
                                  if cat in categories and categories[cat]]
        
        if not available_categories:
            return [], composition_info
        
        actual_layers = min(num_layers, len(available_categories))
        selected_categories = random.sample(available_categories, actual_layers)
        
        volume_ranges = {
            'drums': (0.4, 0.9), 'bass': (0.3, 0.8), 'melody': (0.2, 0.7),
            'harmony': (0.2, 0.6), 'fx': (0.1, 0.8), 'vocals': (0.3, 0.8),
            'loops': (0.2, 0.7), 'other': (0.1, 0.9)
        }
        
        compatible_keys = self.get_compatible_keys(self.current_key)
        
        for category in selected_categories:
            if categories[category]:
                compatible_samples = []
                all_samples = []
                
                for sample_info in categories[category]:
                    sample_path, bpm, key = sample_info
                    all_samples.append((sample_path, bpm, key))
                    
                    if category in ['drums', 'fx', 'other']:
                        compatible_samples.append((sample_path, bpm, key))
                    else:
                        if key is None or key in compatible_keys:
                            compatible_samples.append((sample_path, bpm, key))
                
                samples_to_use = compatible_samples if compatible_samples else all_samples
                
                if samples_to_use:
                    sample_path, original_bpm, sample_key = random.choice(samples_to_use)
                    
                    try:
                        audio = AudioSegment.from_file(sample_path)
                        audio = self.optimize_audio_length(audio, self.target_bpm)
                        
                        if original_bpm > 0 and abs(original_bpm - self.target_bpm) > 1:
                            audio = self.change_tempo(audio, original_bpm, self.target_bpm)
                        
                        vol_range = volume_ranges.get(category, (0.2, 0.7))
                        volume = random.uniform(vol_range[0], vol_range[1])
                        
                        layers.append({
                            'category': category,
                            'sample': sample_path,
                            'audio': audio,
                            'original_bpm': original_bpm,
                            'key': sample_key,
                            'volume': volume
                        })
                        
                        composition_info['layers'].append({
                            'category': category,
                            'sample': os.path.basename(sample_path),
                            'original_bpm': original_bpm,
                            'key': sample_key,
                            'volume': volume
                        })
                        
                    except Exception as e:
                        continue
        
        return layers, composition_info
    
    def generate_mix_audio(self, layers, duration_ms=30000):
        """Generate final audio mix from layers"""
        if not layers:
            raise ValueError("No layers to mix")
        
        # Create empty audio of required length
        mix_audio = AudioSegment.silent(duration=duration_ms)
        
        for layer in layers:
            audio = layer['audio']
            gain_db = 20 * math.log10(layer['volume'])
            audio_with_gain = audio.apply_gain(gain_db)
            
            # Loop layer to required length
            looped_audio = AudioSegment.empty()
            while len(looped_audio) < duration_ms:
                looped_audio += audio_with_gain
            
            looped_audio = looped_audio[:duration_ms]
            
            # Overlay layer on mix
            mix_audio = mix_audio.overlay(looped_audio)
        
        # Save to temporary file
        temp_file = os.path.join(self.temp_dir, f"mix_{datetime.now().strftime('%H%M%S')}.wav")
        mix_audio.export(temp_file, format="wav")
        
        return temp_file
    
    def generate_complete_mix(self, num_layers=3, custom_samples_dir=None):
        """Complete mix generation process"""
        try:
            # 1. Create composition
            layers, composition_info = self.create_multilayer_composition(
                num_layers, custom_samples_dir
            )
            
            if not layers:
                raise ValueError("Could not create composition")
            
            # 2. Generate audio file
            audio_path = self.generate_mix_audio(layers)
            
            # 3. Format description
            description = self._format_composition_info(composition_info)
            
            return audio_path, description, composition_info
            
        except Exception as e:
            raise
    
    def _format_composition_info(self, composition_info):
        """Format composition information"""
        text = f"""
🎶 **Generated Mix!**
        
**Parameters:**
• Layers: {len(composition_info['layers'])}
• BPM: {composition_info['bpm']}
• Key: {composition_info['key']}
• Mode: {composition_info['mode']}
        
**Mix Composition:**
"""
        
        for i, layer in enumerate(composition_info['layers'], 1):
            key_info = f", key: {layer['key']}" if layer['key'] else ""
            text += f"\n{i}. {layer['category']}: {layer['sample']} "
            text += f"(BPM: {layer['original_bpm']}, volume: {layer['volume']:.2f}{key_info})"
        
        return text