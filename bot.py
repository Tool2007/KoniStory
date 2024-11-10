import requests
import json
import time
from eth_account import Account
import secrets
import base64
import urllib.parse
import concurrent.futures
import os

# Configuration
API_BASE_URL = "https://sp-odyssey-api.playnation.app/api"
HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://story-protocol-odyssey-tele.playnation.app',
    'referer': 'https://story-protocol-odyssey-tele.playnation.app/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
}

def generate_wallet():
    private_key = secrets.token_hex(32)
    account = Account.from_key(private_key)
    return {
        'address': account.address,
        'private_key': private_key
    }

def read_init_data_list():
    try:
        with open('query.txt', 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("Error: query.txt file not found!")
        return None

def login(wallet_address, init_data, referral_code="3iILL6YnL"):
    url = f"{API_BASE_URL}/account/login"
    
    payload = {
        "address": wallet_address,
        "referralCode": referral_code,
        "initData": init_data
    }
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Login error: {str(e)}")
        return None

def get_task_list(token):
    url = f"{API_BASE_URL}/task/history"
    headers = {**HEADERS, 'authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Get task list error: {str(e)}")
        return None

def submit_task(token, task_id):
    url = f"{API_BASE_URL}/task/submit"
    headers = {**HEADERS, 'authorization': f'Bearer {token}'}
    
    payload = {
        "taskId": task_id,
        "extrinsicHash": "",
        "network": ""
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Submit task error: {str(e)}")
        return None

def process_tasks(token, wallet_address):
    print("Starting task ...")
    print()
    
    # Get task list
    tasks = get_task_list(token)
    if not tasks:
        print("Failed to get task list!")
        return
    
    # Filter incomplete tasks
    incomplete_tasks = [task for task in tasks if task.get('status') is None]
    
    # Process each incomplete task
    for task in incomplete_tasks:
        task_id = task['id']
        task_name = task['name']
        print(f"Processing task: {task_name} (ID: {task_id})")
        
        # Submit task
        result = submit_task(token, task_id)
        if result and result.get('success'):
            print(f"✅ Successfully completed task: {task_name}")
        else:
            print(f"❌ Failed to complete task: {task_name}")

def process_single_account(init_data, index):
    # Generate new wallet
    wallet = generate_wallet()
    print(f"[Account {index}] Generated wallet address: {wallet['address']}")
    print(f"[Account {index}] Attempting login...")
    
    # Attempt login
    login_response = login(wallet['address'], init_data)
    
    if login_response:
        print(f"[Account {index}] Login successful!")
        token = login_response.get('token')
        
        if token:
            # Process tasks
            process_tasks(token, wallet['address'])
            
            # Save wallet info
            if not os.path.exists('accounts'):
                os.makedirs('accounts')
            wallet_file = f"accounts/wallet_{index}_{wallet['address']}.json"
            with open(wallet_file, 'w') as f:
                json.dump(wallet, f, indent=4)
            print(f"[Account {index}] Wallet details saved to {wallet_file}")
        else:
            print(f"[Account {index}] No token found in login response!")
    else:
        print(f"[Account {index}] Login failed!")

def main():
    # Read init data list from query.txt
    init_data_list = read_init_data_list()
    if not init_data_list:
        return
    
    print(f"Found {len(init_data_list)} accounts to process\n")
    
    # Process each account sequentially
    for index, init_data in enumerate(init_data_list, 1):
        try:
            print("="*50)
            print(f"Processing account {index} of {len(init_data_list)}")
            print("="*50)
            print()
            process_single_account(init_data, index)
            
            # Add delay between accounts
            if index < len(init_data_list):
                print("\nWaiting 5 seconds before processing next account...")
                time.sleep(5)
                print()
                
        except Exception as e:
            print(f"Error processing account {index}: {str(e)}")
            continue

if __name__ == "__main__":
    main()
