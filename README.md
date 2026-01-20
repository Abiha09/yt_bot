# YT_BOT: YouTube Automation Engine (Logic Ready)

This is a professional Python-based bot designed to automate the complete YouTube content creation workflow. 

##  Components Integrated Today:
Today I have successfully built the core architecture. The bot is programmed to use:
- **Script Generation:** OpenRouter (Mistral AI).
- **Voice Synthesis (TTS):** Edge-TTS for human-like audio.
- **Subtitles & Transcription:** OpenAI Whisper.
- **Visual Assets:** Pexels API for 4K stock clips.
- **Video Processing:** **MoviePy** to merge and render final MP4 files.
- **Upload:** YouTube Data API v3.

##  Current Progress:
- [x] **Project Structure:** Organized into `src`, `data`, and `config`.
- [x] **Logic Flow:** Successfully tested the path from Topic to Upload.
- [x] **Data Handling:** Reading from `queue.json` (Topics: Space, AI, Medicine).
- [x] **History Logging:** Updating `completed.json` after every run.

##  Next Step:
Connecting Real API Keys to the existing logic.

---
