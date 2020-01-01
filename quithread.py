import threading, time, logging
from PyQt5.QtCore import pyqtSignal, QObject

logger = logging.getLogger("quithread")

class ThreadData:
    '''
    Defines an object that stores stateful data during the lifetime of a thread.

    This object is also where the functor for the thread (the 'meat' of the thread) is stored.

    Inherit from this and override:
        setlocals: to initialize thread-local data on thread execution.
        run_action: the function that is essentially the thread after initialization.  Assume setlocals called beforehand.
    '''

    def __init__(self, action=None):
        '''
        __init__(self, action):
            initializes this thread data with a functor representing the process of the thread.  action should take
                no arguments.  When it is none, it is expected that the member function 'run' be overridden in the
                inheriting class.
        '''
        super(ThreadData, self).__init__()
        self.local = None
        self.action = action

        #when this is true, the UI thread will emit the 'update' signal.
        #this is set to false after an update.
        self.should_update = True

        #specifies that the thread is finished.  Set to true to
        #end thread execution.
        self.finished = False
    
    def setlocals(self) -> None:
        raise NotImplementedError(ThreadData.setlocals.__qualname__ + ": Not implemented")
    
    def run_action(self) -> None:
        if self.action is None:
            raise NotImplementedError(ThreadData.run_action.__qualname__ + ": Not implemented")
        self.action()
        self.should_update = True

class WindowUpdateThread(threading.Thread):
    class QtComObject(QObject):
        update = pyqtSignal(ThreadData)
        started = pyqtSignal(ThreadData)
        finished = pyqtSignal(ThreadData)

    def __init__(self, threaddata: ThreadData):
        '''
        __init__(action)
            initializes this object with a functor that takes no arguments.  
        '''
        super(WindowUpdateThread, self).__init__()

        if not isinstance(threaddata, ThreadData):
            raise TypeError("Passed an object not of type ThreadData to WindowUpdateThread!")

        self.threaddata = threaddata
        self.com = WindowUpdateThread.QtComObject()
        self.abort = False

    def run(self) -> None:
        self.threaddata.setlocals()
        self.com.started.emit(self.threaddata)
        while not self.abort and not self.threaddata.finished:
            time.sleep(1 / 60)
            self.threaddata.run_action()
            if self.threaddata.should_update:
                self.threaddata.should_update = False
                self.com.update.emit(self.threaddata)
        self.com.finished.emit(self.threaddata)
        