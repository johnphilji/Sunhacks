import requests
import json

def test_system():
    url = "http://127.0.0.1:8000/run-system"
    payload = {
        "strategy": "Buy when price is above SMA-50. Sell when below.",
        "symbol": "AAPL",
        "period": "1y"
    }
    
    print(f"Testing system with: {payload['strategy']} on {payload['symbol']}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print("\n--- TEST SUCCESSFUL ---")
        print(f"Original Profit: {data['original_results']['profit_pct']}%")
        print(f"Optimized Profit: {data['optimized_results']['profit_pct']}%")
        print(f"Risk Level: {data['risk_analysis']['level'].upper()}")
        print(f"Final Decision: {data['final_decision']['chosen'].upper()}")
        print("\nDecision Reasoning:")
        print(data['final_decision']['reasoning'])
        
    except Exception as e:
        print(f"\n--- TEST FAILED ---")
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Server response: {e.response.text}")

if __name__ == "__main__":
    test_system()
