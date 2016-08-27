import keras
from keras import backend as K
import time
import os
import datetime
import numpy as np

class ProgressTracker(keras.callbacks.Callback):
    def __init__(self, task, save_weights=True):
        self.task = task
        self.save_weights = save_weights
        self.start_time = time.time()
        super(ProgressTracker, self).__init__()
        self.task.set('status.progress', 0)

    def on_batch_begin(self, batch, logs={}):
        if self.task.abort.is_set():
            self.task.set('status.error', 'interrupted')
            self.model.stop_training = True
            raise Exception('stopped by user')

    def on_batch_end(self, batch, logs={}):
        info = ''
        for k, v in logs.items():
            if isinstance(v, (np.ndarray, np.generic) ):
                vstr = str(v.tolist())
            else:
                vstr = str(v)
            info += "{}: {}\n".format(k,vstr)
        self.elapsed_time = time.time()-self.start_time
        info += "elapsed_time: {:.2f}s".format(self.elapsed_time)
        self.task.update('status.info', info)
        self.task.update('status.progress', batch%100)

    def on_epoch_begin(self, epoch, logs={}):
        self.task.set('status.stage', 'epoch #'+str(epoch))
        if hasattr(self.model.optimizer, 'lr'):
            if self.task.get('config.learning_rate'):
                lr = float(self.task.get('config.learning_rate'))
                K.set_value(self.model.optimizer.lr, lr)
            else:
                lr = K.get_value(self.model.optimizer.lr).tolist()
            self.task.push('output.learning_rate', lr)
        else:
            self.task.set('status.error', 'Optimizer must have a "lr" attribute.')

    def on_epoch_end(self, epoch, logs={}):
        self.task.push('output.epoch', epoch)
        for k, v in logs.items():
            self.task.push('output.'+k, v)
        self.task.set('output.elapsed_time', "%.2fs"%self.elapsed_time)
        self.task.set('output.last_epoch_update_time', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))