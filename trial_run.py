import sys
import os
sys.path.append(os.path.abspath("src"))
import asyncio

def trial_run():
    from video_engine import VideoEngine
    
    print("--- YT_BOT PROFESSIONAL SCENE-SYNC TRIAL ---")
    ve = VideoEngine()
    
    topic_data = {"id": 1001, "content": "The Essential Benefits of Daily Exercise"}
    
    print(f"Starting professional generation for: {topic_data['content']}")
    result = ve.generate_content(topic_data)
    
    if result:
        print(f"SUCCESS! Professional video generated at: {result['video_path']}")
        print(f"Final Script Duration: approx {len(result['description'].split()) / 2.5:.1f} seconds")
    else:
        print("FAILURE: Video generation failed.")

if __name__ == "__main__":
    trial_run()
