import asyncio
import aiocoap.resource as resource
import aiocoap
import logging
import cv2
import RPi.GPIO as GPIO
import threading
import time
import datetime

global crowdCount

def getCrowdCount():
    global crowdCount
    return crowdCount

def setCrowdCount(count):
    global crowdCount
    crowdCount = count

def alert():
    piezoCount = 0
    piezoPin = 18

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(piezoPin, GPIO.OUT)

    pwm = GPIO.PWM(piezoPin, 500)

    while piezoCount <= 4:
        pwm.start(90)
        time.sleep(2)
        pwm.stop()
        time.sleep(1)
        piezoCount += 1

    pwm.stop()
    GPIO.cleanup()

def objDetect():
    global image

    # Set pretrained TensorFlow Object Detection weights model and config file path
    weightsModel = "/home/magu/magugan/models/frozen_inference_graph_V2.pb"
    configFile = "/home/magu/magugan/models/ssd_mobilenet_v2_coco_2018_03_29.pbtxt"

    # Read TensorFlow DNN(Deep Neural Network)
    cv2DNN = cv2.dnn.readNetFromTensorflow(weightsModel, configFile)

    # Set camera
    camera = cv2.VideoCapture(-1)

    while True:
        # Initialize value
        tempCrowdCnt = 0
        cv2.waitKey(1)
        imgBool, image = camera.read()
        # If read image successful, Keep going
        # Get image height, width, channel (When color image)
        imgHeight, imgWidth, imgChannel = image.shape
        # Make input image to blob object, Function cv2.dnn.blobFromImage() returns 4-dimensional blob object with N,C,H,W demensions
        # Set image size to (500, 500)
        blob = cv2.dnn.blobFromImage(image, size=(250, 250))
        # Input blob object to DNN
        cv2DNN.setInput(blob)
        # Run forward pass
        outputBlob = cv2DNN.forward()
        for detectedInfo in outputBlob[0, 0, :, :]:
            # Detect only Perosn
            if isPerson(detectedInfo[1]) == True:
                # Detect when accuracy is greater than {}
                if detectedInfo[2] > .30:
                    # start point from top-left corner
                    startPoint = (int(detectedInfo[3] * imgWidth), int(detectedInfo[4] * imgHeight))
                    # end point from bottom-right corner
                    endPoint = (int(detectedInfo[5] * imgWidth), int(detectedInfo[6] * imgHeight))
                    # Set box color
                    color = (0, 255, 0)
                    # Make rectangle on detected object
                    cv2.rectangle(image, startPoint, endPoint, color, thickness=3)
                    # Add tempCrowdCnt value
                    tempCrowdCnt += 1
        # Display image on screen
        cv2.imshow('Crowd Detection', image)
        setCrowdCount(tempCrowdCnt)

def isPerson(detectionValue):
    # 1.0 is Person
    # If detect Person, Return true else nothing
    if detectionValue == 1:
        return True
    else:
        return False

class CrowdResource(resource.ObservableResource):
    def __init__(self):
        super().__init__()

        self.handle = None

    def notify(self):
        self.updated_state()
        self.reschedule()

    def reschedule(self):
        self.handle = asyncio.get_event_loop().call_later(5, self.notify)

    def update_observation_count(self, count):
        if count and self.handle is None:
            print("Starting the clock")
            self.reschedule()
        if count == 0 and self.handle:
            print("Stopping the clock")
            self.handle.cancel()
            self.handle = None

    async def render_get(self, request):
        payload = str(getCrowdCount()).encode('utf-8')
        return aiocoap.Message(payload=payload)

class StateResource(resource.Resource):
    def __init__(self):
        super().__init__()
        self.set_content(b'stable')

    def set_content(self, content):
        self.content = content

    async def render_get(self, request):
        return aiocoap.Message(payload=self.content)

    async def render_put(self, request):
        print('PUT payload: %s' % request.payload)
        self.set_content(request.payload)

        if (self.content == b'alert'):
            alert()
            self.set_content(b'stable')
        
        return aiocoap.Message(code=aiocoap.CHANGED, payload=self.content)

class TimeResource(resource.ObservableResource):
    def __init__(self):
        super().__init__()

        self.handle = None

    def notify(self):
        self.updated_state()
        self.reschedule()

    def reschedule(self):
        self.handle = asyncio.get_event_loop().call_later(5, self.notify)

    def update_observation_count(self, count):
        if count and self.handle is None:
            print("Starting the clock")
            self.reschedule()
        if count == 0 and self.handle:
            print("Stopping the clock")
            self.handle.cancel()
            self.handle = None

    async def render_get(self, request):
        payload = datetime.datetime.now().\
                strftime("%Y-%m-%d %H:%M").encode('ascii')
        return aiocoap.Message(payload=payload)

class WhoAmI(resource.Resource):
    async def render_get(self, request):
        text = ["Used protocol: %s." % request.remote.scheme]

        text.append("Request came from %s." % request.remote.hostinfo)
        text.append("The server address used %s." % request.remote.hostinfo_local)

        claims = list(request.remote.authenticated_claims)
        if claims:
            text.append("Authenticated claims of the client: %s." % ", ".join(repr(c) for c in claims))
        else:
            text.append("No claims authenticated.")

        return aiocoap.Message(content_format=0,
                payload="\n".join(text).encode('utf8'))

logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)

async def server():
    root = resource.Site()

    root.add_resource(['.well-known', 'core'],
            resource.WKCResource(root.get_resources_as_linkheader))
    root.add_resource(['crowd'], CrowdResource())
    root.add_resource(['state'], StateResource())
    root.add_resource(['time'], TimeResource())
    root.add_resource(['whoami'], WhoAmI())

    await aiocoap.Context.create_server_context(root)

    await asyncio.get_running_loop().create_future()

def serverOpen():
    asyncio.run(server())

if __name__ == "__main__":
    task1 = threading.Thread(target = serverOpen)
    task2 = threading.Thread(target = objDetect)
    task1.start()
    task2.start()