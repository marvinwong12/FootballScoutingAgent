from src.engine.scout_engine import ScoutEngine

def main():
    engine = ScoutEngine()
    
    if engine._df is None or engine._df.empty:
        print("❌ CRITICAL: The ScoutEngine loaded an empty DataFrame. Check your CSV path in scout_engine.py!")
        return
        
    print(f"✅ Engine loaded successfully with {len(engine._df)} players.")
    
    # Print the first 10 player names in your dataset so we can copy one exactly
    print("\nHere are the first 10 valid player names you can test:")
    names = engine._df.index.tolist()[:10]
    for name in names:
        print(f" - {name}")

if __name__ == "__main__":
    main()