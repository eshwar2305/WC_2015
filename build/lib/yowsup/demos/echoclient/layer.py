from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities  import ImageDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_media.protocolentities  import LocationMediaMessageProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
from yowsup.layers.protocol_media.protocolentities  import VCardMediaMessageProtocolEntity
from yowsup.layers.protocol_iq.protocolentities          import *
from yowsup.common import YowConstants
from yowsup.layers.network import YowNetworkLayer
import os,datetime
import time
import logging
from threading import Thread, Lock

class EchoLayer(YowInterfaceLayer):
    
    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):

        #if not messageProtocolEntity.isGroupMessage():
        if messageProtocolEntity.getType() == 'text':
            self.onTextMessage(messageProtocolEntity)
    
    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", "delivery")
        self.toLower(ack)

    def onTextMessage(self,messageProtocolEntity):
        receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom())
            
        outgoingMessageProtocolEntity = TextMessageProtocolEntity(
            messageProtocolEntity.getBody(),
            to = messageProtocolEntity.getFrom())

        formattedDate = datetime.datetime.fromtimestamp(messageProtocolEntity.getTimestamp()).strftime('%d-%m-%Y %H:%M')
        script_dir = os.getcwd()
        rel_path = "out.txt"
        abs_file_path = os.path.join(script_dir,rel_path)
        f = open(abs_file_path,'a')
        msgData = messageProtocolEntity.getBody().replace("\n","")
        f.write("%s [%s]:%s \n" % (messageProtocolEntity.getFrom(False),formattedDate, msgData))
        f.close()
        print("%s [%s]:%s" % (messageProtocolEntity.getFrom(False),formattedDate,msgData))
        
        #send receipt otherwise we keep receiving the same message over and over
        self.toLower(receipt)
        #self.toLower(outgoingMessageProtocolEntity)

    def onEvent(self, event):
        name = event.getName()
        if name == YowNetworkLayer.EVENT_STATE_CONNECTED:
            if not self._pingThread:
                self._pingQueue = {}
                self._pingThread = YowPingThread(self)
                self.__logger.debug("starting ping thread.")
                self._pingThread.start()
        elif name == YowNetworkLayer.EVENT_STATE_DISCONNECT or name == YowNetworkLayer.EVENT_STATE_DISCONNECTED:
            if self._pingThread:
                self.__logger.debug("stopping ping thread")
                if self._pingThread:
                    self._pingThread.stop()
                    self._pingThread = None
                self._pingQueue = {}

class YowPingThread(Thread):
    def __init__(self, layer):
        assert type(layer) is EchoLayer, "layer must be a YowIqProtocolLayer, got %s instead." % type(layer)
        self._layer = layer
        self._stop = False
        self.__logger = logging.getLogger(__name__)
        super(YowPingThread, self).__init__()
        self.name = "YowPing%s" % self.name

    def run(self):
        while not self._stop:
            for i in range(1, 24):
                time.sleep(5)
                if self._stop:
                    self.__logger.debug("%s - ping thread stopped" % self.name)
                    return
            ping = PingIqProtocolEntity()
            self._layer.waitPong(ping.getId())
            if not self._stop:
                self._layer.sendIq(ping)

    def stop(self):
        self._stop = True
            
