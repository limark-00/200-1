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
  "@app-component/ifDirective": {
    "_descriptor": {},
    "data": {},
    "template": {
      "type": "div",
      "attr": {
        "debugLine": "pages/ifDirective/ifDirective:1"
      },
      "children": [
        {
          "type": "text",
          "attr": {
            "debugLine": "pages/ifDirective/ifDirective:3",
            "value": "function () {return this.componentData.if}"
          },
          "shown": "function () {return this.conditionVar===1}"
        },
        {
          "type": "div",
          "attr": {
            "className": "item-content",
            "debugLine": "pages/ifDirective/ifDirective:6"
          },
          "classList": [
            "item-content"
          ],
          "children": [
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/ifDirective/ifDirective:7",
                "value": "function () {return this.componentData.if}"
              },
              "shown": "function () {return this.conditionVar===1}"
            },
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/ifDirective/ifDirective:8",
                "value": "function () {return this.componentData.elif}"
              },
              "shown": "function () {return this.conditionVar===2&&!(this.conditionVar===1)}"
            },
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/ifDirective/ifDirective:9",
                "value": "function () {return this.componentData.else}"
              },
              "shown": "function () {return !(this.conditionVar===2)&&!(this.conditionVar===1)}"
            }
          ]
        },
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/ifDirective/ifDirective:13"
          },
          "shown": "function () {return this.showTest}",
          "children": [
            {
              "type": "div",
              "attr": {
                "debugLine": "pages/ifDirective/ifDirective:14"
              },
              "repeat": "function () {return this.list}",
              "children": [
                {
                  "type": "text",
                  "attr": {
                    "debugLine": "pages/ifDirective/ifDirective:15",
                    "value": "function () {return (this.$idx) + decodeURI('.') + (this.$item.name)}"
                  }
                }
              ]
            }
          ]
        },
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/ifDirective/ifDirective:20"
          },
          "repeat": "function () {return this.list}",
          "children": [
            {
              "type": "div",
              "attr": {
                "debugLine": "pages/ifDirective/ifDirective:21"
              },
              "shown": "function () {return !this.showTest}",
              "children": [
                {
                  "type": "text",
                  "attr": {
                    "debugLine": "pages/ifDirective/ifDirective:22",
                    "value": "function () {return (this.$idx) + decodeURI('.') + (this.$item.name)}"
                  }
                }
              ]
            }
          ]
        },
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/ifDirective/ifDirective:27"
          },
          "repeat": {
            "exp": "function () {return this.list}",
            "key": "personIndex",
            "value": "personItem"
          },
          "children": [
            {
              "type": "div",
              "attr": {
                "debugLine": "pages/ifDirective/ifDirective:28"
              },
              "shown": "function () {return this.personIndex==1}",
              "children": [
                {
                  "type": "text",
                  "attr": {
                    "debugLine": "pages/ifDirective/ifDirective:29",
                    "value": "function () {return this.personItem.name}"
                  }
                }
              ]
            }
          ]
        },
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/ifDirective/ifDirective:34"
          },
          "shown": "function () {return this.num1>this.num2?this.true_value:this.false_value}",
          "children": [
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/ifDirective/ifDirective:35",
                "value": "function () {return this.true_value}"
              }
            }
          ]
        }
      ]
    }
  }

}