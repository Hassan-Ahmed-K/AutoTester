import re
import os

expert_names = [
    'ExpertMACD - Copy.ex5', 'ExpertMACD.ex5', 'ExpertMAMA.ex5', 
    'ExpertMAPSAR.ex5', 'ExpertMAPSARSizeOptimized.ex5', 
    'ExpertMAPSARSizeOptimized_1.ex5', 'ExpertMAPSARSizeOptimized_2.1.ex5', 
    'ChartInChart.ex5', 'Controls.ex5', 'Correlation Matrix 3D.ex5', 
    'MACD Sample.ex5', 'Math 3D.ex5', 'Math 3D Morpher.ex5', 
    'Moving Average.ex5', 'BlackCrows WhiteSoldiers CCI.ex5', 
    'BlackCrows WhiteSoldiers MFI.ex5', 'BlackCrows WhiteSoldiers RSI.ex5', 
    'BlackCrows WhiteSoldiers Stoch.ex5', 'BullishBearish Engulfing CCI.ex5', 
    'BullishBearish Engulfing MFI.ex5', 'BullishBearish Engulfing RSI.ex5', 
    'BullishBearish Engulfing Stoch.ex5', 'BullishBearish Harami CCI.ex5', 
    'BullishBearish Harami MFI.ex5', 'BullishBearish Harami RSI.ex5', 
    'BullishBearish Harami Stoch.ex5', 'BullishBearish MeetingLines CCI.ex5', 
    'BullishBearish MeetingLines MFI.ex5', 'BullishBearish MeetingLines RSI.ex5', 
    'BullishBearish MeetingLines Stoch.ex5', 'DarkCloud PiercingLine CCI.ex5', 
    'DarkCloud PiercingLine MFI.ex5', 'DarkCloud PiercingLine RSI.ex5', 
    'DarkCloud PiercingLine Stoch.ex5', 'HangingMan Hammer CCI.ex5', 
    'HangingMan Hammer MFI.ex5', 'HangingMan Hammer RSI.ex5', 
    'HangingMan Hammer Stoch.ex5', 'MorningEvening StarDoji CCI.ex5', 
    'MorningEvening StarDoji MFI.ex5', 'MorningEvening StarDoji RSI.ex5', 
    'MorningEvening StarDoji Stoch.ex5'
]

def split_name_version(filename):
    # remove extension
    name, _ = os.path.splitext(filename)

    # regex to catch version patterns like _1, _2.1, -v1.2, etc.
    match = re.search(r'[_ -]?(\d+(\.\d+)*)$', name)
    if match:
        version = match.group(1)
        name = name[:match.start()].strip(" _-")
    else:
        version = None
    return name, version

results = [split_name_version(f) for f in expert_names]

for name, version in results:
    print(f"Name: {name}, Version: {version}")
