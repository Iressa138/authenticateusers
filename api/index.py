from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import uuid
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLAYFAB_API_URL = "https://{title_id}.playfabapi.com"
DEVICE_MODEL = "Oculus Quest"
DEVICE_OS = "Android"

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "PlayFab Proxy"}), 200

@app.route('/auth/login', methods=['POST'])
def login_with_device():
    """
    Proxy login that spoofs device as Oculus Quest
    Expects JSON body with: title_id, custom_id (optional), create_account (optional)
    """
    try:
        data = request.get_json()
        
        title_id = data.get('title_id')
        custom_id = data.get('custom_id', str(uuid.uuid4()))
        create_account = data.get('create_account', True)
        
        if not title_id:
            return jsonify({"error": "title_id is required"}), 400
        
        playfab_url = f"{PLAYFAB_API_URL.format(title_id=title_id)}/Client/LoginWithCustomID"
        
        payload = {
            "TitleId": title_id,
            "CustomId": custom_id,
            "CreateAccount": create_account,
            "InfoRequestParameters": {
                "GetUserAccountInfo": True,
                "GetUserInventory": True,
                "GetUserVirtualCurrency": True,
                "GetPlayerProfile": True,
                "GetCharacterInventories": False,
                "GetCharacterList": False,
                "GetTitleData": False,
                "GetUserData": True,
                "GetUserReadOnlyData": False
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-PlayFabSDK": "UnitySDK-2.0",
            "X-ReportErrorAsSuccess": "true"
        }
        
        logger.info(f"Attempting login for CustomID: {custom_id} with TitleID: {title_id}")
        
        response = requests.post(playfab_url, json=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('code') == 200:
            logger.info(f"Login successful for {custom_id}")
            
            session_ticket = response_data['data'].get('SessionTicket')
            playfab_id = response_data['data'].get('PlayFabId')
            
            if session_ticket:
                update_device_info(title_id, session_ticket)
            
            return jsonify({
                "success": True,
                "data": response_data['data'],
                "custom_id": custom_id,
                "spoofed_device": DEVICE_MODEL
            }), 200
        else:
            logger.error(f"Login failed: {response_data}")
            return jsonify({
                "success": False,
                "error": response_data
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Exception during login: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/auth/android-login', methods=['POST'])
def login_with_android():
    """
    Login using Android Device ID and spoof as Oculus Quest
    """
    try:
        data = request.get_json()
        
        title_id = data.get('title_id')
        android_device_id = data.get('android_device_id', str(uuid.uuid4()))
        create_account = data.get('create_account', True)
        
        if not title_id:
            return jsonify({"error": "title_id is required"}), 400
        
        playfab_url = f"{PLAYFAB_API_URL.format(title_id=title_id)}/Client/LoginWithAndroidDeviceID"
        
        payload = {
            "TitleId": title_id,
            "AndroidDeviceId": android_device_id,
            "CreateAccount": create_account,
            "OS": DEVICE_OS,
            "AndroidDevice": DEVICE_MODEL,
            "InfoRequestParameters": {
                "GetUserAccountInfo": True,
                "GetUserInventory": True,
                "GetUserVirtualCurrency": True,
                "GetPlayerProfile": True,
                "GetUserData": True
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-PlayFabSDK": "UnitySDK-2.0",
            "X-ReportErrorAsSuccess": "true"
        }
        
        logger.info(f"Attempting Android login for DeviceID: {android_device_id}")
        
        response = requests.post(playfab_url, json=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('code') == 200:
            logger.info(f"Android login successful for {android_device_id}")
            
            return jsonify({
                "success": True,
                "data": response_data['data'],
                "android_device_id": android_device_id,
                "spoofed_device": DEVICE_MODEL
            }), 200
        else:
            logger.error(f"Android login failed: {response_data}")
            return jsonify({
                "success": False,
                "error": response_data
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Exception during Android login: {str(e)}")
        return jsonify({"error": str(e)}), 500

def update_device_info(title_id, session_ticket):
    """
    Update player's device info to Oculus Quest
    """
    try:
        playfab_url = f"{PLAYFAB_API_URL.format(title_id=title_id)}/Client/UpdateUserData"
        
        payload = {
            "Data": {
                "DeviceModel": DEVICE_MODEL,
                "DeviceOS": DEVICE_OS
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Authorization": session_ticket,
            "X-PlayFabSDK": "UnitySDK-2.0"
        }
        
        response = requests.post(playfab_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Device info updated to {DEVICE_MODEL}")
        else:
            logger.warning(f"Failed to update device info: {response.text}")
            
    except Exception as e:
        logger.error(f"Exception updating device info: {str(e)}")

@app.route('/api/proxy', methods=['POST'])
def proxy_api_call():
    """
    Generic proxy for any PlayFab API call with session ticket
    """
    try:
        data = request.get_json()
        
        title_id = data.get('title_id')
        endpoint = data.get('endpoint')
        session_ticket = data.get('session_ticket')
        payload = data.get('payload', {})
        
        if not all([title_id, endpoint, session_ticket]):
            return jsonify({"error": "title_id, endpoint, and session_ticket are required"}), 400
        
        playfab_url = f"{PLAYFAB_API_URL.format(title_id=title_id)}{endpoint}"
        
        headers = {
            "Content-Type": "application/json",
            "X-Authorization": session_ticket,
            "X-PlayFabSDK": "UnitySDK-2.0"
        }
        
        response = requests.post(playfab_url, json=payload, headers=headers)
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        logger.error(f"Exception in proxy: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("PlayFab Proxy Server Starting")
    print(f"Device Model Spoof: {DEVICE_MODEL}")
    print(f"Device OS Spoof: {DEVICE_OS}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
