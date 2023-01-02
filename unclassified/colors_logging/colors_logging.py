#!/usr/bin/env python3

__all__ = ['colors_logging']

'''
    使用说明：
        1. 只要你使用logging.Logger.info输出日志，那么，就不要再使用logging.info的方式输出日志。
        2. 在调用create_logger方法之前，可以通过修改类的属性来修改样式。
        3. create_logger的name参数十分重要，有明确依赖关系的模块可以通过name参数完成继承。例如：
            a.py脚本如下：
                from b import somethings
                from ipgs_lib.colors_logging import colors_logging
                logger = colors_logging().create_logging(name = 'a')
            那么，b.py脚本写成下面这样：
                import logging
                logging.getLogger('a.b')
            这样，b.py脚本中的日志记录器会直接继承a.py脚本中日志记录器。
        4. create_logger方法支持将日志输出到标准输出，也可以通过log_file参数同时把日志记录到文件中。
        5. multi_mode参数为True时启动进程安全。
'''

import os
import time
import logging
import colorlog

from random import random
from logging import FileHandler

class SafeFileHandler(FileHandler):
    '''
        Logging File Handle for Process Level Security
    '''
    def __init__(self, filename, mode, encoding = None, delay = 0):
        FileHandler.__init__(self, filename, mode, encoding, delay)
        self.mode = mode
        self.encoding = encoding
        self.time = 0
        self.begin_status = 0

    def emit(self, record):
        try:
            if self.check_status(record):
                self.rebuild()
            FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
            
    def check_status(self, record):
        '''
            Check Time and File Status
        '''
        if self.begin_status == 0:
            time.sleep(random())
            self.begin_status = 1

        if os.path.exists(self.baseFilename) and self.time == time.time():
            return 0
        else:
            return 1

    def rebuild(self):
        """
            Reopen stream
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        self.time = time.time()
        self.mode = 'a'
        if not self.delay:
            self.stream = self._open()


class colors_logging:
    def __init__(self, multi_mode:bool = False) -> None:
        '''
            Colors logging Class
                1. This class implements color logging by importing logging and colorlog.
                2. This class packages the code required to generate the 'Logger' object for easy use.
        '''
        self.debug_color = 'white'
        self.info_color = 'green'
        self.warning_color = 'yellow'
        self.error_color = 'red'
        self.critical_color = 'bold_red'
        self.fmt = '%(log_color)s[%(levelname)s] - %(asctime)s - %(name)s : %(message)s'
        self.file_fmt = '[%(levelname)s] - %(asctime)s - %(name)s : %(message)s'
        self.datefmt = '%Y-%m-%d %H:%M:%S'
        if isinstance(multi_mode, bool):
            self.multi_mode = multi_mode
        else:
            raise TypeError("Argument multi_mode is a bool type!")

    def create_logger(self, name:str, level:str = 'INFO', log_file:str = '', mode:str = 'w', encoding:str = 'utf8', show:bool = True) -> logging.Logger:
        #0 build logger object
        logger = logging.getLogger(name)
        logger.setLevel(level)
        #1 build formatter object
        colors_config = {'DEBUG': self.debug_color, 'INFO': self.info_color, 'WARNING': self.warning_color, 'ERROR': self.error_color,'CRITICAL': self.critical_color}
        formatter = colorlog.ColoredFormatter(fmt = self.fmt, datefmt = self.datefmt, log_colors = colors_config, reset = True, style = '%')
        #2 add stdout handle
        if show:
            stdout = logging.StreamHandler()
            stdout.setFormatter(formatter)
            logger.addHandler(stdout)
        #3 add file handle
        if log_file != '':
            file_formatter = colorlog.ColoredFormatter(fmt = self.file_fmt, datefmt = self.datefmt, reset = False, style = '%')
            if self.multi_mode:
                fileout = SafeFileHandler(filename = log_file, mode = mode, encoding = encoding)
            else:
                fileout = logging.FileHandler(filename = log_file, mode = mode, encoding = encoding)
            fileout.setFormatter(file_formatter)
            logger.addHandler(fileout)
        if not show and log_file == '':
            null_handle = logging.NullHandler()
            logger.addHandler(null_handle)
        return logger