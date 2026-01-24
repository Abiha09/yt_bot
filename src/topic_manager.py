import json
import os
from datetime import datetime
import yaml

class TopicManager:
    """Handles reading from queue.json, daily limits, and history logging."""
    
    def __init__(self):
        self.queue_file = os.path.join("Data", "queue.json")
        self.completed_file = os.path.join("Data", "completed.json")
        self.state_file = os.path.join("Data", "bot_state.json")
        self.settings_file = os.path.join("config", "settings.yaml")
        self.load_settings()

    def load_settings(self):
        with open(self.settings_file, 'r') as f:
            self.settings = yaml.safe_load(f)
        self.daily_limit = self.settings.get('automation_settings', {}).get('daily_limit', 3)

    def get_daily_count(self):
        """Returns the number of videos created today."""
        if not os.path.exists(self.state_file):
            return 0
        
        today = datetime.now().strftime("%Y-%m-%d")
        with open(self.state_file, 'r') as f:
            try:
                state = json.load(f)
            except:
                return 0
            
        if state.get("date") == today:
            return state.get("count", 0)
        return 0

    def increment_daily_count(self):
        """Increments the count of videos created today."""
        today = datetime.now().strftime("%Y-%m-%d")
        count = self.get_daily_count() + 1
        
        with open(self.state_file, 'w') as f:
            json.dump({"date": today, "count": count}, f)

    def reset_stuck_topics(self):
        """Resets any topics with 'processing' status back to 'pending'."""
        if not os.path.exists(self.queue_file):
            return
            
        with open(self.queue_file, 'r') as f:
            try:
                topics = json.load(f)
            except:
                return

        changed = False
        for t in topics:
            if t.get('status') == 'processing':
                t['status'] = 'pending'
                changed = True
        
        if changed:
            print("🔄 System: Resetting stuck 'processing' topics to 'pending'...")
            self.save_topics(topics)

    def get_next_topic(self):
        """Fetches the first pending topic, respecting daily limits."""
        if self.get_daily_count() >= self.daily_limit:
            print(f"Daily limit of {self.daily_limit} reached. Waiting for tomorrow...")
            return None

        if not os.path.exists(self.queue_file):
            print("Error: Data/queue.json not found!")
            return None
            
        with open(self.queue_file, 'r') as f:
            try:
                topics = json.load(f)
            except:
                print("Error: Could not read queue.json")
                return None
        
        for t in topics:
            if t['status'] == 'pending':
                t['status'] = 'processing'
                self.save_topics(topics)
                return t
        
        # If no pending, auto-generate from permanent_topic if enabled
        perm_topic = self.settings.get('automation_settings', {}).get('permanent_topic')
        if perm_topic:
            import random
            variations = ["latest news on", "mystery of", "future secrets of", "shocking facts about", "the history of"]
            prefix = random.choice(variations)
            
            new_id = max([t['id'] for t in topics], default=0) + 1
            new_content = f"{prefix} {perm_topic}"
            
            # Check if we should clear old pending topics that don't match the new perm_topic
            # This is a bit aggressive, but solves the user's "stuck on old topic" issue.
            new_job = {
                "id": new_id,
                "content": new_content,
                "status": "processing"
            }
            topics.append(new_job)
            self.save_topics(topics)
            print(f"System: Auto-generated new job based on Permanent Topic: {new_job['content']}")
            return new_job
            
        return None

    def clear_pending_queue(self):
        """Clears all pending and processing topics from the queue."""
        if not os.path.exists(self.queue_file):
            return
            
        with open(self.queue_file, 'r') as f:
            topics = json.load(f)
            
        new_topics = [t for t in topics if t.get('status') == 'completed']
        self.save_topics(new_topics)
        print("🧹 System: Pending and Processing queue cleared.")

    def save_topics(self, topics):
        with open(self.queue_file, 'w') as f:
            json.dump(topics, f, indent=4)

    def rollback_topic(self, topic_id):
        """Resets a topic's status from processing back to pending."""
        if not os.path.exists(self.queue_file):
            return

        with open(self.queue_file, 'r') as f:
            topics = json.load(f)
        
        for t in topics:
            if t['id'] == topic_id:
                t['status'] = 'pending'
                break
        
        self.save_topics(topics)

    def mark_as_done(self, topic_id, video_path):
        """Moves the topic to history and updates daily count."""
        print(f"System: Moving Topic ID {topic_id} to completion history...")
        
        # Load all topics to update the specific one
        if not os.path.exists(self.queue_file):
            return

        with open(self.queue_file, 'r') as f:
            topics = json.load(f)
        
        for t in topics:
            if t['id'] == topic_id:
                t['status'] = 'completed'
                t['video_path'] = video_path
                break
        
        self.save_topics(topics)
        self.increment_daily_count()

        history_entry = {
            "topic_id": topic_id,
            "completion_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "video_path": video_path,
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