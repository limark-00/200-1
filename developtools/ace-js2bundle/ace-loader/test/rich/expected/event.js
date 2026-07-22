/*
 * Copyright (c) 2021 Huawei Device Co., Ltd.
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

{
  "@app-component/event": {
    "_descriptor": {},
    "data": {},
    "template": {
      "attr": {
        "debugLine": "pages/event/event:1"
      },
      "children": [
        {
          "attr": {
            "debugLine": "pages/event/event:3"
          },
          "events": {
            "click": "test"
          },
          "type": "div"
        },
        {
          "attr": {
            "debugLine": "pages/event/event:6"
          },
          "events": {
            "click": "function (evt) {this.test(this.value,evt)}"
          },
          "type": "div"
        },
        {
          "attr": {
            "debugLine": "pages/event/event:9"
          },
          "events": {
            "click": "function (evt) {this.test(this.value,this.time,evt)}"
          },
          "type": "div"
        },
        {
          "attr": {
            "debugLine": "pages/event/event:12"
          },
          "events": {
            "click": "test"
          },
          "type": "div"
        },
        {
          "attr": {
            "debugLine": "pages/event/event:15"
          },
          "events": {
            "click": "function (evt) {this.test(this.value,evt)}"
          },
          "type": "div"
        },
        {
          "attr": {
            "debugLine": "pages/event/event:18"
          },
          "events": {
            "click": "function (evt) {this.test(this.value,this.time,evt)}"
          },
          "type": "div"
        },
        {
          "type": "input",
          "attr": {
            "debugLine": "pages/event/event:21"
          },
          "events": {
            "click": "function (evt) {this.handleInput('(',evt)}"
          }
        },
        {
          "type": "input",
          "attr": {
            "debugLine": "pages/event/event:24"
          },
          "events": {
            "click": "function (evt) {this.handleInput(')',evt)}"
          }
        },
        {
          "type": "input",
          "attr": {
            "debugLine": "pages/event/event:27"
          },
          "events": {
            "click": "function (evt) {this.handleInput('(',this.value,this.time,evt)}"
          }
        },
        {
          "attr": {
            "debugLine": "pages/event/event:30"
          },
          "type": "div",
          "onBubbleEvents": {
            "touchstart": "test1"
          }
        },
        {
          "attr": {
            "debugLine": "pages/event/event:31"
          },
          "type": "div",
          "onBubbleEvents": {
            "touchstart": "test2"
          }
        },
        {
          "attr": {
            "debugLine": "pages/event/event:32"
          },
          "type": "div",
          "onBubbleEvents": {
            "touchstart": "test3"
          }
        },
        {
          "attr": {
            "debugLine": "pages/event/event:33"
          },
          "type": "div",
          "catchBubbleEvents": {
            "touchstart": "test4"
          }
        },
        {
          "attr": {
            "debugLine": "pages/event/event:34"
          },
          "type": "div",
          "onBubbleEvents": {
            "touchstart": "test5"
          }
        },
        {
          "attr": {
            "debugLine": "pages/event/event:35"
          },
          "type": "div",
          "onBubbleEvents": {
            "touchstart": "test6"
          }
        },
        {
          "attr": {
            "debugLine": "pages/event/event:36"
          },
          "type": "div",
          "catchBubbleEvents": {
            "touchstart": "test7"
          }
        },
        {
          "attr": {
            "debugLine": "pages/event/event:37"
          },
          "type": "div",
          "onCaptureEvents": {
            "touchstart": "test8"
          }
        },
        {
          "attr": {
            "debugLine": "pages/event/event:38"
          },
          "type": "div",
          "catchCaptureEvents": {
            "touchstart": "test9"
          }
        }
      ],
      "type": "div"
    }
  }
}