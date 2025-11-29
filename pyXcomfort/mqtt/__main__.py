#!/usr/bin/env python3
import logging
import json
import os
import sys
import traceback
import signal

# Set up logging FIRST before any imports that might fail
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# Log startup
logger.info("=" * 60)
logger.info("Xcomfort MQTT Bridge Starting")
logger.info("=" * 60)

try:
    # Import dependencies
    logger.info("Importing xcomfort library...")
    from xcomfort.xcomfort import Xcomfort
    logger.info("Importing paho.mqtt...")
    import paho.mqtt.client as mqtt
    logger.info("All imports successful")
except ImportError as e:
    logger.error(f"Failed to import required library: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)


def load_config():
    """Load configuration from options.json and environment variables"""
    logger.info("Loading configuration...")
    config = {}

    # Load add-on options
    try:
        logger.info("Reading /data/options.json...")
        with open('/data/options.json') as f:
            config = json.load(f)
        logger.info(f"Loaded options.json with {len(config)} keys")
    except FileNotFoundError:
        logger.warning('options.json not found, using defaults')
        config = {
            'device': '/dev/ttyUSB0',
            'mqtt': {
                'username': '',
                'password': '',
                'host': '',
                'port': 1883,
                'rootTopic': 'homeassistant/'
            },
            'devices': [],
            'log_level': 'info'
        }
    except Exception as e:
        logger.error(f'Failed to load options.json: {e}')
        logger.error(traceback.format_exc())
        sys.exit(1)

    # Override with environment variables if set (from run script)
    logger.info("Checking for environment variable overrides...")

    if os.getenv('MQTT_HOST'):
        config['mqtt']['host'] = os.getenv('MQTT_HOST')
        logger.info(f"Using MQTT host from environment: {config['mqtt']['host']}")

    if os.getenv('MQTT_PORT'):
        config['mqtt']['port'] = int(os.getenv('MQTT_PORT'))
        logger.info(f"Using MQTT port from environment: {config['mqtt']['port']}")

    if os.getenv('MQTT_USERNAME'):
        config['mqtt']['username'] = os.getenv('MQTT_USERNAME')
        logger.info(f"Using MQTT username from environment: {config['mqtt']['username']}")

    if os.getenv('MQTT_PASSWORD'):
        config['mqtt']['password'] = os.getenv('MQTT_PASSWORD')
        logger.info("Using MQTT password from environment (hidden)")

    # Set log level from config
    log_level = config.get('log_level', 'info').upper()
    logger.info(f"Setting log level to: {log_level}")
    logging.getLogger().setLevel(getattr(logging, log_level, logging.INFO))

    return config


# Global variables
config = None
xcomfort = None
client = None
known_devices = []
root_topic = None
base_topic = 'xcomfort/'


def getTopic(device, device_type='light'):
    """Generate MQTT topic for device"""
    return '{}{}/{}{}/'.format(
        root_topic,
        device_type,
        base_topic if device_type != 'device_automation' else '',
        str(device.serial))


def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    try:
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            subscribe_topic = root_topic + 'light/' + base_topic + '+/set'
            client.subscribe(subscribe_topic)
            logger.info(f"Subscribed to: {subscribe_topic}")

            # Set up xcomfort devices
            xcomfort.lights = config['devices']
            xcomfort.onSwitch(button_pressed)

            # Register all configured devices
            for light in xcomfort.lights:
                try:
                    register_device(light)
                    light.onChange(update_state)
                except Exception as e:
                    logger.error(f"Failed to register device {light.serial}: {e}")

            logger.info(f"Registered {len(xcomfort.lights)} devices")
        else:
            error_messages = {
                1: "incorrect protocol version",
                2: "invalid client identifier",
                3: "server unavailable",
                4: "bad username or password",
                5: "not authorized"
            }
            error_msg = error_messages.get(rc, f"unknown error code {rc}")
            logger.error(f"Failed to connect to MQTT broker: {error_msg}")
    except Exception as e:
        logger.error(f"Error in on_connect: {e}")
        logger.error(traceback.format_exc())


def on_disconnect(client, userdata, rc):
    """MQTT disconnection callback"""
    try:
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnect. Return code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    except Exception as e:
        logger.error(f"Error in on_disconnect: {e}")


def on_message(client, userdata, msg):
    """MQTT message callback"""
    try:
        logger.debug(f"Received message on topic: {msg.topic}")
        topics = msg.topic.split('/')

        if len(topics) < 4:
            logger.warning(f"Invalid topic format: {msg.topic}")
            return

        serial = int(topics[3])
        payload = json.loads(msg.payload)
        logger.debug(f"Message for device {serial}: {payload}")

        # Find and update device
        for light in xcomfort.lights:
            if light.serial == serial:
                if 'brightness' in payload:
                    light.brightness = int(payload['brightness'])
                    logger.info(f"Set brightness for {serial} to {light.brightness}")
                else:
                    light.state = True if payload['state'] == 'ON' else False
                    light._brightness = 100 if payload['state'] == 'ON' else 0
                    logger.info(f"Set state for {serial} to {light.state}")
                break
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse MQTT message payload: {e}")
    except ValueError as e:
        logger.error(f"Invalid serial number in topic: {e}")
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")
        logger.error(traceback.format_exc())


def update_state(device):
    """Publish device state to MQTT"""
    try:
        topic = getTopic(device, device_type='light')
        deviceConfig = {
            'state': 'ON' if device.state else 'OFF',
            'brightness': device.brightness
        }
        client.publish(topic + 'state', payload=json.dumps(deviceConfig))
        logger.debug(f"Published state for device {device.serial}")
    except Exception as e:
        logger.error(f"Error updating state for device {device.serial}: {e}")


def button_pressed(switch):
    """Handle button press event"""
    try:
        serial = str(switch.serial)
        logger.info(f"Button {serial} pressed")

        if serial not in known_devices:
            logger.info(f"New button discovered: {serial}")
            known_devices.append(serial)
            register_device_trigger(switch)

        trigger_device_automation(switch)
    except Exception as e:
        logger.error(f"Error handling button press: {e}")
        logger.error(traceback.format_exc())


def trigger_device_automation(device):
    """Trigger device automation in Home Assistant"""
    try:
        topic = getTopic(device, device_type='device_automation')
        state = 'turn_on' if device.state else 'turn_off'
        client.publish(topic + state + '/state', payload=state)
        logger.debug(f"Triggered automation: {state} for device {device.serial}")
    except Exception as e:
        logger.error(f"Error triggering automation: {e}")


def register_device_trigger(device):
    """Register device trigger for Home Assistant MQTT discovery"""
    try:
        serial = str(device.serial)
        topic = getTopic(device, device_type='device_automation')
        topic_turn_off = topic + 'turn_off/'
        topic_turn_on = topic + 'turn_on/'

        # Register turn_on trigger
        deviceConfig = {
            'automation_type': 'trigger',
            'topic': topic_turn_on + 'state',
            'type': 'button_short_press',
            'subtype': 'turn_on',
            'unique_id': 'switch-' + serial,
            'device': {
                'identifiers': [serial],
                'manufacturer': 'Eaton',
                'model': 'Xcomfort',
                'name': 'Button-' + serial,
                'sw_version': 'pyXcomfort v1.0'
            }
        }
        client.publish(topic_turn_on + 'config', payload=json.dumps(deviceConfig), retain=True)

        # Register turn_off trigger
        deviceConfig['subtype'] = 'turn_off'
        deviceConfig['topic'] = topic_turn_off + 'state'
        client.publish(topic_turn_off + 'config', payload=json.dumps(deviceConfig), retain=True)

        logger.info(f"Registered device trigger for button {serial}")
    except Exception as e:
        logger.error(f"Error registering device trigger: {e}")
        logger.error(traceback.format_exc())


def register_device(device):
    """Register device for Home Assistant MQTT discovery"""
    try:
        topic = getTopic(device, device_type='light')
        logger.info(f"Registering device {device.serial} ({device.name}) to topic: {topic}")

        deviceConfig = {
            'schema': 'json',
            'brightness': True,
            'command_topic': topic + 'set',
            'state_topic': topic + 'state',
            'name': device.name,
            'unique_id': 'light-' + str(device.serial),
            'device': {
                'identifiers': [str(device.serial)],
                'manufacturer': 'Eaton',
                'model': 'Xcomfort',
                'name': device.name,
                'sw_version': 'pyXcomfort v1.0'
            }
        }

        client.publish(topic + 'config', payload=json.dumps(deviceConfig), retain=True)
        logger.info(f"Device {device.serial} registered successfully")
    except Exception as e:
        logger.error(f"Error registering device {device.serial}: {e}")
        logger.error(traceback.format_exc())


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if client:
        client.disconnect()
    sys.exit(0)


def main():
    """Main application entry point"""
    global config, xcomfort, client, root_topic

    try:
        # Load configuration
        config = load_config()

        # Validate configuration
        logger.info("Validating configuration...")

        if not config.get('device'):
            logger.error('No serial device configured!')
            sys.exit(1)

        if not config['mqtt'].get('host'):
            logger.error('No MQTT broker configured!')
            sys.exit(1)

        root_topic = config['mqtt'].get('rootTopic', 'homeassistant/')

        logger.info(f"Device: {config['device']}")
        logger.info(f"MQTT broker: {config['mqtt']['host']}:{config['mqtt']['port']}")
        logger.info(f"MQTT user: {config['mqtt'].get('username') or '(none)'}")
        logger.info(f"Root topic: {root_topic}")
        logger.info(f"Configured devices: {len(config.get('devices', []))}")

        # Initialize Xcomfort
        logger.info("Initializing Xcomfort...")
        try:
            xcomfort = Xcomfort(devicePath=config['device'])
            logger.info("Xcomfort initialized successfully")
        except Exception as e:
            logger.error(f'Failed to initialize Xcomfort: {e}')
            logger.error(traceback.format_exc())
            sys.exit(1)

        # Setup MQTT client
        logger.info("Setting up MQTT client...")
        broker = config['mqtt']['host']
        port = config['mqtt']['port']

        client = mqtt.Client('ha-xcomfort')
        client.enable_logger(logger)

        # Set callbacks
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message

        # Set username/password if provided
        if config['mqtt'].get('username'):
            logger.info("Using MQTT authentication")
            client.username_pw_set(
                username=config['mqtt']['username'],
                password=config['mqtt']['password']
            )
        else:
            logger.info("No MQTT authentication configured")

        # Setup signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Connect to MQTT broker
        logger.info(f"Connecting to MQTT broker {broker}:{port}...")
        client.connect(broker, port=port, keepalive=60)

        # Start MQTT loop
        logger.info("Starting MQTT loop...")
        client.loop_forever()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        if client:
            client.disconnect()
    except Exception as e:
        logger.error(f"FATAL ERROR in main: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        logger.info("Xcomfort MQTT Bridge stopped")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"UNCAUGHT EXCEPTION: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
