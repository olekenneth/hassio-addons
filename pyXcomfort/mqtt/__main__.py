import logging
import re
import json
from xcomfort.xcomfort import Xcomfort
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    config = json.loads(open('/data/options.json').read())
except:
    logging.info('No config. Using default - don\'t expect anything to work')
    config = {
        'mqtt': {
            'username': '',
            'password': '',
            'host': '',
            'port': 1883,
            'rootTopic': 'homeassistant/'
        },
        'devices': []
    }

rootTopic = config['mqtt']['rootTopic']
baseTopic = 'light/xcomfort/'
xcomfort = Xcomfort(devicePath=config['device'])

def getTopic(device):
    return '{}{}{}/'.format(
        rootTopic,
        baseTopic,
        str(device.serial))

def on_connect(client, userdata, res, code):
    if code is 0:
        logging.info("connected OK")
        client.subscribe(rootTopic + baseTopic + '+/set')
        xcomfort.lights = config['devices']

        for light in xcomfort.lights:
            register_device(light)
            light.onChange(update_state)
    else:
        logging.warning("Not connected result code " + str(res) +
                        str(userdata) + str(code))

def on_message(client, userdata, msg):
    topics = msg.topic.split('/')
    serial = int(topics[3])

    payload = json.loads(msg.payload)
    for light in xcomfort.lights:
        if light.serial == serial:
            if 'brightness' in payload:
                light.brightness = int(payload['brightness'])
            else:
                light.state = True if payload['state'] == 'ON' else False
                light._brightness = 100 if payload['state'] == 'ON' else 0
            break

def update_state(device):
    topic = getTopic(device)
    deviceConfig = {
        'state': 'ON' if device.state else 'OFF',
        'brightness': device.brightness
    }
    client.publish(topic + 'state', payload=json.dumps(deviceConfig))


def register_device(device):
    topic = getTopic(device)
    deviceConfig = {
        'schema': 'json',
        'brightness': device.isDimable,
        'command_topic': topic + 'set',
        'state_topic': topic + 'state',
        'name': device.name,
        'unique_id': 'light-' + str(device.serial),
        'device': {
            'identifiers': str(device.serial),
            'manufacturer': 'Eaton',
            'model': 'Xcomfort',
            'name': device.name,
            'sw_version': 'pyXcomfort v1.0'
        }
    }
    
    # client.publish(topic + 'config', payload="") Delete entity
    client.publish(topic + 'config', payload=json.JSONEncoder().encode(deviceConfig))


broker = config['mqtt']['host']
client = mqtt.Client('ha-xcomfort')
client.enable_logger(logger)
client.username_pw_set(username=config['mqtt']['username'],
                       password=config['mqtt']['password'])

client.on_connect = on_connect
client.on_message = on_message

logging.info('Start')
logging.info('Connecting to broker %s', broker)

client.connect(broker)

client.loop_forever()
logging.info('Finished')
