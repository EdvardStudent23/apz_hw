import requests
import json
import time

BASE_URL = "http://localhost:8000/process"

def send_test_transactions():
    print("10 message start")
    for i in range(1, 11):
        msg_text = f"msg{i}"
        payload = {
            "user_id": "user1",
            "amount": 10,
            "msg": msg_text
        }
        try:
            response = requests.post(BASE_URL, json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"[SUCCESS] Sent: {msg_text} | Received Transaction ID: {data['transaction_id']} | New Balance: {data['balance']}")
            else:
                print(f"[ERROR] Failed to send {msg_text}. Status code: {response.status_code}")
        except Exception as e:
            print(f"[CRITICAL] Could not connect to Facade Service: {e}")
            break

    print("Finished")

if __name__ == "__main__":
    send_test_transactions()