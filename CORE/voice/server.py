"""
Voice MCP Server
Non-blocking bidirectional voice. Speak returns immediately, recording runs in background.

Tools:
  speak  - TTS text + start background recording. Returns instantly.
  hear   - Check if a recording is ready. Returns transcription or "still recording."

Requires:
  pip install openai sounddevice soundfile numpy
"""

import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA
from _needs import update_needs

# --- Paths ---

VOICE_PATH = DATA / 'voice'
RECORDINGS_PATH = VOICE_PATH / 'recordings'
RESPONSES_PATH = VOICE_PATH / 'responses'
CONFIG_PATH = VOICE_PATH / 'config.json'
LOG_FILE = VOICE_PATH / 'conversation.log'

# --- Audio imports (graceful) ---

try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# --- Config ---

SAMPLE_RATE = 16000
CHANNELS = 1
DEFAULT_VOICE = "nova"
SILENCE_THRESHOLD = 0.01
SILENCE_DURATION = 4.0
MAX_RECORD_SECONDS = 90

# --- Background recording state ---

_bg_lock = threading.Lock()
_bg_result = None       # None = no recording, "recording" = in progress, dict = done
_bg_timestamp = None


def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_api_key():
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    return load_config().get("openai_api_key")


def get_openai_client():
    api_key = get_api_key()
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def get_voice():
    return load_config().get("voice", DEFAULT_VOICE)


def log_exchange(speaker, text):
    try:
        VOICE_PATH.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {speaker}: {text}\n")
    except Exception:
        pass


# --- Core functions ---

def speak_text(text, voice=None):
    """TTS via OpenAI. Returns filepath or error string."""
    if not HAS_AUDIO:
        return None, "Audio libraries not installed. Run: pip install sounddevice soundfile numpy"

    client = get_openai_client()
    if not client:
        return None, "OpenAI API key not configured."

    if voice is None:
        voice = get_voice()

    RESPONSES_PATH.mkdir(parents=True, exist_ok=True)

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format="wav"
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = RESPONSES_PATH / f"response_{timestamp}.wav"
        with open(filepath, "wb") as f:
            f.write(response.read())

        data, samplerate = sf.read(str(filepath))
        sd.play(data, samplerate)
        sd.wait()

        return str(filepath), None
    except Exception as e:
        return None, f"TTS error: {e}"


def record_and_transcribe():
    """Record audio, transcribe, return result dict. Runs in background thread."""
    global _bg_result

    if not HAS_AUDIO:
        with _bg_lock:
            _bg_result = {"error": "Audio libraries not installed."}
        return

    RECORDINGS_PATH.mkdir(parents=True, exist_ok=True)

    # Record
    frames = []
    silence_frames = 0
    silence_threshold_frames = int(SILENCE_DURATION * SAMPLE_RATE / 1024)

    def callback(indata, frame_count, time_info, status):
        nonlocal silence_frames
        frames.append(indata.copy())
        volume = np.abs(indata).mean()
        if volume < SILENCE_THRESHOLD:
            silence_frames += 1
        else:
            silence_frames = 0

    try:
        # Play beep to signal listening
        duration_beep = 0.25
        freq = 1000
        t = np.linspace(0, duration_beep, int(SAMPLE_RATE * duration_beep), False)
        beep = 0.6 * np.sin(2 * np.pi * freq * t)
        fade = int(SAMPLE_RATE * 0.02)
        beep[:fade] *= np.linspace(0, 1, fade)
        beep[-fade:] *= np.linspace(1, 0, fade)
        sd.play(beep.astype(np.float32), SAMPLE_RATE)
        sd.wait()

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                           callback=callback, blocksize=1024):
            start_time = time.time()
            while True:
                sd.sleep(100)
                elapsed = time.time() - start_time
                if elapsed >= MAX_RECORD_SECONDS:
                    break
                if silence_frames >= silence_threshold_frames and len(frames) > 50:
                    break

        if not frames:
            with _bg_lock:
                _bg_result = {"you_said": "(no audio captured)"}
            return

        audio_data = np.concatenate(frames)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = RECORDINGS_PATH / f"recording_{timestamp}.wav"
        sf.write(str(filepath), audio_data, SAMPLE_RATE)

    except Exception as e:
        with _bg_lock:
            _bg_result = {"error": f"Recording error: {e}"}
        return

    # Transcribe
    text = None

    client = get_openai_client()
    if client:
        try:
            with open(filepath, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            text = transcript.text
        except Exception:
            pass

    if text is None:
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(str(filepath))
            text = result["text"]
        except Exception:
            pass

    if text is None:
        with _bg_lock:
            _bg_result = {"error": "No transcription service available.", "audio_file": str(filepath)}
        return

    text = text.strip()
    if not text or text == ".":
        text = "(silence)"

    log_exchange("Human", text)

    with _bg_lock:
        _bg_result = {"you_said": text, "audio_file": str(filepath)}


# --- Tool handlers ---

def handle_speak(args):
    """Speak text aloud, start background recording. Return immediately."""
    global _bg_result, _bg_timestamp

    text = args.get('text', '')
    voice = args.get('voice')

    if not text:
        return [{"type": "text", "text": "Nothing to say. Provide text parameter."}]

    # Speak the text (this blocks until TTS playback finishes — that's intentional)
    filepath, error = speak_text(text, voice)
    if error:
        return [{"type": "text", "text": f"Speak error: {error}"}]

    log_exchange("Agent", text)

    # Start background recording
    with _bg_lock:
        _bg_result = "recording"
        _bg_timestamp = datetime.now().strftime("%H:%M:%S")

    thread = threading.Thread(target=record_and_transcribe, daemon=True)
    thread.start()

    return [{"type": "text", "text": f"Spoke: \"{text}\"\nRecording reply — use hear to check."}]


def handle_hear(args):
    """Check if background recording is done. Return result or status."""
    global _bg_result

    with _bg_lock:
        result = _bg_result

    if result is None:
        return [{"type": "text", "text": "No recording in progress. Use speak first."}]

    if result == "recording":
        return [{"type": "text", "text": f"Still recording (started {_bg_timestamp}). Check back soon."}]

    # Recording is done — return result and clear state
    with _bg_lock:
        _bg_result = None

    if "error" in result:
        return [{"type": "text", "text": f"Recording error: {result['error']}"}]

    you_said = result.get("you_said", "(nothing)")
    return [{"type": "text", "text": f"They said: {you_said}"}]


# ============ MCP Protocol ============

def send_response(rid, result):
    r = {"jsonrpc": "2.0", "id": rid, "result": result}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


def send_error(rid, code, msg):
    r = {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": str(msg)}}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


TOOLS = [
    {
        "name": "speak",
        "description": "Speak text aloud, then start recording reply. Returns immediately. Use hear to get the reply.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "What to say (spoken aloud)"},
                "voice": {"type": "string", "description": "Voice: alloy/echo/fable/onyx/nova/shimmer"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "hear",
        "description": "Check if a recording finished. Returns what was said or 'still recording.'",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]


def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    rid = req.get("id")

    if method == "initialize":
        send_response(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "voice", "version": "1.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": TOOLS})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "speak":
                result = handle_speak(args)
            elif name == "hear":
                result = handle_hear(args)
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("voice", name)
        except Exception as e:
            send_error(rid, -32000, str(e))
        return

    send_error(rid, -32601, f"Unknown method: {method}")


def main():
    VOICE_PATH.mkdir(parents=True, exist_ok=True)
    RECORDINGS_PATH.mkdir(parents=True, exist_ok=True)
    RESPONSES_PATH.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            handle_request(json.loads(line))
        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    main()
