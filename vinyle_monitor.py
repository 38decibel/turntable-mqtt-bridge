#!/usr/bin/env python3
import subprocess
import paho.mqtt.client as mqtt
import time

# --- Config ---
MQTT_HOST = "ipv4_du_broker_mqtt"
MQTT_PORT = 1883
MQTT_USER = "votre_user_mqtt"
MQTT_PASS = "votre_pass_mqtt"
MQTT_TOPIC = "vinyle/status"

SILENCE_THRESHOLD = 0.01     # Seuil RMS pour détecter la lecture
SILENCE_DURATION = 60        # Secondes de silence avant de passer à idle
CHECK_INTERVAL = 5           # Secondes entre chaque mesure

# --- MQTT ---
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(MQTT_HOST, MQTT_PORT)
client.loop_start()

def get_rms_level():
    """Mesure le niveau RMS via sox sur le stream Icecast."""
    try:
        result = subprocess.run(
            ["sox", "-t", "mp3", "http://localhost:8000/turntable.mp3", "-n",
             "trim", "0", "2", "stat"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stderr.splitlines():
            if "RMS" in line and "amplitude" in line:
                val = float(line.split()[-1])
                print(f"[DEBUG] RMS = {val}", flush=True)
                return val
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
    return 0.0

def publish(state):
    client.publish(MQTT_TOPIC, state, retain=True)
    print(f"[MQTT] -> {state}", flush=True)

# --- Boucle principale ---
current_state = None
silence_since = None

while True:
    rms = get_rms_level()
    is_playing = rms > SILENCE_THRESHOLD

    if is_playing:
        silence_since = None
        if current_state != "playing":
            current_state = "playing"
            publish("playing")
    else:
        if silence_since is None:
            silence_since = time.time()
        elif time.time() - silence_since >= SILENCE_DURATION:
            if current_state != "idle":
                current_state = "idle"
                publish("idle")

    time.sleep(CHECK_INTERVAL)
