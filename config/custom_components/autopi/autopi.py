import datetime

class Autopi:
    
    def __init__(self, webhook_id):
        self.update_time = datetime.datetime.min
        self.latest = None
        self._callbacks = set()

        self.webhook_id = webhook_id
    
    def update(self, request):
        self.update_time = datetime.datetime.utcnow()
        self.latest = request
        for callback in self._callbacks:
            callback()

    def register_callback(self, callback):
        """Register callback, called when job changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        """Remove previously registered callback."""
        self._callbacks.discard(callback)
