# workstarter - утилита для автоматического запуска всех нужных программ и сайтов при запуске Вашего пк

Для работы утилиты, соберите её (для сборки рекомендуется использовать <i>pyinstaller</i>) и поместите ярлык в папке автозагрузки

Настройка workstarter производится через config.json - создайте его в папке с исполняемым файлом
Пример структуры config.json:
```json
{
    "delay": 0,
    "tasks": [
      {
        "type": "open_link",
        "url": "https://www.google.com",
        "new_window": false,
        "browser": "windows-default"
      },
  
      {
        "type": "open_program",
        "path": "C:\\Users\\ivann\\AppData\\Local\\Programs\\Notion\\Notion.exe"
      }
    ]
  }
  
```
