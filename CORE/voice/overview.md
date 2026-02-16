# Voice Server

Bidirectional voice. Speak aloud, then record and transcribe the reply. Non-blocking design.

## Tools
- **speak** — TTS text aloud via OpenAI, then start background recording. Returns immediately. Optional voice param (alloy/echo/fable/onyx/nova/shimmer, default nova).
- **hear** — check if background recording finished. Returns transcription, "still recording", or "no recording in progress".

## How It Works
- Speak plays audio via sounddevice, then spawns a background thread for recording.
- Recording listens until silence (4s of quiet) or max 90 seconds. Plays a beep to signal listening.
- Transcription tries OpenAI Whisper API first, falls back to local whisper model.
- Conversation logged to DATA/voice/conversation.log.
- WAV format throughout (not MP3 — soundfile can't decode MP3).
- Silence threshold: 0.01 (tuned for typical ambient noise).

## Database
None.

## File Storage
- `DATA/voice/recordings/` — recorded WAV files
- `DATA/voice/responses/` — TTS output WAV files
- `DATA/voice/config.json` — OpenAI API key + voice preference
- `DATA/voice/conversation.log` — timestamped exchange log

## External Dependencies
- `_paths.py` — DATA
- Requires: `pip install openai sounddevice soundfile numpy`
- Graceful degradation: works without audio libs (returns helpful error), works without OpenAI key (returns config error)
