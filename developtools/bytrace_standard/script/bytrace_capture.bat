@rem Copyright (C) 2021 Huawei Device Co., Ltd.
@rem Licensed under the Apache License, Version 2.0 (the "License");
@rem you may not use this file except in compliance with the License.
@rem You may obtain a copy of the License at
@rem
@rem     http://www.apache.org/licenses/LICENSE-2.0
@rem
@rem Unless required by applicable law or agreed to in writing, software
@rem distributed under the License is distributed on an "AS IS" BASIS,
@rem WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
@rem See the License for the specific language governing permissions and
@rem limitations under the License.

@echo off
hdc shell "echo > /sys/kernel/debug/tracing/trace"
hdc shell "echo 4096 > /d/tracing/saved_cmdlines_size"
hdc shell "bytrace -t 10 -b 4096 --overwrite ohos zimage zmedia zcamera zaudio ability distributeddatamgr sched freq irq workq  rs idle load disk pagecache memreclaim > /data/mynewtrace.ftrace"
hdc shell "echo > /sys/kernel/debug/tracing/trace"
hdc shell "sed -i '1,2d' /data/mynewtrace.ftrace"
hdc pull /data/mynewtrace.ftrace .
pause
