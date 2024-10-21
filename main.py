import json
from task import Task, TaskOpenLink, TaskOpenProgram
import asyncio
import time
import os
import appdirs

APP_NAME = "WorkStarter"
APP_AUTHOR = "ivanoskov"

class WorkStarterAgent:
    def __init__(self):
        self.tasks: list[Task] = []
        self.config = self.read_config()
        self.parse_tasks()
        self.start_time = time.time()

    def read_config(self):
        config_dir = appdirs.user_config_dir(APP_NAME, APP_AUTHOR)
        config_path = os.path.join(config_dir, "config.json")
        try:
            with open(config_path, "r") as f:
                config: dict = json.load(f)
                return config
        except FileNotFoundError:
            print(f"Конфигурационный файл не найден: {config_path}")
            return {"tasks": []}
        except json.JSONDecodeError:
            print(f"Ошибка при чтении конфигурационного файла: {config_path}")
            return {"tasks": []}
    
    def parse_tasks(self):
        json_tasks: list[dict] = self.config.get("tasks", [])
        for json_task in json_tasks:
            self.tasks.append(self.parse_task(json_task))

    def parse_task(self, json_task):
        match json_task.get("type"):
            case "open_link":
                return TaskOpenLink(json_task)
            case "open_program":
                return TaskOpenProgram(json_task)
            case _:
                raise ValueError("Неизвестный тип задачи")

    async def run(self):
        tasks = [asyncio.create_task(self.run_task(task)) for task in self.tasks]
        await asyncio.gather(*tasks)

    async def run_task(self, task):
        delay = task.config.get("delay", 0)
        elapsed = time.time() - self.start_time
        if delay > elapsed:
            await asyncio.sleep(delay - elapsed)
        await task.run()


async def main():
    agent = WorkStarterAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
