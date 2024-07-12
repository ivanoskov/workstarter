import json
import time
import webbrowser
import subprocess

class WorkStarterAgent:
    def __init__(self):
        self.config = self.read_config()
        self.run()

    def read_config(self):
        with open("config.json", "r") as f:
            config: dict = json.load(f)
            return config
        
    def run(self):
        time.sleep(self.config.get("delay"))
        tasks: list[dict] = self.config.get("tasks")
        for task in tasks:
            match task.get("type"):
                case "open_link":
                    self.open_link(task)
                case "open_program":
                    self.open_program(task)

    def open_link(self, task: dict):
        webbrowser.get(using=task.get('browser')).open_new_tab(task.get("url"))

    def open_program(self, task: dict):
        subprocess.Popen([task.get("path")])
        

if __name__ == "__main__":
    WorkStarterAgent()