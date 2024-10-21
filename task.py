import asyncio
import webbrowser
import subprocess
from enum import Enum
import time

class TaskState(Enum):
    WAIT = "wait"
    START = "start"
    DONE = "done"
    ERROR = "error"

class Task:
    def __init__(self, config):
        self.config = config

    async def run(self):
        raise NotImplementedError

class TaskOpenLink(Task):
    async def run(self):
        webbrowser.open(self.config['url'])
        await asyncio.sleep(self.config.get('delay', 0))

class TaskOpenProgram(Task):
    async def run(self):
        subprocess.Popen(self.config['path'], shell=True)
        await asyncio.sleep(self.config.get('delay', 0))
