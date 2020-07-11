import queue
import time

from codelab_adapter_client.utils import threaded
from codelab_adapter.core_extension import Extension

import networkzero as nw0

nw0_message_queue = queue.Queue()


class Nw0Helper:
    def __init__(self, extensionInstance):
        self.extensionInstance = extensionInstance
        self.logger = extensionInstance.logger
        self.addresses = None  # 当前连接的port

    @threaded
    def _wait_for_message(self, name, address):
        while True:  # thread
            message = nw0.wait_for_message_from(address)
            nw0.send_reply_to(address, "ok")
            # todo send to scratch
            print(f"address -> {address}; message -> {message}")  # queue
            nw0_message_queue.put((name, message))

    def advertise(self, content):
        # 如果存在则不能再广播
        address = nw0.advertise(content, fail_if_exists=True)  # 强行 只允许一次
        if address:
            self._wait_for_message(content, address)
            return address
        else:
            # 已经存在
            return "already exists!"

    def discover(self, content):
        address = nw0.discover(content, wait_for_s=1)
        return address

    def discover_all(self):
        addresses = nw0.discover_all()
        return addresses

    def update_addresses(self):
        addresses = nw0.discover_all()
        message = self.extensionInstance.message_template()
        message["payload"]["content"] = {
            "addresses": addresses, # [['a','xxx'],]
        }
        self.extensionInstance.publish(message)
        return "ok"

    def send_message_to(self, address, content):
        reply = nw0.send_message_to(address, content)
        return reply


class NW0Extension(Extension):

    NODE_ID = "eim/extension_NetworkZero"
    HELP_URL = "http://adapter.codelab.club/extension_guide/NetworkZero/"
    VERSION = "1.0"  # extension version
    DESCRIPTION = "NetworkZero"
    WEIGHT = 94.1
    REQUIRES_ADAPTER = ">= 3.4.0"

    def __init__(self):
        super().__init__()
        self.nw0Helper = Nw0Helper(self)

    def run_python_code(self, code):
        # fork from python extension
        try:
            output = eval(code, {"__builtins__": None}, {
                "nw0Helper": self.nw0Helper,
            })
        except Exception as e:
            output = str(e)
        return output

    def extension_message_handle(self, topic, payload):
        self.logger.info(f'python code: {payload["content"]}')
        message_id = payload.get("message_id")
        python_code = payload["content"]
        output = self.run_python_code(python_code)
        payload["content"] = output
        message = {"payload": payload}  # 无论是否有message_id都返回
        self.publish(message)

    def run(self):
        "避免插件结束退出"
        while self._running:
            time.sleep(0.05)
            if not nw0_message_queue.empty():
                
                (name, nw0_message) = nw0_message_queue.get()
                self.logger.debug(f'(name, nw0_message)(to scrtch) -> {(name, nw0_message)}')
                message = self.message_template()
                # pub to scratch
                message["payload"]["content"] = {
                    "name": name,
                    "message": nw0_message
                }
                self.publish(message)


export = NW0Extension