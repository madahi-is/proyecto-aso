from util.exports_manager import ExportsManager
import json

print(json.dumps(ExportsManager.list_parsed(), indent=2))
