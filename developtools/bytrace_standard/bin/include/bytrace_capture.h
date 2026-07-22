/*
 * Copyright (C) 2021 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef DEVELOPTOOLS_BYTRACE_ADAPTER_INCLUDE_BYTRACE_CAPTURE_H
#define DEVELOPTOOLS_BYTRACE_ADAPTER_INCLUDE_BYTRACE_CAPTURE_H

#include <string>
#include <map>

const int MAX_SYS_FILES = 11;
enum TraceType { USER, KERNEL };
struct TagCategory {
    std::string name;
    std::string description;
    uint64_t tag;
    TraceType type;
    struct {
        std::string path;
    } sysfiles[MAX_SYS_FILES];
};

std::string GetPropertyInner(const std::string& property, const std::string& value);
bool SetPropertyInner(const std::string& property, const std::string& value);
void RefreshBinderServices();
bool RefreshHalServices();
#endif // DEVELOPTOOLS_BYTRACE_ADAPTER_INCLUDE_BYTRACE_CAPTURE_H
