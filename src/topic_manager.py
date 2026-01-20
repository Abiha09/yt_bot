import json
import os
from datetime import datetime

class TopicManager:
    """Handles reading from queue.json and logging to completed.json"""
    
    def __init__(self):
        self.queue_file = os.path.join("data", "queue.json")
        self.completed_file = os.path.join("data", "completed.json")

    def get_next_topic(self):
        """Fetches the first topic with 'pending' status from the queue"""
        if not os.path.exists(self.queue_file):
            print("❌ Error: data/queue.json not found!")
            return None
            
        with open(self.queue_file, 'r') as f:
            topics = json.load(f)
        
        for t in topics:
            if t['status'] == 'pending':
                return t
        return None

    def mark_as_done(self, topic_id, video_url):
        """Moves the topic to history and updates the completion record"""
        print(f"📦 System: Moving Topic ID {topic_id} to completion history...")
        
        history_entry = {
            "topic_id": topic_id,
            "completion_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "youtube_url": video_url,
            "status": "success"
        }

        completed_data = []
        if os.path.exists(self.completed_file):
            with open(self.completed_file, 'r') as f:
                try:
                    completed_data = json.load(f)
                except: 
                    completed_data = []
        
        completed_data.append(history_entry)
        with open(self.completed_file, 'w') as f:
            json.dump(completed_data, f, indent=4)