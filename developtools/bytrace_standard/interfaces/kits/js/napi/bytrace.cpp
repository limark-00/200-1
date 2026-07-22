/*
 * Copyright (c) 2021 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <cstdio>
#include <cstdlib>
#include <string>
#include <hilog/log.h>
#include "bytrace.h"
#include "napi/native_api.h"
#include "napi/native_node_api.h"

using namespace OHOS::HiviewDFX;
namespace {
constexpr int ARGC_NUMBER_TWO = 2;
constexpr int NAME_MAX_SIZE = 1024;
}

static napi_value JSTraceStart(napi_env env, napi_callback_info info)
{
    constexpr int ARGC_NUMBER_THREE = 3;
    size_t argc = ARGC_NUMBER_THREE;
    napi_value argv[ARGC_NUMBER_THREE];
    napi_value thisVar;
    NAPI_CALL(env, napi_get_cb_info(env, info, &argc, argv, &thisVar, NULL));
    NAPI_ASSERT(env, argc == ARGC_NUMBER_TWO || argc == ARGC_NUMBER_THREE, "Wrong number of arguments");

    napi_valuetype valueType;
    NAPI_CALL(env, napi_typeof(env, argv[0], &valueType));
    NAPI_ASSERT(env, valueType == napi_string, "First arg type error, should is string");
    char buf[NAME_MAX_SIZE] = {0};
    size_t len = 0;
    napi_get_value_string_utf8(env, argv[0], buf, NAME_MAX_SIZE, &len);
    std::string name = std::string{buf};

    NAPI_CALL(env, napi_typeof(env, argv[1], &valueType));
    NAPI_ASSERT(env, valueType == napi_number, "Second arg type error, should is number");
    int taskId = 0;
    napi_get_value_int32(env, argv[1], &taskId);
    if (argc == ARGC_NUMBER_TWO) {
        StartAsyncTrace(BYTRACE_TAG_APP, name, taskId);
    } else {
        NAPI_CALL(env, napi_typeof(env, argv[ARGC_NUMBER_TWO], &valueType));
        NAPI_ASSERT(env, valueType == napi_number, "Third arg type error, should is number");
        double limit = 0;
        napi_get_value_double(env, argv[ARGC_NUMBER_TWO], &limit);
        StartAsyncTrace(BYTRACE_TAG_APP, name, taskId, limit);
    }
    return nullptr;
}

static napi_value JSTraceFinish(napi_env env, napi_callback_info info)
{
    size_t argc = ARGC_NUMBER_TWO;
    napi_value argv[ARGC_NUMBER_TWO];
    napi_value thisVar;
    NAPI_CALL(env, napi_get_cb_info(env, info, &argc, argv, &thisVar, NULL));
    NAPI_ASSERT(env, argc == ARGC_NUMBER_TWO, "Wrong number of arguments");

    napi_valuetype valueType;
    NAPI_CALL(env, napi_typeof(env, argv[0], &valueType));
    NAPI_ASSERT(env, valueType == napi_string, "First arg type error, should is string");
    char buf[NAME_MAX_SIZE] = {0};
    size_t len = 0;
    napi_get_value_string_utf8(env, argv[0], buf, NAME_MAX_SIZE, &len);
    std::string name = std::string{buf};

    NAPI_CALL(env, napi_typeof(env, argv[1], &valueType));
    NAPI_ASSERT(env, valueType == napi_number, "Second arg type error, should is number");
    int taskId = 0;
    napi_get_value_int32(env, argv[1], &taskId);
    FinishAsyncTrace(BYTRACE_TAG_APP, name, taskId);
    return nullptr;
}

static napi_value JSTraceCount(napi_env env, napi_callback_info info)
{
    size_t argc = ARGC_NUMBER_TWO;
    napi_value argv[ARGC_NUMBER_TWO];
    napi_value thisVar;
    NAPI_CALL(env, napi_get_cb_info(env, info, &argc, argv, &thisVar, NULL));
    NAPI_ASSERT(env, argc == ARGC_NUMBER_TWO, "Wrong number of arguments");

    napi_valuetype valueType;
    NAPI_CALL(env, napi_typeof(env, argv[0], &valueType));
    NAPI_ASSERT(env, valueType == napi_string, "First arg type error, should is string");
    char buf[NAME_MAX_SIZE] = {0};
    size_t len = 0;
    napi_get_value_string_utf8(env, argv[0], buf, NAME_MAX_SIZE, &len);
    std::string name = std::string{buf};

    NAPI_CALL(env, napi_typeof(env, argv[1], &valueType));
    NAPI_ASSERT(env, valueType == napi_number, "Second arg type error, should is number");
    int64_t count = 0;
    napi_get_value_int64(env, argv[1], &count);
    CountTrace(BYTRACE_TAG_APP, name, count);
    return nullptr;
}

EXTERN_C_START
/*
 * function for module exports
 */
static napi_value BytraceInit(napi_env env, napi_value exports)
{
    static napi_property_descriptor desc[] = {
        DECLARE_NAPI_FUNCTION("startTrace", JSTraceStart),
        DECLARE_NAPI_FUNCTION("finishTrace", JSTraceFinish),
        DECLARE_NAPI_FUNCTION("traceByValue", JSTraceCount),
    };
    NAPI_CALL(env, napi_define_properties(env, exports, sizeof(desc) / sizeof(desc[0]), desc));
    return exports;
}
EXTERN_C_END

/*
 * Module definition
 */
static napi_module bytrace_module = {
    .nm_version = 1,
    .nm_flags = 0,
    .nm_filename = "bytrace",
    .nm_register_func = BytraceInit,
    .nm_modname = "bytrace",
    .nm_priv = ((void *)0),
    .reserved = {0}
};

/*
 * Module registration
 */
extern "C" __attribute__((constructor)) void RegisterModule(void)
{
    napi_module_register(&bytrace_module);
}
