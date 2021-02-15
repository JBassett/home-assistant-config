class Autopi:
    
    def __init__(self, webhook_id):
        self.latest = None
        self._callbacks = set()

        self.webhook_id = webhook_id
    
    def update(self, request):
        self.latest = request
        for callback in self._callbacks:
            callback()

    def register_callback(self, callback):
        """Register callback, called when job changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

# {
#     "soc": 69,
#     "power": 10,
#     "charging": true,
#     "battery_temp": 15,
#     "pi_voltage": 12.1,
#     "voltage": -1,
#     "current": -1,
#     "shifter": 8,
#     "external_temp": 0.5,
#     "lat": 43,
#     "lon": -77,
#     "alt": 105.5
# }