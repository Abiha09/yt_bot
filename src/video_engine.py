import os
import requests
import asyncio
import edge_tts
import whisper
import yaml
from dotenv import load_dotenv
import time

# Configure MoviePy to use the found binaries BEFORE importing it
FFMPEG_PATH = r"C:\Users\tahreemifikhar009\MediaGet2\ffmpeg.exe"
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"

if os.path.exists(FFMPEG_PATH):
    ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
    if ffmpeg_dir not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + ffmpeg_dir
    os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH
    os.environ["FFMPEG_BINARY"] = FFMPEG_PATH
    print(f"System: FFmpeg found and added to PATH: {ffmpeg_dir}")

if os.path.exists(IMAGEMAGICK_PATH):
    os.environ["IMAGEMAGICK_BINARY"] = IMAGEMAGICK_PATH
    print(f"System: ImageMagick linked for subtitles: {IMAGEMAGICK_PATH}")

try:
    from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
except ImportError:
    from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

try:
    import moviepy.video.fx as vfx
except ImportError:
    vfx = None

load_dotenv(os.path.join("API.env", "exact.env"))

class VideoEngine:
    """
    THE FACTORY: 
    Integrates OpenRouter, Edge-TTS, Whisper, Pexels, and MoviePy.
    """

    def __init__(self):
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        
        with open("config/settings.yaml", "r") as f:
            self.settings = yaml.safe_load(f)
            
        self.model = self.settings['ai_config']['model_name']
        
        # Ensure temp directories exist
        os.makedirs("Data/temp", exist_ok=True)
        os.makedirs("Data/library", exist_ok=True)

    def generate_script(self, topic):
        """Generates a structured script with specific visual keywords for each scene."""
        print(f"Generating professional scene-based script for: {topic}")
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "https://github.com/YT_BOT",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Write a highly engaging, professional 60-second YouTube script about {topic}. 
        IMPORTANT: The total script MUST be at least 180 words to fill exactly 60 seconds.
        The tone should be cinematic, authoritative, and visually descriptive.
        
        Break the script into 12-15 short, fast-paced SCENES. Each scene should last 4-5 seconds to keep the viewer engaged.
        For each scene, provide:
        1. "text": Spoken dialogue (2-3 punchy, descriptive sentences that tell a story).
        2. "keywords": 5-8 search terms for high-quality stock footage.
           - Be extremely specific (e.g., instead of 'nature', use 'aerial shot of pine forest at sunrise').
           - Match the emotional tone of the words.
           - Include atmospheric terms ('cinematic 4k', 'slow motion', 'epic lighting').
        
        Return your response in this EXACT JSON format:
        [
          {{"text": "Spoken dialogue here", "keywords": ["specific visual", "cinematic atmosphere"]}},
          ...
        ]
        Return ONLY the JSON array.
        """
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.settings['ai_config'].get('max_tokens', 1500),
            "response_format": { "type": "json_object" } if "gpt-4o" in self.model or "gemini" in self.model else None
        }
        
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            import json
            import re
            content = response.json()['choices'][0]['message']['content']
            
            # Use regex to find the first '[' and last ']' to extract JSON array
            try:
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    json_str = match.group(0)
                else:
                    json_str = content
                
                scenes = json.loads(json_str)
            except (json.JSONDecodeError, AttributeError):
                print(f"Warning: Direct JSON parse failed, attempting manual cleaning...")
                try:
                    # Very simple repair: if it ends with words but missing brackets
                    if content.strip().startswith('[') and not content.strip().endswith(']'):
                         content = content.strip() + '"]}]' # Try to close common patterns
                    
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    scenes = json.loads(content)
                except:
                    raise Exception("AI JSON is too corrupted to repair.")
            
            # Handle if AI returns a dictionary with a "scenes" key
            if isinstance(scenes, dict) and "scenes" in scenes:
                scenes = scenes["scenes"]
            
            return scenes
        except Exception as e:
            print(f"Error generating structured script: {e}")
            # Fallback to a better, much longer multi-scene sequence (approx 50-60s)
            return [
                {"text": f"In the vast tapestry of our modern world, few things carry as much hidden power as {topic}.", "keywords": ["mysterious global footage", "cinematic atmosphere"]},
                {"text": f"We often overlook the subtle influence it has on our daily lives, yet its impact is undeniable.", "keywords": ["daily life routine", "subtle connection"]},
                {"text": f"From its historical origins to the cutting-edge secrets known only to a few, {topic} is evolving.", "keywords": ["historical evolution", "future technology"]},
                {"text": f"Imagine a future where understanding {topic} is the key to unlocking true potential.", "keywords": ["future vision", "unlocking potential"]},
                {"text": f"The benefits we see on the surface are just the beginning of a much deeper story.", "keywords": ["ocean depth", "surface layer"]},
                {"text": f"Experts are now uncovering data that suggests we've only scratched the surface.", "keywords": ["scientific research", "microscope"]},
                {"text": f"But what does this mean for you, and how can you harness this power today?", "keywords": ["personal empowerment", "harnessing energy"]},
                {"text": f"As we peel back the layers, a shocking truth begins to emerge about our connection to it.", "keywords": ["peeling layers", "emerging truth"]},
                {"text": f"It's time to stop ignoring the signs and start embracing the reality of {topic}.", "keywords": ["embracing reality", "awareness"]},
                {"text": f"Stay curious, keep exploring, and remember—the biggest secrets are often hiding in plain sight.", "keywords": ["curiosity", "hiding in plain sight"]}
            ]

    async def generate_voiceover(self, text, output_path):
        """Converts text to speech using Edge-TTS."""
        print("Generating voiceover...")
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        await communicate.save(output_path)
        return output_path

    def generate_subtitles(self, audio_path):
        """Generates subtitle segments using local Whisper."""
        print("Transcribing audio with Whisper for captions...")
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result.get('segments', [])

    def get_visuals(self, keywords, index, main_topic=""):
        """Fetches a single video clip from Pexels with randomized selection for variety."""
        import random
        if isinstance(keywords, str):
            keywords = [keywords]
            
        # Add main topic as a final keyword fallback
        if main_topic and main_topic not in keywords:
            keywords.append(main_topic)

        headers = {"Authorization": self.pexels_key}
        
        for query in keywords:
            print(f"Fetching visual for scene {index} using query: {query}")
            # Request more results to allow for randomization
            url = f"https://api.pexels.com/videos/search?query={query}&per_page=10&orientation=landscape&size=medium"
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                videos = response.json().get('videos', [])
                
                if videos:
                    # Pick a random video from the results to ensure variety
                    selected_video = random.choice(videos)
                    video_url = selected_video['video_files'][0]['link']
                    v_path = f"Data/temp/clip_scene_{index}.mp4"
                    v_data = requests.get(video_url).content
                    with open(v_path, 'wb') as f:
                        f.write(v_data)
                    return v_path
                else:
                    print(f"No visuals found for '{query}'. Trying next keyword...")
            except Exception as e:
                print(f"Error fetching visual for {query}: {e}")
                continue
        
        print(f"FAILED to find any visuals for scene {index}. Using fallback.")
        return None

    def render_video(self, topic, script, audio_path, scene_clips, subtitle_segments):
        """Mashes everything together with matched scenes and captions."""
        print("Rendering professional video with synced scenes and captions...")
        
        audio = AudioFileClip(audio_path)
        
        # Assemble the visual sequence with cinematic transitions
        final_clips = []
        last_valid_clip = None
        
        for i, (path, duration) in enumerate(scene_clips):
            current_clip = None
            
            if path and os.path.exists(path):
                try:
                    # Load and resize to a consistent professional 1080p canvas
                    current_clip = VideoFileClip(path).without_audio().resized(height=1080)
                    last_valid_clip = path 
                except Exception as e:
                    print(f"Error loading clip {path}: {e}")
                    current_clip = None

            if current_clip is None:
                if last_valid_clip and os.path.exists(last_valid_clip):
                    current_clip = VideoFileClip(last_valid_clip).without_audio().resized(height=1080)
                else:
                    continue 
            
            # 1. Loop and Trim
            if current_clip.duration < duration:
                from moviepy.video.fx.Loop import Loop
                current_clip = Loop(duration=duration).apply(current_clip)
            else:
                # Start at a random point if the clip is long enough, for more variety
                import random
                start_offset = 0
                if current_clip.duration > duration + 2:
                    start_offset = random.uniform(0, current_clip.duration - duration - 1)
                current_clip = current_clip.subclipped(start_offset, start_offset + duration)
            
            # 2. Add 'Ken Burns' Dynamic Zoom Effect (Cinematic feel)
            # Randomly decide to zoom in or zoom out
            import random
            is_zoom_in = random.choice([True, False])
            def zoom_effect(t):
                if is_zoom_in:
                    return 1 + 0.15 * (t / duration)
                else:
                    return 1.15 - 0.15 * (t / duration)
                
            current_clip = current_clip.resized(zoom_effect)
            
            # 3. Add Crossfade transition
            if i > 0:
                # Start 0.5s before the previous clip ends
                start_time = sum(d for _, d in scene_clips[:i]) - (i * 0.5)
                current_clip = current_clip.with_start(start_time)
                from moviepy.video.fx.CrossFadeIn import CrossFadeIn
                current_clip = CrossFadeIn(duration=0.5).apply(current_clip)
            else:
                current_clip = current_clip.with_start(0)

            final_clips.append(current_clip)
        
        if not final_clips:
            print("Error: No valid visual clips to render.")
            return None

        # Composite everything
        base_video = CompositeVideoClip(final_clips, size=(1920, 1080))
        
        # Create Caption Clips (Overlay)
        caption_clips = []
        for segment in subtitle_segments:
            duration = segment['end'] - segment['start']
            if duration <= 0: continue
            
            try:
                # Use absolute path for font to avoid "cannot open resource" errors
                font_path = r"C:\Windows\Fonts\arialbd.ttf"
                if not os.path.exists(font_path):
                    font_path = "Arial" # Fallback to generic name
                
                txt_clip = TextClip(
                    text=segment['text'].strip().upper(), # Uppercase for punchy look
                    font_size=55, # Reduced from 80 for better aesthetics
                    color='yellow', # Yellow is common in professional AI videos
                    font=font_path,
                    stroke_color='black',
                    stroke_width=3,
                    method='caption',
                    size=(int(base_video.w * 0.9), None)
                ).with_start(segment['start']).with_duration(duration).with_position(('center', 850))
                caption_clips.append(txt_clip)
            except Exception as e:
                print(f"Warning: Caption error: {e}")
        
        final_composite = CompositeVideoClip([base_video] + caption_clips).with_audio(audio).with_duration(audio.duration)
        
        output_path = f"Data/library/final_{int(time.time())}.mp4"
        final_composite.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        
        # Cleanup scene clips
        for path, _ in scene_clips:
            try: os.remove(path)
            except: pass
            
        return output_path

    def generate_content(self, topic_data):
        topic = topic_data['content']
        
        # 1. Generate Structured Scenes
        scenes = self.generate_script(topic)
        if not scenes: return None
        
        # 2. Voiceover (Full text)
        full_text = " ".join([s['text'] for s in scenes])
        audio_path = f"Data/temp/voiceover_{int(time.time())}.mp3"
        asyncio.run(self.generate_voiceover(full_text, audio_path))
        
        audio = AudioFileClip(audio_path)
        total_duration = audio.duration
        
        # 3. Calculate Scene Timings (proportional to text length)
        total_chars = sum(len(s['text']) for s in scenes)
        scene_clips = []
        for i, scene in enumerate(scenes):
            # Fetch one specific clip for this scene's keywords
            keywords = scene.get('keywords', [scene.get('keyword', topic)])
            clip_path = self.get_visuals(keywords, i, main_topic=topic)
            
            # Determine duration based on text weight, but add 0.5s for the crossfade overlap
            weight = len(scene['text']) / total_chars if total_chars > 0 else (1/len(scenes))
            scene_duration = (weight * total_duration)
            
            # Add 0.5s to all clips except the last one to allow for the crossfade overlap
            if i < len(scenes) - 1:
                scene_duration += 0.5
                
            scene_clips.append((clip_path, scene_duration))
        
        # 4. Captions (Whisper)
        subtitle_segments = self.generate_subtitles(audio_path)
        
        # 5. Render
        video_path = self.render_video(topic, full_text, audio_path, scene_clips, subtitle_segments)
        
        # Cleanup temp audio
        try: os.remove(audio_path)
        except: pass
        
        return {
            "video_path": video_path,
            "title": f"The Wonders of {topic}",
            "description": full_text
        }