from __future__ import print_function
import sys
import ssl
import time
import datetime
import logging, traceback
import paho.mqtt.client as mqtt

### Set endpoint, Url, Username, password, clientid, CA File, topic, and port
username = "y1hsiaochunnn?x-amz-customauthorizer-name=AutoCustom"
password = "123456789"
clientId = "basicPubSub"
topic = "test/topic"
aws_iot_endpoint = "a35611faxmxpn5-ats.iot.us-east-2.amazonaws.com"
port = 443

## Set up Logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(log_format)
logger.addHandler(handler)

## Establish Connection and Publish messages
if __name__ == '__main__':
    try:
        mqttc = mqtt.Client(clientId)
        mqttc.username_pw_set(username=username, password=password)
        ssl_context = ssl.create_default_context()
        ssl_context.set_alpn_protocols(['mqtt'])
        mqttc.tls_set_context(context=ssl_context)
        logger.info("start connect")
        mqttc.connect(aws_iot_endpoint, port=port)
        logger.info("connect success")
        mqttc.loop_start()

        while True:
            now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            logger.info("try to publish: {}".format(now))
            mqttc.publish(topic, now, qos=1)
            time.sleep(2)

    except Exception as e:
        logger.error("exception main()")
        logger.error("e obj: {}".format(vars(e)))
        logger.error("message: {}".format(str(e)))
        traceback.print_exc(file=sys.stdout)
