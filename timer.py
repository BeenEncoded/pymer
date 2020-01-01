import sys, threading, os, time, math, logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt

from quithread import ThreadData, WindowUpdateThread

logger = None

class TimerThreadData(ThreadData):
    def __init__(self, time_passed: float=0.0):
        super(TimerThreadData, self).__init__()
        self.time_passed = time_passed
    
    def setlocals(self):
        if not hasattr(self, "local"):
            self.local = threading.local()
        if self.local is None:
            self.local = threading.local()
        self.local.start = time.time()
        self.local.end = time.time()
        self.local.current = time.time()
        if self.time_passed > 0:
            self.local.start -= self.time_passed
    
    def run_action(self):
        self.local.current = time.time()
        if self.local.current != self.local.end:
            self.local.end = self.local.current
            self.time_passed = (self.local.end - self.local.start)
            self.should_update = True

class TimerWidget(QWidget):
    def __init__(self, parent):
        super(TimerWidget, self).__init__(parent)
        self._init_layout()
        self._init_threads()
        self._connect_handlers()
        self.parent().setWindowTitle("Timer")
        
        self.currenttime = 0.0
    
    def _init_layout(self) -> None:
        mainlayout = QVBoxLayout()

        #The label:
        self.time_left_label = QLabel(self._time_display(0.0))
        self.time_left_label.setFont(QFont("Consolas", 14))
        self.time_left_label.setAlignment(Qt.AlignCenter)

        #the buttons:
        self.startbutton = QPushButton("Start")
        b1layout = QHBoxLayout()
        b1layout.addWidget(self.startbutton)

        self.stopbutton = QPushButton("Stop")
        self.resetbutton = QPushButton("Reset")
        b2layout = QHBoxLayout()
        b2layout.addWidget(self.stopbutton)
        b2layout.addWidget(self.resetbutton)
        
        mainlayout.addWidget(self.time_left_label)
        mainlayout.addLayout(b1layout)
        mainlayout.addLayout(b2layout)

        self.setLayout(mainlayout)

    def _init_threads(self) -> None:
        self.timer_thread = WindowUpdateThread(TimerThreadData())

    def _connect_handlers(self):
        self.timer_thread.com.update.connect(self.updateTimer)
        self.startbutton.clicked.connect(self.startTimer)
        self.stopbutton.clicked.connect(self.stopTimer)
        self.resetbutton.clicked.connect(self.resetTimer)
    
    @pyqtSlot(ThreadData)
    def updateTimer(self, data: ThreadData) -> None:
        self.currenttime = data.time_passed
        self.time_left_label.setText(self._time_display(self.currenttime * 1000))

    @pyqtSlot()
    def startTimer(self) -> None:
        if not self.timer_thread.isAlive():
            self.timer_thread.start()

    @pyqtSlot()
    def stopTimer(self) -> None:
        logger.debug("stopTimer called.")
        if self.timer_thread.isAlive():
            logger.debug("killing timer thread...")
            self.timer_thread.abort = True
            self.timer_thread.join()
            self._rebuild_timerthread()

    def _rebuild_timerthread(self):
        del self.timer_thread
        self.timer_thread = WindowUpdateThread(TimerThreadData(self.currenttime))
        self.timer_thread.com.update.connect(self.updateTimer)

    @pyqtSlot()
    def resetTimer(self) -> None:
        logger.debug("resetbutton clicked!")
        self.stopTimer()
        self.time_left_label.setText(self._time_display(0.0))
        self.currenttime = 0.0
        self._rebuild_timerthread()

    def _time_display(self, time_in_ms: float) -> str:
        millisecond = math.floor(time_in_ms % 1000)
        time_in_ms /= 1000

        second = math.floor(time_in_ms % 60)
        time_in_ms /= 60

        minute = math.floor(time_in_ms % 60)
        time_in_ms /= 60

        hour = math.floor(time_in_ms)

        return f"{hour:>03}:{minute:>02}:{second:>02}.{millisecond:<03}"

class MainWindow(QMainWindow):
    def __init__(self, parent):
        logger.debug("Working")
        super(MainWindow, self).__init__(parent)
        self.setCentralWidget(TimerWidget(self))
        self.show()
    
    
def setup_logging():
    root = logging.getLogger()
    f = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] -> %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    # fh = logging.FileHandler(LOGFILE)
    # fh = RotatingFileHandler(
    #     LOGFILE,
    #     mode='a',
    #     maxBytes=((2**20) * 2.5),
    #     backupCount=2,
    #     encoding=None,
    #     delay=False)

    sh.setFormatter(f)
    # fh.setFormatter(f)

    root.addHandler(sh)
    # root.addHandler(fh)
    root.setLevel(logging.DEBUG)

def main(args):
    global logger
    setup_logging()
    logger = logging.getLogger("timer")

    app = QApplication(args)
    main_window = MainWindow(None)
    return app.exec()

if(__name__ == "__main__"):
    sys.exit(main(sys.argv))