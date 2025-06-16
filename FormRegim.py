# QT_DEBUG_PLUGINS=1 python3 /home/adtema/Документы/vuz/5sem/курсач/kurswork_rita/FormRegim.py


import sys
import re
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QHBoxLayout, QWidget, QComboBox, QGridLayout, QLabel, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from newfile import start

def generate_shooting_patterns():
    min_shots = 1
    max_shots = 28
    temp = 5

    min_pause = 10
    max_pause = 20
    pause_step = 5

    patterns = []

    for queue_length in range(min_shots, max_shots + 1):
        for pause_length in range(min_pause, max_pause + 1, pause_step):
            pattern = []
            remaining_shots = max_shots

            while remaining_shots > 0:
                shots_in_queue = min(queue_length, remaining_shots)
                pattern.append({"Тип": "Очередь", "Выстрелов": shots_in_queue, "Темп": temp})
                remaining_shots -= shots_in_queue

                if remaining_shots > 0:
                    pattern.append({"Тип": "Перерыв", "Время": pause_length})
            if pattern not in patterns:
                patterns.append(pattern)

    return patterns

class CalculationThread(QThread):
    progress_updated = pyqtSignal(int)
    calculation_finished = pyqtSignal(list)

    def run(self):
        print('run')
        patterns = generate_shooting_patterns()
        result_times = []

        for i, pattern in enumerate(patterns):
            print(str(i + 1) + '/' + str(len(patterns)))
            result = start(pattern)
            result, data = result
            result_times.append([pattern, result, data])
            self.progress_updated.emit(int((i + 1) / len(patterns) * 100))

        result_times = [item for item in result_times if item[1] != -1]
        result_times = sorted(result_times, key=lambda x: x[1])[:5]
        self.calculation_finished.emit(result_times)

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Генерация и расчёт")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        self.combo_label = QLabel("Выберите вариант:")
        self.combo_box = QComboBox()
        self.combo_box.currentIndexChanged.connect(self.update_graphs_from_selection)

        self.graph_layout = QGridLayout()

        self.figures = []
        self.canvases = []
        for i in range(4):
            fig = plt.figure()
            canvas = FigureCanvas(fig)
            self.figures.append(fig)
            self.canvases.append(canvas)
            self.graph_layout.addWidget(canvas, i // 2, i % 2)

        self.layout.addWidget(self.combo_label)
        self.layout.addWidget(self.combo_box)
        self.layout.addLayout(self.graph_layout)

        self.central_widget.setLayout(self.layout)

        self.result_times = []
        self.start_calculation()

    def start_calculation(self):
        self.update_progress(0)
        self.thread = CalculationThread()
        self.thread.progress_updated.connect(self.update_progress)
        self.thread.calculation_finished.connect(self.on_calculation_finished)
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_calculation_finished(self, result_times):
        self.result_times = result_times
        self.progress_bar.hide()
        self.combo_box.clear()
        self.combo_box.addItems([
            f"Вариант {i+1}: {len([x for x in pattern if x['Тип'] == 'Очередь'])} очередей, "
            f"{len([x for x in pattern if x['Тип'] == 'Перерыв'])} перерывов "
            f"({next((x['Время'] for x in pattern if x['Тип'] == 'Перерыв'), 'без перерывов')})"
            for i, (pattern, _, _) in enumerate(result_times)
        ])
        self.update_graphs(0)

    def update_graphs_from_selection(self):
        index = self.combo_box.currentIndex()
        self.update_graphs(index)

    def update_graphs(self, index):
        if not self.result_times:
            print('exit')
            return

        val1, val2, val3, val4 = [], [], [], []
        for line in self.result_times[index][2].split('\n'):
            if re.match(r'^\d+', line.strip()):
                values = line.split('\t')
                var1, var2, var3, var4, var5 = map(float, values)
                val1.append(var2)
                val2.append(var3)
                val3.append(var4)
                val4.append(var5)
        data = [val1, val2, val3, val4]
        titles = [
            "Внутренняя (нарезы полн. гл)",
            "Наружная (нарезы полн. гл)",
            "Внутренняя (дул. срез)",
            "Наружная (дул. срез)"
        ]
        for i in range(4):
            self.figures[i].clear()
            ax = self.figures[i].add_subplot(111)
            ax.plot(data[i], marker='o')
            ax.set_title(titles[i])
            ax.set_xlabel("Выстрел")
            ax.set_ylabel("Температура")
            ax.grid()
            self.canvases[i].draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
