# aws_iot_custom_auth_up

Details and steps are being integrated...

## 如何使用aws iot?

1. 创建AWS账户和IAM用户：
    1. 访问AWS管理控制台（[https://aws.amazon.com/](https://aws.amazon.com/)）并创建一个新的AWS账户，如果你还没有账户。(
       需要一张借记卡或者信用卡，这里使用visa卡)
    2. 在AWS管理控制台中，导航到IAM服务，创建一个新的IAM用户，并为该用户分配适当的权限，以便连接到AWS IoT。（目前不做这一步）
2. 登录到控制台界面，选择进入IoT Core
   ![img.png](image/img.png)
3. 点击连接一个设备根据介绍进行
   ![img.png](image/img_0.png)
4. 这里我使用的测试环境是windwos环境
   ![img_1.png](image/img_1.png)
   ![img_2.png](image/img_2.png)
   如果根据平台上说明的执行start.ps1文件会出错，其指定的github连接地址有问题，这里选择直接去github手动下载也可以git到证书目录下
   重命名为：aws-iot-device-sdk-python-v2
   [github 链接地址](https://github.com/aws/aws-iot-device-sdk-python-v2)
5. 在证书目录下安装awsiotsdk库,这里我使用的是conda创建的环境，熟悉conda可自行创建环境
   ![img_3.png](image/img_3.png)

```shell
pip install awsiotsdk
```

安装好之后在证书目录下运行程序：

```shell
python aws-iot-device-sdk-python-v2\samples\pubsub.py --endpoint a35611faxmxpn5-ats.iot.us-east-2.amazonaws.com --ca_file root-CA.crt --cert y1hsiaochunnn_mqtttest.cert.pem --key y1hsiaochunnn_mqtttest.private.key --client_id basicPubSub --topic sdk/test/python --count 0
```

![img_4.png](image/img_4.png)
在平台可以看到正常的输入消息即为成功。
![img_9.png](image/img_9.png)
![img_10.png](image/img_10.png)
![img_11.png](image/img_11.png)
![img_12.png](image/img_12.png)

## 那么如何脱离证书连接aws iot?

在阅读aws开发者文档看到[Custom authentication and authorization](https://docs.aws.amazon.com/iot/latest/developerguide/custom-authentication.html)

这里明确提到可以使用mqtt形式来连接aws iot，其工作原理如图：
![img_5.png](image/img_5.png)

解读这个工作流机制可以得到下述结论：

1. 设备使用通信协议时遵循以下规则：
   ![img_6.png](image/img_6.png)
2. aws iot core收到请求时检查

- 授权者
- 终端认证者
  可以理解为他是**端对端**认证方式，通俗的来说可以参考下图：
  ![img_7.png](image/img_7.png)
  mqtt三大连接方式：
- 裸连
- 服务端认证
- 服务端客户端双重认证
  为了解决某些iot设备不支持证书更新的形式阿里云推出了客户端预注册方式来解决这个问题，那么aws iot的解决方式是提供一个名为lambda的服务

**aws iot lambda?**

根据官方的形容，AWS IoT Lambda功能是AWS IoT服务的一项特性，它允许您将AWS Lambda函数与AWS IoT规则（IoT Rules）结合使用。AWS
Lambda是一种无服务器计算服务，能够在云中运行代码而无需管理服务器。
也就是说他免除了你再开发个后端中继来管理这个mqtt服务，直接在平台上内置一个（可能是为什么那么多用户的关键原因）。

在官方文档中描述到可以免除签名令牌，也就是证书
![img_8.png](image/img_8.png)
到此基本流程了解，开始根据流程开发免证书的username/password形式访问

## 创建aws iot core Authorizers

这一步主要是为了添加一个可用用户当做认证人

![img_13.png](image/img_13.png)
![img_14.png](image/img_14.png)

新建lambda函数
![img_15.png](image/img_15.png)

新建好了之后可以自定义身份验证，这里参考文档说明：

![img_16.png](image/img_16.png)
![img_17.png](image/img_17.png)
后面文档中提供了一个js的lambda函数，简单说明了需要的函数形式，js格式的代码还是非常简单的，给他做一个简单的转换写成python再加点细节就是这样的：

```python

import json
import base64


def lambda_handler(event, context):
    print(json.dumps(event))

    password = event['protocolData']['mqtt']['password']
    print("\n Base64 encoded Password is: " + password)
    password = str(base64.b64decode(password))
    password = password.replace("'", "")
    password = password.replace("b", "", 1)
    print("\n Base64 decoded Password is: " + password)

    if password == "123456789":
        print("Password Athentication: Success")
    else:
        print("Password Athentication: Failre")
        result = {
            "isAuthenticated": False
        }
        return result

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iot:Connect"
                ],
                "Resource": [
                    "arn:aws:iot:us-east-2:*:client/${iot:ClientId}"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iot:Publish",
                    "iot:Receive"
                ],
                "Resource": [
                    "arn:aws:iot:us-east-2:*:topic/${iot:ClientId}/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iot:Subscribe"
                ],
                "Resource": [
                    "arn:aws:iot:us-east-2:*:topicfilter/${iot:ClientId}/*"
                ]
            }
        ]
    }
    result = {
        "isAuthenticated": True,
        "principalId": "EnhancedAuthorizerLambba",
        "policyDocuments": [json.dumps(policy)],
        "disconnectAfterInSeconds": 1800,
        "refreshAfterInSeconds": 300
    }

    print(result)
    return result
```

将收到数据和返回数据做了一个打印操作，方便后面请求观察log。

为了简便这里提供一个python的示例代码来实现连接aws iot，然后上报数据

```python
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

```

这里主要是一个mqtt的连接方式，内容参数写法在开发者文档都能找到
[link](https://docs.aws.amazon.com/zh_cn/iot/latest/developerguide/custom-auth.html)
![img_18.png](image/img_18.png)
**注意一点，开发者文档内推荐使用一个叫aws cli的工具来请求他的服务器，方便快捷。不适合初学者和刚接触aws iot的开发者**

## 查看连接情况
这里查看的应该是[cloud watch](https://us-east-2.console.aws.amazon.com/cloudwatch/home)这个工具

这里展示了全部成功的连接请求和具体参数

![img_19.png](image/img_19.png)

![img_20.png](image/img_20.png)

这里显示了正确的username password方法连接的请求，可以作参考使用