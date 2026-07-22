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
  "@app-component/importJS": {
    "_descriptor": {},
    "back": "function back() {\n    _system[\"default\"].back();\n  }",
    "data": {},
    "template": {
      "attr": {
        "className": "back_container",
        "debugLine": "pages/importJS/importJS:1"
      },
      "children": [
        {
          "attr": {
            "className": "image_back",
            "debugLine": "pages/importJS/importJS:2",
            "src": "/common/image/back.png"
          },
          "classList": [
            "image_back"
          ],
          "type": "image"
        },
        {
          "attr": {
            "className": "text_back",
            "debugLine": "pages/importJS/importJS:3",
            "value": "返回"
          },
          "classList": [
            "text_back"
          ],
          "type": "text"
        }
      ],
        "classList": [
          "back_container"
        ],
          "events": {
        "click": "back"
      },
      "type": "div"
    }
  }
}