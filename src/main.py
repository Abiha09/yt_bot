from topic_manager import TopicManager
from video_engine import VideoEngine
from uploader import YouTubeUploader
import time

def start_bot():
    """Main entry point to start the autonomous YT_BOT pipeline"""
    print("🚀 --- YT_BOT v1.0: SYSTEM INITIALIZING ---")
    
    # Initialize Core Modules
    tm = TopicManager()
    ve = VideoEngine()
    yt = YouTubeUploader()

    # STEP 1: Fetch Task from Queue
    current_job = tm.get_next_topic()
    
    if current_job:
        print(f"🎯 Task Identified: {current_job['content']}")
        
        # STEP 2: Content Generation (Script + Video)
        video_info = ve.generate_content(current_job)
        
        # STEP 3: Artificial Processing Delay (Simulating rendering time)
        print("⏳ Processing: Encoding high-quality video (Simulated Delay)...")
        time.sleep(2)
        
        # STEP 4: YouTube API Integration (Upload)
        final_url = yt.upload_to_youtube(video_info)
        
        # STEP 5: Finalize and Log
        tm.mark_as_done(current_job['id'], final_url)
        
        print(f"🏁 MISSION COMPLETE: Video is now live at: {final_url}")
    else:
        print("📭 Status: Queue is empty. No pending tasks found.")

if __name__ == "__main__":
    start_bot()