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
  "@app-component/expression": {
    "_descriptor": {},
    "data": {},
    "template": {
      "type": "div",
        "attr": {
          "debugLine": "pages/expression/expression:1"
        },
      "children": [
        {
          "type": "text",
          "attr": {
            "debugLine": "pages/expression/expression:3",
            "value": "function () {return this.ti||this.subTitle}"
          }
        },
        {
          "type": "text",
          "attr": {
            "debugLine": "pages/expression/expression:8",
            "value": "function () {return this.ti&&this.subTitle}"
          }
        },
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/expression/expression:13",
            "value": "function () {return this.isArrived==='arrived'&&this.isTravel===false}"
          }
        },
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/expression/expression:18",
            "value": "function () {return this.isArrived==='arrived'||this.isTravel===false}"
          }
        },
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/expression/expression:23",
            "value": "function () {return !this.flag}"
          }
        },
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/expression/expression:28",
            "value": "function () {return !!this.flag}"
          }
        },
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/expression/expression:33",
            "className": "container"
          },
          "classList": [
            "container"
          ],
          "children": [
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/expression/expression:34",
                "className": "text-text",
                "value": "function () {return  false?0:4}"
              },
              "classList": [
                "text-text"
              ]
            },
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/expression/expression:35",
                "className": "text-text",
                "value": "function () {return this.a}"
              },
              "classList": [
                "text-text"
              ]
            },
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/expression/expression:36",
                "className": "text-text",
                "value": "function () {return  false?0:this.b}"
              },
              "classList": [
                "text-text"
              ]
            },
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/expression/expression:37",
                "className": "text-text",
                "value": "function () {return  false?0:null}"
              },
              "classList": [
                "text-text"
              ]
            },
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/expression/expression:38",
                "className": "{{this.a}}{{Math.PI}}"
              },
              "classList": "function () {return [this.a+Math.PI]}"
            },
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/expression/expression:39",
                "className": "text-text",
                "value": "function () {return 1>this.b?this.v>4?this.a:6:7}"
              },
              "classList": [
                "text-text"
              ]
            },
            {
              "type": "text",
              "attr": {
                "className": "text-text",
                "debugLine": "pages/expression/expression:40",
                "value": "function () {return  false?0:7}"
              },
              "classList": [
                "text-text"
              ]
            },
            {
              "type": "text",
              "attr": {
                "className": "text-text",
                "debugLine": "pages/expression/expression:41",
                "value": "function () {return  false?0:7}"
              },
              "classList": [
                "text-text"
              ]
            },
            {
              "type": "text",
              "attr": {
                "className": "text-text",
                "debugLine": "pages/expression/expression:42",
                "value": "function () {return typeof 1}"
              },
              "classList": [
                "text-text"
              ]
            },
            {
              "type": "text",
              "attr": {
                "className": "text-text",
                "debugLine": "pages/expression/expression:43",
                "value": "function () {return new RegExp('123')}"
              },
              "classList": [
                "text-text"
              ]
            },
            {
              "type": "input",
              "attr": {
                "debugLine": "pages/expression/expression:44",
                "value": "function () {return 'ABCDEFG'.toLowerCase()}"
              }
            },
            {
              "type": "input",
              "attr": {
                "debugLine": "pages/expression/expression:45",
                "value": "function () {return this.ns[1]}"
              }
            },
            {
              "type": "input",
              "attr": {
                "debugLine": "pages/expression/expression:46",
                "value": "function () {return this.a.b.c.d}"
              }
            },
            {
              "type": "input",
              "attr": {
                "debugLine": "pages/expression/expression:47",
                "value": "function () {return this.a.b.c[1]}"
              }
            },
            {
              "type": "input",
              "attr": {
                "debugLine": "pages/expression/expression:48",
                "value": "function () {return this.a.b.c[1]}"
              }
            },
            {
              "type": "text",
              "attr": {
                "className": "tab-text",
                "debugLine": "pages/expression/expression:49",
                "value": "function () {return this.$t('strings.home.tabsData')[this.$item].name}"
              },
              "classList": [
                "tab-text"
              ],
              "repeat": "function () {return this.tabsContent}"
            },
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/expression/expression:50",
                "value": "a"
              },
              "shown": "function () {return this.showauto}"
            },
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/expression/expression:51",
                "value": "b"
              },
              "shown": "function () {return !this.showauto}"
            },
            {
              "type": "button",
              "attr": {
                "className": "button_menu",
                "debugLine": "pages/expression/expression:52",
                "value": "go to demo ability"
              },
              "classList": [
                "button_menu"
              ],
              "events": {
                "click": "function (evt) {this.startAbility('com.example.showcases','ShowcasesAbility',{origin:'showcases'},evt)}"
              }
            },
            {
              "type": "div",
              "attr": {
                "className": "item-content",
                "debugLine": "pages/expression/expression:53"
              },
              "classList": [
                "item-content"
              ],
              "children": [
                {
                  "type": "picker",
                  "attr": {
                    "className": "picker",
                    "debugLine": "pages/expression/expression:54",
                    "type": "multi-text",
                    "range": "function () {return this.range1.arr}",
                    "value": "function () {return this.curDate}",
                    "selected": "function () {return this.lastSelected}",
                    "id": "picker1"
                  },
                  "classList": [
                    "picker"
                  ],
                  "events": {
                    "change": "getDate",
                    "cancel": "cancel"
                  },
                  "id": "picker1"
                }
              ]
            },
            {
              "type": "div",
              "attr": {
                "className": "content_for",
                "debugLine": "pages/expression/expression:57"
              },
              "classList": [
                "content_for"
              ],
              "children": [
                {
                  "type": "text",
                  "attr": {
                    "className": "topic",
                    "debugLine": "pages/expression/expression:58",
                    "value": "测试show,if,for渲染属性"
                  },
                  "classList": [
                    "topic"
                  ]
                },
                {
                  "type": "text",
                  "attr": {
                    "className": "text_large",
                    "debugLine": "pages/expression/expression:59",
                    "tid": "id",
                    "value": "function () {return (this.$idx) + decodeURI('+') + (this.$item.id)}"
                  },
                  "classList": [
                    "text_large"
                  ],
                  "repeat": "function () {return this.list}"
                },
                {
                  "type": "text",
                  "attr": {
                    "className": "text_large",
                    "debugLine": "pages/expression/expression:60",
                    "value": "点击显示的文本,点击此处显示show文本"
                  },
                  "classList": [
                    "text_large"
                  ],
                  "shown": "function () {return this.click}",
                  "events": {
                    "click": "change_showon"
                  }
                },
                {
                  "type": "text",
                  "attr": {
                    "className": "text_large",
                    "debugLine": "pages/expression/expression:61",
                    "value": "长按显示的文本，点击此处隐藏show文本"
                  },
                  "classList": [
                    "text_large"
                  ],
                  "shown": "function () {return this.longpress&&!this.click}",
                  "events": {
                    "longpress": "change_showoff"
                  }
                },
                {
                  "type": "text",
                  "attr": {
                    "debugLine": "pages/expression/expression:62",
                    "value": "默认显示的文本"
                  },
                  "shown": "function () {return !this.longpress&&!this.click}"
                },
                {
                  "type": "text",
                  "attr": {
                    "className": "text",
                    "debugLine": "pages/expression/expression:63",
                    "show": "function () {return this.showTest}",
                    "value": "show显示的文本"
                  },
                  "classList": [
                    "text"
                  ]
                }
              ]
            },
            {
              "type": "text",
              "attr": {
                "className": "remain_day_number",
                "debugLine": "pages/expression/expression:65",
                "value": "function () {return this.$t('strings.remain_days',{year:this.currentYear,day:this.countDownDays})}"
              },
              "classList": [
                "remain_day_number"
              ]
            }
          ]
        }
      ]
    }
  }
}