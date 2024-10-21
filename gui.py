from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, 
                             QListWidget, QDialog, QLineEdit, QFormLayout, QComboBox, 
                             QMessageBox, QListWidgetItem, QHBoxLayout, QFileDialog)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
import sys
import json
import os
from urllib.parse import urlparse
from functools import partial
import logging
import appdirs
import tempfile

# В начале файла, после импортов
APP_NAME = "WorkStarter"
APP_AUTHOR = "ivanoskov"
config_dir = appdirs.user_config_dir(APP_NAME, APP_AUTHOR)
log_dir = tempfile.gettempdir()

# Создаем директории, если они не существуют
os.makedirs(config_dir, exist_ok=True)

config_path = os.path.join(config_dir, "config.json")
log_path = os.path.join(log_dir, f"{APP_NAME}.log")

# Настройка логирования
try:
    logging.basicConfig(filename=log_path, level=logging.DEBUG, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        encoding='utf-8')
except PermissionError:
    # Если не удалось создать файл лога, используем вывод в консоль
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.warning(f"Не удалось создать файл лога в {log_path}. Логи будут выводиться в консоль.")

logger = logging.getLogger(__name__)

class TaskDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, task: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        logger.info("Инициализация TaskDialog")
        self.setWindowTitle("Добавить/Редактировать задачу")
        self.layout = QFormLayout(self)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["open_link", "open_program"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        self.layout.addRow("Тип:", self.type_combo)
        
        self.value_input = QLineEdit()
        self.layout.addRow("Значение:", self.value_input)
        
        self.browse_button = QPushButton("Обзор")
        self.browse_button.clicked.connect(self.browse_file)
        self.browse_button.hide()
        self.layout.addRow(self.browse_button)
        
        self.delay_input = QLineEdit()
        self.layout.addRow("Задержка:", self.delay_input)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addRow(self.ok_button)

        if task:
            self.populate_fields(task)
            self.type_combo.setEnabled(False)
        else:
            self.on_type_changed(self.type_combo.currentText())

    def on_type_changed(self, task_type: str) -> None:
        logger.debug(f"Тип задачи изменен на: {task_type}")
        if task_type == "open_link":
            self.layout.labelForField(self.value_input).setText("URL:")
            self.browse_button.hide()
            self.value_input.setReadOnly(False)
        else:
            self.layout.labelForField(self.value_input).setText("Путь:")
            self.browse_button.show()
            self.value_input.setReadOnly(True)

    def browse_file(self) -> None:
        logger.debug("Открытие диалога выбора файла")
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите программу", "", "Executable Files (*.exe)")
        if file_path:
            self.value_input.setText(file_path)
            logger.debug(f"Выбран файл: {file_path}")

    def populate_fields(self, task: Dict[str, Any]) -> None:
        logger.debug(f"Заполнение полей данными задачи: {task}")
        self.type_combo.setCurrentText(task['type'])
        if task['type'] == "open_link":
            self.value_input.setText(task.get('url', ''))
        else:
            self.value_input.setText(task.get('path', ''))
        self.delay_input.setText(str(task.get('delay', '')))
        self.on_type_changed(task['type'])

    def get_task_data(self) -> Dict[str, Any]:
        logger.debug("Получение данных задачи из диалога")
        task_type = self.type_combo.currentText()
        
        try:
            delay = int(self.delay_input.text()) if self.delay_input.text() else 0
        except ValueError:
            logger.error("Неверное значение задержки")
            QMessageBox.critical(self, "Ошибка", "Задержка должна быть целым числом.")
            raise ValueError("Неверное значение задержки")

        task = {
            "type": task_type,
            "delay": delay
        }
        if task_type == "open_link":
            task["url"] = self.value_input.text()
        else:
            task["path"] = self.value_input.text()
        logger.debug(f"Данные задачи: {task}")
        return task

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Инициализация MainWindow")
        self.setWindowTitle("WorkStarter")
        self.setGeometry(100, 100, 400, 300)
        self.setWindowIcon(QIcon("icon.ico"))
        
        layout = QVBoxLayout()
        
        self.task_list = QListWidget()
        layout.addWidget(self.task_list)
        
        add_button = QPushButton("Добавить задачу")
        add_button.clicked.connect(self.add_task)
        layout.addWidget(add_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        self.load_config()

    def load_config(self) -> None:
        logger.info("Загрузка конфигурации")
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                for task in config.get("tasks", []):
                    self.add_task_to_list(task)
        except FileNotFoundError:
            logger.warning("Файл конфигурации не найден")
        except json.JSONDecodeError:
            logger.error("Ошибка при разборе JSON в файле конфигурации")

    def add_task_to_list(self, task: Dict[str, Any], index: Optional[int] = None) -> None:
        logger.debug(f"Добавление задачи в список: {task}")
        item_layout = QHBoxLayout()
        task_text = self.get_task_display_name(task)
        task_label = QPushButton(task_text)
        task_label.setStyleSheet("text-align: left; background-color: transparent; border: none;")
        task_label.setEnabled(False)
        task_label.setProperty("task_data", task)
        
        edit_button = QPushButton("Редактировать")
        edit_button.clicked.connect(partial(self.edit_task, task))
        
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(partial(self.delete_task, task))
        
        item_layout.addWidget(task_label)
        item_layout.addWidget(edit_button)
        item_layout.addWidget(delete_button)

        item_widget = QWidget()
        item_widget.setLayout(item_layout)
        
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        
        if index is not None:
            self.task_list.insertItem(index, list_item)
        else:
            self.task_list.addItem(list_item)
        self.task_list.setItemWidget(list_item, item_widget)

    def get_task_display_name(self, task: Dict[str, Any]) -> str:
        if task['type'] == "open_link":
            parsed_url = urlparse(task['url'])
            return f"Открыть сайт: {parsed_url.netloc}"
        else:
            return f"Запустить программу: {os.path.basename(task['path'])}"

    def add_task(self) -> None:
        logger.info("Открытие диалога для добавления новой задачи")
        dialog = TaskDialog(self)
        if dialog.exec():
            try:
                task = self.save_task(dialog)
                self.add_task_to_list(task)
                self.save_config()
                logger.info("Новая задача добавлена успешно")
            except ValueError:
                logger.error("Ошибка при добавлении новой задачи")

    def edit_task(self, task: Dict[str, Any]) -> None:
        logger.info(f"Открытие диалога для редактирования задачи: {task}")
        index = self.find_task_index(task)
        if index is not None:
            dialog = TaskDialog(self, task)
            if dialog.exec():
                try:
                    updated_task = self.save_task(dialog, task)
                    self.update_task_in_list(updated_task, index)
                    self.save_config()
                    logger.info("Задача успешно отредактирована")
                except ValueError:
                    logger.error("Ошибка при редактировании задачи")

    def find_task_index(self, task: Dict[str, Any]) -> Optional[int]:
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            widget = self.task_list.itemWidget(item)
            if widget:
                task_data = widget.layout().itemAt(0).widget().property("task_data")
                if task_data == task:
                    return i
        return None

    def delete_task(self, task: Dict[str, Any]) -> None:
        logger.info(f"Попытка удаления задачи: {task}")
        reply = QMessageBox.question(self, 'Удалить задачу', 'Вы уверены, что хотите удалить эту задачу?', 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            index = self.find_task_index(task)
            if index is not None:
                self.task_list.takeItem(index)
                self.save_config()
                logger.info("Задача успешно удалена")

    def save_task(self, dialog: TaskDialog, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logger.debug("Сохранение задачи из диалога")
        new_task = dialog.get_task_data()
        
        if task:
            task.update(new_task)
        else:
            task = new_task
        
        return task

    def update_task_in_list(self, task: Dict[str, Any], index: int) -> None:
        logger.debug(f"Обновление задачи в списке: {task}")
        self.task_list.takeItem(index)
        self.add_task_to_list(task, index)

    def save_config(self) -> None:
        logger.info("Сохранение конфигурации")
        tasks = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            widget = self.task_list.itemWidget(item)
            if widget:
                task_data = widget.layout().itemAt(0).widget().property("task_data")
                if task_data:
                    tasks.append(task_data)
        
        config = {"tasks": tasks}
        try:
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            logger.info("Конфигурация успешно сохранена")
        except IOError:
            logger.error("Ошибка при сохранении конфигурации")

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}", exc_info=True)
        # Добавим вывод ошибки в консоль для отладки
        print(f"Критическая ошибка: {str(e)}", file=sys.stderr)
