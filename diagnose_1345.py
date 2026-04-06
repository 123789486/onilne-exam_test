def inspect():
    with open('temp_bank.txt', 'r', encoding='gb18030', errors='ignore') as f:
        text = f.read()
    
    # Let's find some strings that should be answers but might be formatted as '---'
    # Row 1345 previously had '1BC' in answer.
    # Let's find 1BC in the text.
    
    matches = list(re.finditer(r'[\n\r]+.*1BC', text))
    if matches:
        print(f"Found '1BC' markers: {len(matches)}")
        for m in matches[:3]:
            start = m.start() - 200
            end = m.end() + 200
            print(f"\n--- Context near 1BC at {start} ---")
            print(text[max(0, start):min(len(text), end)])
    else:
        print("Could not find '1BC' in raw text directly.")

    # Let's see Row 1345 in the current Excel to find its stem
    import pandas as pd
    df = pd.read_excel('题库_竞赛_标准化.xlsx')
    row = df.iloc[1344]
    stem = str(row['题干'])[:50]
    print(f"\nSearching for stem in text: '{stem}'")
    
    stem_m = list(re.finditer(re.escape(stem), text))
    if stem_m:
        for m in stem_m:
            start = m.start() - 100
            end = m.end() + 500
            print(f"\n--- Context in Raw Text at {start} ---")
            print(text[max(0, start):min(len(text), end)])

if __name__ == "__main__":
    import re
    inspect()
