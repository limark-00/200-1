#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2021 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import codecs
import sys
import os
import re
import time

files = []
trace_regex = "\s*(.*?)-(\d+?)\s+\(\s*(\d+?)\)\s+\[\d+\]\s+(.*?)\s+(.*?):\s+"
all_traces_dict = {} # {"deviceName": [(timestamp, line) ...]}
all_real_time_dict = {}
default_real_time = 7983849599000 # 2222-12-31 23:59:59

def compare_timestamp(time1, time2):
    return float(time1) < float(time2)

def read_files(file, devices_name):
    traces = []
    with codecs.open(file, 'r', encoding='utf-8') as fp:
        for line in fp:
            if line.find("binder_transaction") > -1 \
                or line.find("tracing_mark_write") > -1:
                line = line.replace("\n", "")
                trace_match = re.match(trace_regex, line)
                if trace_match:
                    traces.append((float(trace_match.group(5)), line))
                if line.find("realtime_ts") > -1:
                    time_regex = trace_regex + \
                        "tracing_mark_write:\s+trace_event_clock_sync: realtime_ts=(.*)"
                    time_match = re.match(time_regex, line)
                    all_real_time_dict[devices_name] = { \
                        "realtime_ts": int(time_match.group(6)), \
                        "timestamp": float(time_match.group(5))}
    if (not all_real_time_dict.__contains__(devices_name)) and traces:
        line = traces[-1][1]
        trace_match = re.match(trace_regex, line)
        all_real_time_dict[devices_name] = { \
            "realtime_ts": default_real_time, \
            "timestamp": float(trace_match.group(5))}
    return traces

def handle_option():
    if len(sys.argv) < 2:
        print("eg: python bytrace_multi.py file1.ftrace file2.ftrace ...")
        exit(0)
    for i in range(len(sys.argv)):
        if i == 0:
            continue
        if sys.argv[i] == "-h" or sys.argv[i] == "--help":
            print("eg: python bytrace_multi.py file1.ftrace file2.ftrace ...")
            exit(0)
        elif not os.path.exists(sys.argv[i]):
            print("Warning: {} is not found.".format(sys.argv[i]))
        else:
            files.append(sys.argv[i])

def change_trace_time(all_trace_list, \
                      base_real_time, \
                      base_time_stamp, \
                      target_device):
    target_real_time = all_real_time_dict[target_device]["realtime_ts"]
    target_time_stamp = all_real_time_dict[target_device]["timestamp"]
    if not target_real_time == default_real_time:
        diff_real_time = float(target_real_time - base_real_time) / 1000
        target_time_stamp_ = base_time_stamp + diff_real_time
        diff_time = target_time_stamp - target_time_stamp_
    else:
        # If the file does not have realtime, the difference is 0.5s.
        diff_real_time = 0.5
        target_time_stamp_ = base_time_stamp + diff_real_time
        diff_time = target_time_stamp - target_time_stamp_
    traces = all_traces_dict[target_device]
    for mtuple in traces:
        timestamp = float(mtuple[0])
        line = mtuple[1]
        timestamp_ = "{:.6f}".format(timestamp - diff_time)
        line_ = target_device + \
            line.replace("{:.6f}".format(timestamp), str(timestamp_))
        all_trace_list.append((timestamp_, line_))

def write_to_file(data, file_name):
    with codecs.open(file_name, 'w+', encoding='utf-8') as fp:
        fp.write("# tracer: nop\n")
        fp.write("#\n")
        fp.write("#                                      _-----=> irqs-off\n")
        fp.write("#                                     / _----=> need-resched\n")
        fp.write("#                                    | / _---=> hardirq/softirq\n")
        fp.write("#                                    || / _--=> preempt-depth\n")
        fp.write("#                                    ||| /     delay\n")
        fp.write("#           TASK-PID    TGID   CPU#  ||||    TIMESTAMP  FUNCTION\n")
        fp.write("#              | |        |      |   ||||       |         |\n")
        for mtuple in data:
            fp.write(mtuple[1])
            fp.write("\n")

def main():
    handle_option()
    if len(files) == 0:
        exit(-1)

    for i, val in enumerate(files):
        device_name = "[device_{}]".format(str(i))
        all_traces_dict[device_name] = read_files(val, device_name)

    all_time_sorted_list = sorted(all_real_time_dict.items(), key=lambda \
        all_real_time_dict: all_real_time_dict[1]["realtime_ts"])
    base_real_time = all_time_sorted_list[0][1]["realtime_ts"]
    base_time_stamp = all_time_sorted_list[0][1]["timestamp"]
    all_trace_list = [] # [(timestamp, line)]
    for mtuple in all_time_sorted_list:
        target_device = mtuple[0]
        change_trace_time(all_trace_list, \
                          base_real_time, \
                          base_time_stamp, \
                          target_device)
    # Sort by timestamp from small to large
    all_trace_sorted_list = sorted(all_trace_list, key=lambda x: x[0])
    curtime = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    write_to_file(all_trace_sorted_list, "multi_trace_"+str(curtime)+".ftrace")

if __name__ == '__main__':
    main()
