import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np
import threading
try:
    from scipy.signal import resample_poly
    from math import gcd
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

class WhisperNode(Node):

    def __init__(self):
        super().__init__('whisper_node')
        self.publisher = self.create_publisher(String, '/voice_command', 10)
        
        # Whisper Setup (Optimized for Jetson CPU)
        model_size = "tiny.en" 
        try:
            # Try CUDA first
            self.model = WhisperModel(model_size, device="cuda", compute_type="float16")
            self.get_logger().info(f"Whisper model '{model_size}' loaded on CUDA")
        except Exception as e:
            self.get_logger().warn(f"CUDA failed, using CPU: {e}")
            self.model = WhisperModel(model_size, device="cpu", compute_type="default", cpu_threads=4)

        # Audio Buffer & State
        self.audio_data_list = []
        self.silence_blocks = 0
        self.max_silence_blocks = 15 # ~1.5s
        self.min_recording_blocks = 3 # ~0.3s
        self.max_recording_blocks = 50 # ~5.0s hard cutoff
        self.is_recording = False
        
        # Audio Device Selection — find the USB mic by exact name

        # Audio Device Selection — find the USB mic by exact hw:2,0 name
        devices = sd.query_devices()
        device_id = None
        
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                name = d['name'].lower()
                # Match the exact device seen: 'Usb Audio Device: USB Audio (hw:2,0)'
                if 'usb audio device' in name or ('usb' in name and 'hw:2' in name):
                    device_id = i
                    self.get_logger().info(f"✓ USB mic found at device [{i}]: {d['name']}")
                    break
        
        # Fallback: pulse (now routed to USB mic via pactl above)
        if device_id is None:
            for i, d in enumerate(devices):
                if d['max_input_channels'] > 0 and 'pulse' in d['name'].lower():
                    device_id = i
                    self.get_logger().info(f"✓ Using PulseAudio (routed to USB mic) [{i}]: {d['name']}")
                    break
        
        if device_id is None:
            self.get_logger().warn("No audio input found, using system default.")

        # Start Stream
        target_rate = 16000
        try:
            self.stream = sd.InputStream(
                device=device_id, channels=1, samplerate=target_rate,
                callback=self.audio_callback, blocksize=int(target_rate * 0.1)
            )
            self.actual_rate = target_rate
        except Exception as e:
            self.get_logger().warn(f"16kHz on device {device_id} failed, using native: {e}")
            info = sd.query_devices(device_id, 'input')
            self.actual_rate = int(info['default_samplerate'])
            self.stream = sd.InputStream(
                device=device_id, channels=1, samplerate=self.actual_rate,
                callback=self.audio_callback, blocksize=int(self.actual_rate * 0.1)
            )
        
        self.stream.start()
        self.get_logger().info(f"Whisper Node Ready — Device {device_id} at {self.actual_rate}Hz")

    def audio_callback(self, indata, frames, time, status):
        """Accumulate audio and trigger transcription on silence or max duration."""
        audio_block = indata.copy().flatten()
        # Use RMS instead of L2 norm so it is independent of blocksize
        rms = np.sqrt(np.mean(audio_block**2))
        
        # Always append valid blocks if we are already recording
        if self.is_recording:
            self.audio_data_list.append(audio_block)
            
        # Trigger on sound (0.02 RMS is more sensitive to softer speech)
        if rms > 0.02: 
            if not self.is_recording:
                self.get_logger().info("Sound detected, listening...")
                self.is_recording = True
                self.audio_data_list.append(audio_block) # Append onset
            
            self.silence_blocks = 0
            
            # Force transcription if recording gets too long (e.g. background noise stuck)
            if len(self.audio_data_list) > self.max_recording_blocks:
                self.get_logger().info("Max recording duration reached. Transcribing...")
                full_audio = np.concatenate(self.audio_data_list)
                threading.Thread(target=self.transcribe, args=(full_audio,)).start()
                self.is_recording = False
                self.audio_data_list = []
                self.silence_blocks = 0
        else:
            if self.is_recording:
                self.silence_blocks += 1
                if self.silence_blocks > self.max_silence_blocks:
                    blocks = len(self.audio_data_list)
                    if blocks > self.min_recording_blocks:
                        full_audio = np.concatenate(self.audio_data_list)
                        threading.Thread(target=self.transcribe, args=(full_audio,)).start()
                    else:
                        self.get_logger().info(f"Discarded short sound ({blocks} blocks).")
                    
                    self.is_recording = False
                    self.audio_data_list = []
                    self.silence_blocks = 0

    def resample_audio(self, audio, from_rate, to_rate=16000):
        """Downsample and normalize audio for Whisper."""
        if from_rate != to_rate:
            if HAS_SCIPY:
                g = gcd(from_rate, to_rate)
                audio = resample_poly(audio, to_rate // g, from_rate // g).astype(np.float32)
            else:
                ratio = from_rate // to_rate
                audio = audio[::ratio].astype(np.float32)
        
        # Normalize to ±0.9 for Whisper
        peak = np.max(np.abs(audio))
        if peak > 1e-4:
            audio = audio * (0.9 / peak)
            self.get_logger().info(f"Segment Peak: {peak:.3f} (Normalized to 0.9)")
        return audio

    def transcribe(self, audio_data):
        try:
            # Resample and Normalize
            audio_16k = self.resample_audio(audio_data, self.actual_rate)
            duration = len(audio_16k) / 16000.0
            self.get_logger().info(f"Transcribing {duration:.1f}s segment...")
            
            # Use initial_prompt to bias towards robot commands
            segments, _ = self.model.transcribe(
                audio_16k, 
                beam_size=5,
                language="en",
                condition_on_previous_text=False,
                initial_prompt="A robot receiving voice commands like 'turn left', 'go forward', 'slowly', 'stop'."
            )
            
            text = "".join([s.text for s in segments]).strip()
            if text:
                self.get_logger().info(f"Parsed: '{text}'")
                msg = String()
                msg.data = text
                self.publisher.publish(msg)
            else:
                self.get_logger().info("Transcription empty (noise detected).")
        except Exception as e:
            self.get_logger().error(f"Transcription error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = WhisperNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stream.stop()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
