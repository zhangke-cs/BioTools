#!/usr/bin/env python3

__all__ = ['FileSlicer', 'MultiFileSlicer']

'''
    Readme:
        FileSlicer use seek and tell function to split file by line and chunk size.
        Pass a result of FileSlicer to the child process, and then start parallel processing.
        Other languages that support seek and tell function can also do the same.
    Options:
        file_list: [file_path1, file_path2, ...]
        chunk_size: important parameter, decide how big the file is to be divided into, unit is byte.
        split_num: recalculate chunk_size according to the input value.
        skip: skip the first few lines.
    Result format:
        pointers attr: [(file_path, begin_pointer, end_pointer), (...), ...]
'''

import os
import multiprocessing as mp

from typing import List

class MultiFileSlicer:
    '''
        #Multi-process efficiency: 399 files with a total size of 854GB, 51 minutes for a single process, 15 minutes for a 5-process.
        #Test platform: HPC, file is in GPFS(IBM, 193T)
        #If you think the single-threaded splitting speed is not ideal, please use this.
        from file_slice import MultiFileSlicer
        for every_block in MultiFileSlicer([fp1, fp2], 100000).pointers:
            b = open(every_block[0], 'rb')
            b.seek(every_block[1])
            c = b.read(every_block[2] - every_block[1]) #c is data for sub process.
    '''
    def __init__(self, file_list:List[str], threads:int = 5, chunk_size:int = 100000, split_num:int = 0, header:List[int] = [],
        encoding:str = 'utf8', skip:bool = False):
        if not isinstance(file_list, List):
            raise TypeError("file_list is List, but now is %s" % type(file_list))
        if not isinstance(header, List):
            raise TypeError("header is List, but now is %s" % type(header))
        if len(header) < len(file_list):
            header += [0 for _ in range(len(file_list) - len(header))]
        elif len(header) > len(file_list):
            raise ValueError("length of file list is %d, length of skip list is %d, skip gt file???" % (len(file_list), len(header)))
        self.encoding = encoding
        self.skip = skip
        self.pointers, self.header = self.begin(file_list, threads, chunk_size, split_num, header)

    def begin(self, file_list:list, threads:int = 5, chunk_size:int = 100000, split_num:int = 0, header:list = []) -> tuple:
        pool = mp.Pool(processes = threads)
        pool_result = []
        for every_file, every_header in zip(file_list, header):
            parameters = [every_file, chunk_size, split_num, every_header]
            pool_result.append(pool.apply_async(self.seek_file, parameters))
        result, final_result, final_header = [], [], []
        for e in pool_result:
            e.wait()
            result = e.get()
            final_result += result[0]
            final_header += result[1]
        pool.close()
        pool.join()
        return final_result, final_header

    def seek_file(self, file:str, chunk_size:int = 100000, split_num:int = 0, every_header:int = 0) -> list:
        seek_result, header_result = [], []
        if not os.path.exists(file):
            raise FileNotFoundError("%s is not found!" % (file))
        init_pointer = 0
        total_size = os.path.getsize(file)
        input_handle = open(file, 'rb')
        if every_header > 0:
            one_header = []
            for _ in range(0, every_header):
                if self.skip:
                    _ = input_handle.readline()
                else:
                    one_header.append(input_handle.readline().decode(encoding = self.encoding).strip("\n"))
            header_result.append(one_header)
            init_pointer = input_handle.tell()
        if split_num >= 1:
            #recalculate chunk_size
            chunk_size = int((total_size - init_pointer) / split_num)
        while init_pointer < total_size:
            #seek and find line ends
            input_handle.seek(chunk_size, 1)
            _ = input_handle.readline()
            now_pointer = input_handle.tell()
            if now_pointer == init_pointer:
                continue
            else:
                #save result
                seek_result.append((file, init_pointer, now_pointer))
                #because the readline method is used
                init_pointer = now_pointer
        '''
            The problem of the last loop exceeding the file size is not dealt with,
            because it will automatically stop if it exceeds the file size during reading
        '''
        input_handle.close()
        return [seek_result, header_result]

class FileSlicer:
    '''
        from file_slice import FileSlicer
        for every_block in FileSlicer([fp1, fp2], 100000).pointers:
            b = open(every_block[0], 'rb')
            b.seek(every_block[1])
            c = b.read(every_block[2] - every_block[1]) #c is data for sub process
    '''
    def __init__(self, file_list:List[str], chunk_size:int = 100000, split_num:int = 0, header:List[int] = [], encoding:str = 'utf8', skip:bool = False):
        if not isinstance(file_list, List):
            raise TypeError("file_list is List, but now is %s" % type(file_list))
        if not isinstance(header, List):
            raise TypeError("header is List, but now is %s" % type(header))
        self.encoding = encoding
        self.skip = skip
        self.pointers, self.header = self.seek_file(file_list, chunk_size, split_num, header)

    def seek_file(self, file_list:list, chunk_size:int = 100000, split_num:int = 0, header:list = []) -> tuple:
        if len(header) < len(file_list):
            header += [0 for _ in range(len(file_list) - len(header))]
        elif len(file_list) < len(header):
            raise ValueError("length of file list is %d, length of skip list is %d, skip gt file???" % (len(file_list), len(header)))
        seek_result, header_result = [], []
        for every_file, every_header in zip(file_list, header):
            if not os.path.exists(every_file):
                raise FileNotFoundError("%s is not found!" % (every_file))
            init_pointer = 0
            total_size = os.path.getsize(every_file)
            input_handle = open(every_file, 'rb')
            if every_header > 0:
                one_header = []
                for _ in range(0, every_header):
                    if self.skip:
                        _ = input_handle.readline()
                    else:
                        one_header.append(input_handle.readline().decode(encoding = self.encoding).strip("\n"))
                header_result.append(one_header)
                init_pointer = input_handle.tell()
            if split_num >= 1:
                #recalculate chunk_size
                chunk_size = int((total_size - init_pointer) / split_num)
            while init_pointer < total_size:
                #seek and find line ends
                input_handle.seek(chunk_size, 1)
                _ = input_handle.readline()
                now_pointer = input_handle.tell()
                if now_pointer == init_pointer:
                    continue
                else:
                    #save result
                    seek_result.append((every_file, init_pointer, now_pointer))
                    #because the readline method is used
                    init_pointer = now_pointer
            '''
                The problem of the last loop exceeding the file size is not dealt with,
                because it will automatically stop if it exceeds the file size during reading
            '''
            input_handle.close()
        return seek_result, header_result

class FileSlicerAlpha:
    '''
        NOT RECOMMENDED FOR USE
        Read file and recode pointer, no support chinese and so slow
    '''
    def __init__(self, file_list, line_num, encoding = 'utf8', header = False):
        self.pointer_list = self.__seek_file(file_list, line_num, encoding, header)

    def __seek_file(self, file_list, line_num, file_encoding, header):
        seek_result = []
        for every_file in file_list:
            init_pointer = 0
            now_num = 0
            if os.path.exists(every_file):
                with open(every_file, 'rb', encoding = file_encoding) as input_handle:
                    if header:
                        _ = input_handle.readline()
                        init_pointer = input_handle.tell() + 1
                    while True:
                        line = input_handle.readline()
                        now_num += 1
                        if not line:
                            break
                        if now_num == line_num:
                            seek_result.append([every_file, init_pointer, input_handle.tell(), now_num])
                            now_num = 0
                            init_pointer = input_handle.tell() + 1
                    if now_num > 0:
                        seek_result.append([every_file, init_pointer, input_handle.tell(), now_num])
            else:
                raise Exception("file is %s, not found!" % (every_file))
        return seek_result
