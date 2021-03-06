from io import StringIO
import contextlib
import sys
import time
# import subprocess
# import webbrowser
from codelab_adapter.core_extension import Extension

# 安全性原则: 打开这个插件前，提醒社区用户确认积木中没有危险的Python代码， 允许社区成员举报危险代码
# 在EIM中运行Python代码，通用


class PythonKernelExtension(Extension):
    def __init__(self):
        super().__init__()
        self.EXTENSION_ID = "eim/python"

    @contextlib.contextmanager
    def stdoutIO(self, stdout=None):
        old = sys.stdout
        if stdout is None:
            stdout = StringIO()
        sys.stdout = stdout
        yield stdout
        sys.stdout = old

    def extension_message_handle(self, topic, payload):
        '''
        所有可能运行代码的地方，都加上验证，确认payload中代码风险和token
        '''
        self.logger.info(f'python: {payload}')
        message_id = payload.get("message_id")
        python_code = payload["content"]
        try:
            with self.stdoutIO() as s:
                # 'hello world'[::-1]
                # import re; print(re.search('just4fun', 'blog.just4fun.site').span())
                # exec(object[, globals[, locals]])
                exec(python_code)  # 注意安全问题, 但应当支持灵活的教学和创造。 赋予用户能力，但提醒他们别让锤子砸伤脚。
            output = s.getvalue()
        except Exception as e:
            output = e
        payload["content"] = str(output)
        message = {"payload": payload} # 无论是否有message_id都返回
        self.publish(message)

    def run(self):
        "服务于UI"
        while self._running:
            time.sleep(0.5)


export = PythonKernelExtension
