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
  "@app-component/forDirective": {
    "_descriptor": {},
    "data": {},
    "template": {
      "type": "div",
      "attr": {
        "debugLine": "pages/forDirective/forDirective:1"
      },
      "children": [
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/forDirective/forDirective:3"
          },
          "repeat": "function () {return this.list}",
          "events": {
            "click": "function (evt) {this.test(this.$item,evt)}"
          },
          "children": [
            {
              "type": "text",
              "attr": {
                "debugLine": "pages/forDirective/forDirective:4",
                "value": "function () {return (this.$idx) + decodeURI('.') + (this.$item.name)}"
              }
            }
          ]
        },
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/forDirective/forDirective:8"
          },
          "children": [
            {
              "type": "div",
              "attr": {
                "debugLine": "pages/forDirective/forDirective:9"
              },
              "repeat": {
                "exp": "function () {return this.list}",
                "value": "personItem"
              },
              "events": {
                "click": "function (evt) {this.test(this.$idx,evt)}"
              },
              "children": [
                {
                  "type": "text",
                  "attr": {
                    "debugLine": "pages/forDirective/forDirective:10",
                    "value": "function () {return (this.$idx) + decodeURI('-') + (this.personItem.name) + decodeURI('--') + (this.personItem.age)}"
                  }
                }
              ]
            },
            {
              "type": "image",
              "attr": {
                "debugLine": "pages/forDirective/forDirective:12",
                "src": "function () {return this.personItem}"
              }
            }
          ]
        },
        {
          "type": "div",
          "attr": {
            "debugLine": "pages/forDirective/forDirective:16"
          },
          "children": [
            {
              "type": "div",
              "attr": {
                "debugLine": "pages/forDirective/forDirective:17"
              },
              "repeat": {
                "exp": "function () {return this.flexShrinkClass}",
                "value": "shrinkClass",
                "exp": "function () {return this.list}",
                "key": "personIndex",
                "value": "personItem"
              },
              "events": {
                "click": "function (evt) {this.test(this.personItem,evt)}"
              },
              "children": [
                {
                  "type": "text",
                  "attr": {
                    "debugLine": "pages/forDirective/forDirective:18",
                    "value": "function () {return (this.personIndex) + decodeURI('.') + (this.personItem.name)}"
                  }
                }
              ]
            },
            {
              "type": "swiper",
              "attr": {
                "debugLine": "pages/forDirective/forDirective:20",
                "index": "function () {return this.personIndex}",
                "loop": "function () {return this.personItem}"
              }
            }
          ]
        },
        {
          "attr": {
            "debugLine": "pages/forDirective/forDirective:24"
          },
          "children": [
            {
              "attr": {
                "debugLine": "pages/forDirective/forDirective:25"
              },
              "children": [
                {
                  "attr": {
                    "debugLine": "pages/forDirective/forDirective:26",
                    "value": "function () {return (this.personItem.id) + decodeURI('--') + (this.item.name)}"
                  },
                  "type": "text"
                }
              ],
              "repeat": {
                "exp": "function () {return this.menu}",
                "key": "index",
                "value": "item"
              },
              "type": "div"
            }
          ],
          "events": {
            "click": "function (evt) {this.test(this.personItem,evt)}"
          },
          "repeat": {
            "exp": "function () {return this.list}",
            "key": "personIndex",
            "value": "personItem"
          },
          "type": "div"
        },
        {
          "attr": {
            "debugLine": "pages/forDirective/forDirective:31"
          },
          "children": [
            {
              "attr": {
                "debugLine": "pages/forDirective/forDirective:32"
              },
              "children": [
                {
                  "attr": {
                    "debugLine": "pages/forDirective/forDirective:33",
                    "value": "function () {return (this.index) + decodeURI('--') + (this.item.name)}"
                  },
                  "type": "text"
                }
              ],
              "repeat": {
                "exp": "function () {return this.personItem}",
                "key": "index",
                "value": "item"
              },
              "type": "div"
            }
          ],
          "events": {
            "click": "function (evt) {this.test(this.personItem,evt)}"
          },
          "repeat": {
            "exp": "function () {return this.list}",
            "key": "personIndex",
            "value": "personItem"
          },
          "type": "div"
        },
        {
          "attr": {
            "debugLine": "pages/forDirective/forDirective:39"
          },
          "children": [
            {
              "attr": {
                "debugLine": "pages/forDirective/forDirective:40",
                "value": "function () {return (this.personIndex) + decodeURI('.') + (this.personItem.name)}"
              },
              "events": {
                "click": "personItem.click"
              },
              "type": "div"
            }
          ],
          "events": {
            "click": "function (evt) {this.test(this.personItem,evt)}"
          },
          "repeat": {
            "exp": "function () {return this.list}",
            "key": "personIndex",
            "value": "personItem"
          },
          "type": "div"
        },
        {
          "attr": {
            "debugLine": "pages/forDirective/forDirective:46"
          },
          "children": [
            {
              "attr": {
                "debugLine": "pages/forDirective/forDirective:47",
                "value": "function () {return this.value.info}"
              },
              "events": {
                "click": "value.click"
              },
              "type": "div"
            }
          ],
          "events": {
            "click": "function (evt) {this.test(this.value,evt)}"
          },
          "repeat": {
            "exp": "function () {return this.value.list}",
            "key": "value",
            "value": "index"
          },
          "type": "div"
        },
        {
          "attr": {
            "debugLine": "pages/forDirective/forDirective:51"
          },
          "children": [
            {
              "attr": {
                "debugLine": "pages/forDirective/forDirective:52",
                "value": "function () {return this.value.info}"
              },
              "events": {
                "click": "value.click"
              },
              "type": "div"
            }
          ],
          "events": {
            "click": "function (evt) {this.test(this.value,evt)}"
          },
          "repeat": {
            "exp": "function () {return this.flexShrinkClass}",
            "value": "shrinkClass"
          },
          "type": "div"
        }
      ]
    }
  }
}
