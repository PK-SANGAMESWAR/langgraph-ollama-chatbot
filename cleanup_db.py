import os
import glob

# Get the current directory (databasee folder)
current_dir = os.path.dirname(os.path.abspath(__file__))

# List of patterns to match unwanted database files
patterns = [
    "chatbot_ch*.db",
    "chatbot_ch*.db-shm",
    "chatbot_ch*.db-wal",
    "chatbot.db",
    "chatbot.db-shm", 
    "chatbot.db-wal"
]

# Files to keep
keep_files = ["chatbot_checkpoints.db", "chatbot_checkpoints.db-shm", "chatbot_checkpoints.db-wal"]

print("🗑️  Cleaning up database files...\n")

deleted_count = 0

for pattern in patterns:
    files = glob.glob(os.path.join(current_dir, pattern))
    
    for file in files:
        filename = os.path.basename(file)
        
        # Skip files we want to keep
        if filename in keep_files:
            print(f"⏭️  Skipping: {filename}")
            continue
        
        try:
            os.remove(file)
            print(f"✅ Deleted: {filename}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ Error deleting {filename}: {e}")

print(f"\n✨ Cleanup complete! Deleted {deleted_count} file(s).")
print(f"📁 Kept: chatbot_checkpoints.db (and its associated files)")