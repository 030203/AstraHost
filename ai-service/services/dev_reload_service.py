class DevReloadService:
    def __init__(self, watched_files):
        self.watched_files = watched_files

    def token(self):
        latest_mtime = 0
        for file_path in self.watched_files:
            if file_path.exists():
                latest_mtime = max(latest_mtime, int(file_path.stat().st_mtime_ns))
        return str(latest_mtime)
