from topic_manager import TopicManager
from video_engine import VideoEngine
import time
import os
import yaml
import shutil

def check_disk_space(path=".", min_gb=1):
    """Returns True if there is at least min_gb of free space."""
    _, _, free = shutil.disk_usage(path)
    free_gb = free / (2**30)
    return free_gb >= min_gb

def start_bot():
    """Main entry point to start the autonomous YT_BOT pipeline"""
    print("--- YT_BOT v2.0: AUTONOMOUS SYSTEM INITIALIZING ---")
    
    # Load settings
    with open("config/settings.yaml", "r") as f:
        settings = yaml.safe_load(f)
    
    check_interval = settings['automation_settings']['check_interval_seconds']
    retry_delay = settings['automation_settings']['retry_delay_seconds']

    tm = TopicManager()
    ve = VideoEngine()

    # Reset any topics that were interrupted
    tm.reset_stuck_topics()

    while True:
        try:
            if not check_disk_space():
                print(f"[{time.strftime('%H:%M:%S')}] CRITICAL: Low disk space! Waiting for cleanup...")
                time.sleep(300)
                continue
                
            print(f"[{time.strftime('%H:%M:%S')}] Checking queue...")
            current_job = tm.get_next_topic()
            
            if current_job:
                print(f"Task Identified: {current_job['content']}")
                
                # Content Generation
                video_info = ve.generate_content(current_job)
                
                if video_info:
                    tm.mark_as_done(current_job['id'], video_info['video_path'])
                    print(f"MISSION COMPLETE: {video_info['video_path']}")
                else:
                    print("Generation failed. Rolling back topic status.")
                    tm.rollback_topic(current_job['id'])
            else:
                print(f"Sleeping for {check_interval} seconds...")
                time.sleep(check_interval)
                
        except ConnectionError:
            print(f"Network Error! Re-trying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        except Exception as e:
            print(f"Unexpected Error: {e}")
            time.sleep(60) # Short sleep on generic error

if __name__ == "__main__":
    start_bot()