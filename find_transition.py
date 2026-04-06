import re

def find_transition():
    with open('temp_bank.txt', 'r', encoding='gb18030', errors='ignore') as f:
        text = f.read()
    
    # Let's count questions incrementally and see the answer markers.
    # Searching for either 【正确答案】 or --- followed by an option.
    
    # We find all blocks starting with 【...选题】
    blocks = re.split(r'(?=【(?:单选|多选|判断|单选题|多选题|判断题)】)', text)
    print(f"Total blocks split: {len(blocks)}")
    
    # Check Row 1345 (approx)
    # Actually, in Excel it's Row 1345.
    # Total entries I parsed was 2905.
    # Let's find index 1340 to 1360 in the split blocks.
    
    print("\n--- Inspecting Blocks 1340-1360 ---")
    for i in range(1340, min(len(blocks), 1360)):
        print(f"Block {i}:")
        print(blocks[i].strip()[:300])
        print("---")

    print("\n--- Inspecting Blocks 2260-2280 ---")
    for i in range(2260, min(len(blocks), 2280)):
        print(f"Block {i}:")
        print(blocks[i].strip()[:300])
        print("---")

if __name__ == "__main__":
    find_transition()
