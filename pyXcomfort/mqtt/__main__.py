import logging
import re
import json
from xcomfort.xcomfort import Xcomfort
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    config = json.loads(open('/data/options.json').read())
except:
    logging.info('No config. Using default - don\'t expect anything to work')
    config = {
        'device': '',
        'mqtt': {
            'username': '',
            'password': '',
            'host': '',
            'port': 1883,
            'rootTopic': 'homeassistant/'
        },
        'devices': []
    }

known_devices = []
root_topic = config['mqtt']['rootTopic']
base_topic = 'xcomfort/'
logging.info('Starting pyXcomfort with {}'.format(config['device']))
xcomfort = Xcomfort(devicePath=config['device'])

def getTopic(device, device_type = 'light'):
    return '{}{}/{}{}/'.format(
        root_topic,
        device_type,
        base_topic if device_type != 'device_automation' else '',
        str(device.serial))

def on_connect(client, userdata, res, code):
    if code == 0:
        logging.info("connected OK")
        client.subscribe(root_topic + 'light/' + base_topic + '+/set')
        xcomfort.lights = config['devices']
        xcomfort.onSwitch(button_pressed)

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
    topic = getTopic(device, device_type='light')
    deviceConfig = {
        'state': 'ON' if device.state else 'OFF',
        'brightness': device.brightness
    }
    client.publish(topic + 'state', payload=json.dumps(deviceConfig))

def button_pressed(switch):
    serial = str(switch.serial)
    logging.info("Button {} is pressed".format(serial))
    if serial in known_devices:
        logging.info("Button in known_devices")
    else:
        logging.info("Button IS NOT IN KNOWN_DEVICES")
        known_devices.append(serial)
        register_device_trigger(switch)
    trigger_device_automation(switch)

def trigger_device_automation(device):
    '''
    Switch button is pressed
    '''
    topic = getTopic(device, device_type = 'device_automation')
    state = 'turn_on' if device.state else 'turn_off'

    client.publish(topic + state + '/state', payload=state)

def register_device_trigger(device):
    '''
    Register all switches that can be pressed
    {
      "automation_type": "trigger",
      "type":            "action",
      "subtype":         "arrow_right_click",
      "payload":         "arrow_right_click",
      "topic":           "zigbee2mqtt/0x90fd9ffffedf1266/action",
      "device":
        {
          "identifiers": ["zigbee2mqtt_0x90fd9ffffedf1266"]
        }
    }
    '''
    serial = str(device.serial)
    topic = getTopic(device, device_type='device_automation')
    topic_turn_off = topic + 'turn_off/'
    topic_turn_on = topic + 'turn_on/'
    deviceConfig = {
        'automation_type': 'trigger',
        'topic': topic_turn_on + 'state',
        'type':'button_short_press',
        'subtype': 'turn_on',
        'unique_id': 'switch-' + serial,
        'device': {
            'identifiers': serial,
            'manufacturer': 'Eaton',
            'model': 'Xcomfort',
            'name': 'Button-' + serial,
            'sw_version': 'pyXcomfort v1.0'
        }
    }
    client.publish(topic_turn_on + 'config', payload=json.dumps(deviceConfig))
    deviceConfig['subtype'] = 'turn_off'
    deviceConfig['topic'] = topic_turn_off + 'state'
    client.publish(topic_turn_off + 'config', payload=json.dumps(deviceConfig))

def register_device(device):
    topic = getTopic(device, device_type='light')
    logger.info('register device ({}) to topic: {}'.format(str(device.serial), topic))
    deviceConfig = {
        'schema': 'json',
        'brightness': True,
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

    #client.publish(topic + 'config', payload="") #Delete entity
    client.publish(topic + 'config', payload=json.dumps(deviceConfig))


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
