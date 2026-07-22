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
  "render": "function (vm) { var _vm = vm || this; return _c('div') }",
  "styleSheet":  {
    "@media": [{
      "condition": "screen and (max-width: 454px)",
      "classSelectors": { "title": { "fontSize": 30, "color": 16711680 } }
    }, {
      "condition": "screen and (min-width: 455px)",
      "classSelectors": { "title": { "fontSize": 72, "color": 65280 } }
    }],
    "@keyframes":  {
      "animationChange":  [
         {
          "backgroundColor": 16711680,
          "time": 0
        },
         {
          "backgroundColor": 255,
          "time": 100
        }
      ],
      "animationChange1":  [
         {
          "time": 0,
          "transform":  {
            "translateX": "120px"
          }
        },
         {
          "time": 100,
          "transform":  {
            "translateX": "170px"
          }
        }
      ],
      "animationChange3": [
         {
          "time": 0,
          "transform":  {
            "rotate": "0deg"
          }
        },
         {
          "time": 100,
          "transform":  {
            "rotate": "360deg"
          }
        }
      ]
    },
    "classSelectors":  {
      "a":  {
        "animationDelay": "300ms",
        "animationDuration": "900ms",
        "animationFillMode": "none",
        "animationIterationCount": "1000"
      },
      "b":  {
        "animationIterationCount": "infinite",
        "backgroundImage": "url(/common/img/xmad.jpg)"
      },
      "c":  {
        "color": 16776995,
        "width": 200
      },
      "d":  {
        "color": 11674146
      },
      "f": {
          "marginBottom": "10%",
          "marginLeft": "10%",
          "marginRight": "10%",
          "marginTop": "10%"
        },
        "g": {
          "marginBottom": "108%",
          "marginLeft": "-8%",
          "marginRight": "2%",
          "marginTop": "33%"
        },
        "h": {
          "left": "20%",
          "top": "80%"
        },
        "i": {
          "height": "30%",
          "width": "100%"
        }
    },
    "idSelectors":  {
      "e":  {
        "marginBottom": 11,
        "marginLeft": 11,
        "marginRight": 11,
        "marginTop": 11
      }
    }
  }
}
