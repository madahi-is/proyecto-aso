from util.exports_manager import ExportsManager

try:
    parsed = ExportsManager.list_parsed()
    # parsed es una lista de dicts: {'path', 'hosts', 'raw', 'lineno'}
    for e in parsed:
        print(e['lineno'], e['path'], e['hosts'])
except Exception as e:
    print("Error:", e)
