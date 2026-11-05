from engine.sources.base import Source
from engine.sources.bevy import Bevy

# Instances, not classes. The key is `sources.platform` and `NormalizedEvent.source_platform`.
REGISTRY: dict[str, Source] = {"bevy": Bevy()}
