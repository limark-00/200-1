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
  "@app-component/class": {
    "_descriptor": {},
    "data": {},
    "template": {
      "type": "div",
        "attr": {
          "className": "container",
          "debugLine": "pages/class/class:1"
        },
      "classList": [
        "container"
      ],
        "children": [
          {
            "type": "div",
            "attr": {
              "className": "title",
              "debugLine": "pages/class/class:3",
              "value": "class_test1"
            },
            "classList": [
              "title"
            ]
          },
          {
            "type": "div",
            "attr": {
              "className": "title table",
              "debugLine": "pages/class/class:6",
              "value": "class_test2"
            },
            "classList": [
              "title",
              "table"
            ]
          },
          {
            "type": "div",
            "attr": {
              "className": "{{flag ? 'item' : 'item-selected'}}",
              "debugLine": "pages/class/class:9",
              "value": "class_test3"
            },
            "classList": "function () {return [this.flag?'item':'item-selected']}"
          },
          {
            "type": "div",
            "attr": {
              "className": "{{a}}    {{c}}",
              "debugLine": "pages/class/class:12",
              "value": "class_test4"
            },
            "classList": "function () {return [this.a, this.c]}"
          },
          {
            "type": "div",
            "attr": {
              "className": "{{$idx}}{{d}} + {{$item.id}} aa",
              "debugLine": "pages/class/class:15",
              "value": "class_test5"
            },
            "classList": "function () {return [this.$idx+this.d, '+', this.$item.id, 'aa']}"
          }
        ]
    }
  }
}