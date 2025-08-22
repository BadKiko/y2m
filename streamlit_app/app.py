import streamlit as st
import requests
import json
import os
from datetime import datetime

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_URL = f"{API_BASE_URL}/api/v1"

# Page configuration
st.set_page_config(
    page_title="MQTT2Yandex Bridge",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None

def make_api_request(endpoint, method="GET", data=None, auth_required=True):
    """Make API request with authentication"""
    url = f"{API_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    if auth_required and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)

        if response.status_code == 401:
            st.error("Authentication required")
            st.session_state.authenticated = False
            st.session_state.token = None
            st.rerun()

        return response

    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None

def login():
    """Login form"""
    st.title("🔐 MQTT2Yandex Bridge")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if username and password:
                response = make_api_request(
                    "/auth/login",
                    method="POST",
                    data={"username": username, "password": password},
                    auth_required=False
                )

                if response and response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.authenticated = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Login failed. Please check your credentials.")
            else:
                st.error("Please enter both username and password")

def main_app():
    """Main application interface"""
    st.title("🔗 MQTT2Yandex Bridge")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Dashboard", "Devices", "Scenarios", "Yandex", "ADB Console", "Settings"]
    )

    if page == "Dashboard":
        show_dashboard()
    elif page == "Devices":
        show_devices()
    elif page == "Scenarios":
        show_scenarios()
    elif page == "Yandex":
        show_yandex()
    elif page == "ADB Console":
        show_adb_console()
    elif page == "Settings":
        show_settings()

def show_dashboard():
    """Dashboard page"""
    st.header("📊 Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("System Status")
        # Get system status
        response = make_api_request("/health")
        if response and response.status_code == 200:
            st.success("✅ Backend API Online")
        else:
            st.error("❌ Backend API Offline")

    with col2:
        st.subheader("MQTT Status")
        response = make_api_request("/mqtt/status")
        if response and response.status_code == 200:
            data = response.json()
            if data["connected"]:
                st.success("✅ MQTT Connected")
            else:
                st.error("❌ MQTT Disconnected")

    with col3:
        st.subheader("Active Devices")
        response = make_api_request("/devices")
        if response and response.status_code == 200:
            devices = response.json()
            st.info(f"📱 {len(devices)} Devices")

def show_devices():
    """Devices management page"""
    st.header("📱 Device Management")

    tab1, tab2 = st.tabs(["📋 Device List", "➕ Add Device"])

    with tab1:
        st.subheader("Device List")

        # Get devices
        response = make_api_request("/devices")
        if response and response.status_code == 200:
            devices = response.json()

            if devices:
                for device in devices:
                    with st.expander(f"📱 {device['name']} ({device['type']})"):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write(f"**ID:** {device['id']}")
                            st.write(f"**Type:** {device['type']}")

                        with col2:
                            st.write(f"**MQTT Base Topic:** {device['mqtt_base_topic']}")
                            st.write(f"**State Topic:** {device['state_topic']}")

                        with col3:
                            st.write(f"**Active:** {'✅' if device['is_active'] else '❌'}")
                            st.write(f"**Created:** {device['created_at'][:10]}")

                        # Control buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("🔄 Refresh State", key=f"refresh_{device['id']}"):
                                st.info(f"Refreshing state for {device['name']}")

                        with col2:
                            if st.button("🔧 Edit", key=f"edit_{device['id']}"):
                                st.info(f"Edit functionality for {device['name']}")

                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_{device['id']}"):
                                delete_response = make_api_request(f"/devices/{device['id']}", method="DELETE")
                                if delete_response and delete_response.status_code == 200:
                                    st.success(f"Device {device['name']} deleted!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete device")
            else:
                st.info("No devices found. Add your first device!")

    with tab2:
        st.subheader("Add New Device")

        with st.form("add_device_form"):
            name = st.text_input("Device Name", placeholder="e.g., living_room_light")
            device_type = st.selectbox("Device Type", ["switch", "sensor", "light", "climate"])
            meta = st.text_area("Metadata (JSON)", placeholder='{"room": "living_room"}')

            submit = st.form_submit_button("Add Device")

            if submit:
                if name and device_type:
                    try:
                        device_data = {
                            "name": name,
                            "type": device_type,
                            "meta": json.loads(meta) if meta else {}
                        }

                        response = make_api_request("/devices", method="POST", data=device_data)

                        if response and response.status_code == 200:
                            st.success(f"Device '{name}' created successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to create device")

                    except json.JSONDecodeError:
                        st.error("Invalid JSON in metadata field")
                else:
                    st.error("Please fill in all required fields")

def show_scenarios():
    """Scenarios management page"""
    st.header("🎬 Scenario Management")
    st.info("Scenario management functionality will be implemented here")

def show_yandex():
    """Yandex integration page"""
    st.header("🇷🇺 Yandex Integration")
    st.info("Yandex Home integration functionality will be implemented here")

def show_adb_console():
    """ADB console page"""
    st.header("📱 ADB Console")
    st.info("ADB console functionality will be implemented here")

def show_settings():
    """Settings page"""
    st.header("⚙️ Settings")
    st.info("Application settings will be implemented here")

# Main application logic
if not st.session_state.authenticated:
    login()
else:
    main_app()

    # Logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.token = None
        st.rerun()
