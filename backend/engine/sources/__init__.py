from engine.sources.base import Source

# Instances, not classes. Empty until Bevy (#13): REGISTRY["bevy"] = Bevy().
REGISTRY: dict[str, Source] = {}
