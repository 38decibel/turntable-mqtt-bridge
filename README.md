# turntable-mqtt-bridge

Détection automatique de la lecture d'une platine vinyle USB, envoi de l'état via MQTT et lecture automatique d'une enceinte Sonos par automatisation Home Assistant.

## Architecture

```
Platine USB → Raspberry Pi Zero → Darkice → Icecast (stream MP3)
                                       ↓
                              vinyle_monitor.py
                              (détection niveau audio RMS)
                                       ↓
                              MQTT Broker (Mosquitto)
                                       ↓
                              Home Assistant Automation
                                       ↓
                              Sonos (bascule source + volume)
```

## Matériel requis

- Raspberry Pi Zero (ou tout autre modèle)
- Carte son USB (ex: USB AUDIO CODEC)
- Platine vinyle avec sortie audio usb
- Home Assistant avec add-on Mosquitto MQTT
- Enceinte Sonos (ou autre !)

## Prérequis logiciels

Sur le Raspberry Pi :
- Raspberry Pi OS
- Darkice + Icecast2 (pour le stream audio)
- Sox avec support MP3
- Python 3
- paho-mqtt

## Installation

### 1. Installer les dépendances

```bash
sudo apt update
sudo apt install sox libsox-fmt-mp3 python3 python3-paho-mqtt
```

### 2. Installer Darkice et Icecast

https://github.com/basdp/USB-Turntables-to-Sonos-with-RPi

### 3. Vérifier le stream mp3

Darkice capture le flux audio de la carte son USB et l'envoie vers Icecast.
Vérifier (depuis le pi zero) que le stream est accessible :

```bash
sox -t mp3 http://localhost:8000/turntable.mp3 -n trim 0 2 stat 2>&1
```

La ligne `RMS amplitude` doit afficher une valeur > 0 quand la platine tourne.

### 4. Déployer le script de détection

Copier `vinyle_monitor.py` dans `/home/pi/` et éditer les variables de configuration :

```python
MQTT_HOST = "ipv4_du_broker_mqtt"
MQTT_PORT = 1883
MQTT_USER = "votre_user_mqtt"
MQTT_PASS = "votre_pass_mqtt"
MQTT_TOPIC = "vinyle/status"

SILENCE_THRESHOLD = 0.01     # Seuil RMS pour détecter la lecture
SILENCE_DURATION = 60        # Secondes de silence avant de passer à idle
CHECK_INTERVAL = 5           # Secondes entre chaque mesure
```

### 5. Créer le service systemd

Copier `vinyle-monitor.service` dans `/etc/systemd/system/` en adaptant l'utilisateur :

```bash
sudo cp vinyle-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vinyle-monitor
sudo systemctl start vinyle-monitor
```

Vérifier que le service tourne :

```bash
sudo systemctl status vinyle-monitor
journalctl -u vinyle-monitor -f
```

### 6. Configurer Home Assistant

#### Automation YAML

Importer `automation_vinyle_sonos.yaml` dans Home Assistant via :
**Paramètres → Automations → Créer une automation → Mode YAML**

Adapter les valeurs suivantes dans le fichier :

```yaml
media_content_id: "x-rincon-mp3radio://http://vinyl.local:8000/turntable.mp3"
entity_id: media_player.enceinte_sonos
volume_level: 0.30
```

## Fonctionnement

- Le script mesure le niveau RMS du stream Icecast toutes les 5 secondes
- Si RMS > `SILENCE_THRESHOLD` → publie `playing` sur le topic MQTT
- Si RMS < `SILENCE_THRESHOLD` pendant plus de `SILENCE_DURATION` secondes → publie `idle`
- Home Assistant écoute le topic et bascule le Sonos en conséquence

## Dépannage

**Le service ne démarre pas (status=217/USER)**
→ Vérifier que l'utilisateur dans le fichier `.service` correspond bien à `whoami`

**RMS toujours à 0.0**
→ Vérifier que la ligne Sox contient bien `RMS     amplitude` (avec plusieurs espaces)
→ Le fix est dans le script : `if "RMS" in line and "amplitude" in line`

**paho-mqtt DeprecationWarning**
→ Warning sans impact sur le fonctionnement, lié à la version de paho-mqtt disponible sur Pi OS

## Fichiers

| Fichier | Description |
|---|---|
| `vinyle_monitor.py` | Script de détection audio et publication MQTT |
| `vinyle-monitor.service` | Service systemd pour démarrage automatique |
| `automation_vinyle_sonos.yaml` | Automation Home Assistant |

## Licence

MIT
