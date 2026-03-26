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

from std_msgs.msg import Int16MultiArray

class WhisperNode(Node):

    def __init__(self):
        super().__init__('whisper_node')
        
        # Parameters
        self.declare_parameter('mode', 'local') # local, producer, consumer
        self.mode = self.get_parameter('mode').value
        
        # Audio State
        self.is_recording = False
        self.audio_data_list = []
        self.silence_blocks = 0
        self.max_recording_blocks = 300 # ~30s
        self.min_recording_blocks = 5 # ~0.5s
        self.max_silence_blocks = 15 # ~1.5s
        
        self.publisher = self.create_publisher(String, '/voice_command', 10)
        self.audio_pub = self.create_publisher(Int16MultiArray, '/audio_captured', 10)
        
        if self.mode in ['local', 'consumer']:
            # Whisper Setup (Optimized for Laptop GPU if consumer, Jetson CPU if local)
            model_size = "base.en" if self.mode == 'consumer' else "tiny.en"
            device = "cuda" if self.mode == 'consumer' else "cpu"
            try:
                self.model = WhisperModel(model_size, device=device, compute_type="float16" if device=="cuda" else "default")
                self.get_logger().info(f"Whisper model '{model_size}' loaded on {device}")
            except Exception as e:
                self.get_logger().warn(f"{device} failed, using CPU: {e}")
                self.model = WhisperModel(model_size, device="cpu", compute_type="default", cpu_threads=4)

        if self.mode == 'consumer':
            self.audio_sub = self.create_subscription(Int16MultiArray, '/audio_captured', self.remote_audio_callback, 10)
            self.get_logger().info("Whisper Node (CONSUMER) ready. Listening for remote audio...")
            return 
        
        # --- Mic Setup (Only for Producer/Local) ---
        self.declare_parameter('device_id', '')
        device_id = self.get_parameter('device_id').value
        
        # 1. Try to find a USB mic automatically
        if not device_id:
            try:
                devices = sd.query_devices()
                for i, d in enumerate(devices):
                    if d['max_input_channels'] > 0:
                        name = d['name'].lower()
                        if 'usb' in name:
                            device_id = i
                            self.get_logger().info(f"✓ USB mic found: {d['name']}")
                            break
            except Exception as e:
                self.get_logger().error(f"Could not query audio devices: {e}")

        # 2. Final Fallback to system default if no USB mic found
        if device_id is None or device_id == '':
            self.get_logger().info("No USB mic found. Using system default input.")
            device_id = None # sounddevice default

        if device_id is None:
            self.get_logger().warn("No audio input found, using system default.")

        # Start Stream
        self.stream = None
        target_rate = 16000
        try:
            self.stream = sd.InputStream(
                device=device_id, channels=1, samplerate=target_rate,
                callback=self.audio_callback, blocksize=int(target_rate * 0.1)
            )
            self.actual_rate = target_rate
        except Exception as e:
            self.get_logger().warn(f"16kHz on device {device_id} failed: {e}")
            info = sd.query_devices(device_id, 'input')
            self.actual_rate = int(info['default_samplerate'])
            self.stream = sd.InputStream(
                device=device_id, channels=1, samplerate=self.actual_rate,
                callback=self.audio_callback, blocksize=int(self.actual_rate * 0.1)
            )
        
        if self.stream is not None:
            self.stream.start()
            self.get_logger().info(f"Whisper Node ({self.mode.upper()}) Ready — Mic {device_id} at {self.actual_rate}Hz")
        else:
            self.get_logger().error("Critical: Could not connect to microphone. Voice control disabled.")

    def audio_callback(self, indata, frames, time, status):
        """Producer/Local: Accumulate audio."""
        audio_block = indata.copy().flatten()
        rms = np.sqrt(np.mean(audio_block**2))
        
        if self.is_recording:
            self.audio_data_list.append(audio_block)
            
        if rms > 0.02: 
            if not self.is_recording:
                self.get_logger().info("Listening...")
                self.is_recording = True
                self.audio_data_list.append(audio_block)
            self.silence_blocks = 0
            
            if len(self.audio_data_list) > self.max_recording_blocks:
                self.get_logger().info("Max recording duration reached. Processing...")
                self.process_recording()
        else:
            if self.is_recording:
                self.silence_blocks += 1
                if self.silence_blocks > self.max_silence_blocks:
                    if len(self.audio_data_list) > self.min_recording_blocks:
                        self.process_recording()
                    else:
                        self.get_logger().info(f"Discarded short sound ({len(self.audio_data_list)} blocks).")
                    self.is_recording = False
                    self.audio_data_list = []
                    self.silence_blocks = 0

    def process_recording(self):
        full_audio = np.concatenate(self.audio_data_list)
        if self.mode == 'producer':
            # Resample to 16kHz for network efficiency
            audio_16k = self.resample_audio(full_audio, self.actual_rate, 16000)
            # Fast offload: Send raw PCM Int16 to network
            msg = Int16MultiArray()
            # Convert float32 [-1, 1] to int16
            pcm = (audio_16k * 32767).astype(np.int16)
            msg.data = pcm.tolist()
            self.audio_pub.publish(msg)
            self.get_logger().info(f"Sent {len(pcm)} samples (16kHz) to remote host.")
        else:
            # Local transcription
            threading.Thread(target=self.transcribe, args=(full_audio,), daemon=True).start()
        
        self.audio_data_list = []
        self.is_recording = False

    def remote_audio_callback(self, msg):
        """Consumer: Receive audio from network and transcribe."""
        # Convert list back to numpy and then to float32
        pcm = np.array(msg.data, dtype=np.int16)
        audio_float = pcm.astype(np.float32) / 32767.0
        self.get_logger().info(f"Received {len(audio_float)} samples from Jetson. Transcribing...")
        threading.Thread(target=self.transcribe, args=(audio_float,), daemon=True).start()

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
        return audio

    def transcribe(self, audio_data):
        try:
            # If rate isn't set (consumer), it must be 16k since producer sends 16k resampled?
            # Actually producer sends raw. Let's fix that: producer should resample or consumer should know.
            # We'll assume producer sends 16k for network efficiency.
            rate = 16000 if self.mode == 'consumer' else self.actual_rate
            audio_16k = self.resample_audio(audio_data, rate)
            
            self.get_logger().info(f"Transcribing {len(audio_16k) / 16000.0:.1f}s segment...")
            
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
        if hasattr(node, 'stream') and node.stream is not None:
            try:
                node.stream.stop()
                node.stream.close()
            except Exception:
                pass
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass

if __name__ == '__main__':
    main()
