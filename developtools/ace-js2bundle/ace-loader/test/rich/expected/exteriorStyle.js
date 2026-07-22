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
  "@app-component/exteriorStyle": {
    "_descriptor": {},
    "data": {},
    "template": {
      "type": "div",
        "attr": {
          "debugLine": "pages/exteriorStyle/exteriorStyle:1",
          "value": "exteriorStyle_test"
      }
    },
    "style": {
      ".a": {
        "width": "100%",
        "height": "50%"
      },
      ".b": {
        "width": "100px",
        "height": "200px"
      },
      ".c": {
        "color": "#808080"
      },
      ".d": {
        "color": "#008000"
      },
      ".e": {
        "color": "rgba(80,60,150,1)"
      },
      ".f": {
        "animationDuration": "500ms",
        "animationDelay": "100ms"
      },
      ".g": {
        "animationIterationCount": 3
      },
      ".h": {
        "animationTimingFunction": "linear"
      },
      ".h-steps": {
        "animationTimingFunction": "steps(9,start)"
      },
      ".i": {
        "animationFillMode": "forwards"
      },
      ".j": {
        "gridTemplateColumns": "50px 40px 80px",
        "gridTemplateRows": "auto-fill 20px"
      },
      ".l": {
        "gridRowStart": 3
      },
      ".m": {
        "borderTopWidth": "5px",
        "borderRightWidth": "5px",
        "borderBottomWidth": "5px",
        "borderLeftWidth": "5px",
        "borderTopStyle": "solid",
        "borderRightStyle": "solid",
        "borderBottomStyle": "solid",
        "borderLeftStyle": "solid",
        "borderTopColor": "#808080",
        "borderRightColor": "#808080",
        "borderBottomColor": "#808080",
        "borderLeftColor": "#808080"
      },
      ".n": {
        "textIndent": "50px"
      },
      ".o": {
        "backgroundImage": "/common/img/a.jpg"
      },
      "@TRANSITION": {
        ".p": {
          "property": "width"
        },
        ".q": {
          "duration": "5s"
        }
      },
      ".p": {
        "transitionProperty": "width"
      },
      ".q": {
        "transitionDuration": "5s"
      },
      ".r": {
        "transform": "{\"translate\":\"50% 50%\"}"
      },
      ".s": {
        "transformOrigin": "20% 40%"
      },
      ".t": {
        "startAngle": "240deg"
      },
      ".u": {
        "selectedFontFamily": "PingFangSC-Regular"
      },
      ".v": {
        "paddingTop": "10px",
        "paddingRight": "15px",
        "paddingBottom": "10px",
        "paddingLeft": "15px"
      },
      "#w": {
        "fontSize": "15px",
        "fontFamily": "PingFangSC-Regular"
      },
      "@KEYFRAMES": {
        "animation1": [
          {
            "backgroundColor": "#808080",
            "time": 0
          },
          {
            "backgroundColor": "#000000",
            "time": "50"
          },
          {
            "backgroundColor": "#000fff",
            "time": 100
          }
        ],
        "animation2": [
          {
            "transform": "{\"translateX\":\"90px\"}",
            "time": 0
          },
          {
            "transform": "{\"translateX\":\"130px\"}",
            "time": "50"
          },
          {
            "transform": "{\"translateX\":\"200px\"}",
            "time": 100
          }
        ],
        "animation3": [
          {
            "transform": "{\"rotate\":\"90deg\"}",
            "time": 0
          },
          {
            "transform": "{\"rotate\":\"150deg\"}",
            "time": "50"
          },
          {
            "transform": "{\"rotate\":\"260deg\"}",
            "time": 100
          }
        ],
        "animation4": [
          {
            "transform": "{\"rotate\":\"0.25turn\"}",
            "time": 0
          },
          {
            "transform": "{\"rotate\":\"57deg\"}",
            "time": "50"
          },
          {
            "transform": "{\"rotate\":\"400grad\"}",
            "time": 100
          }
        ],
        "shared-transition": [
          {
            "opacity": 0,
            "time": 0
          },
          {
            "opacity": 1,
            "time": 100
          }
        ]
      },
      ".gradient1": {
        "background": "{\"values\":[{\"type\":\"linearGradient\",\"directions\":[\"to\",\"bottom\"],\"values\":[\"#ff0000\",\"#00ff00\"]}]}"
      },
      ".gradient2": {
        "background": "{\"values\":[{\"type\":\"linearGradient\",\"directions\":[\"45deg\"],\"values\":[\"rgb(255,0,0)\",\"rgb(0,255,0)\"]}]}"
      },
      ".gradient3": {
        "background": "{\"values\":[{\"type\":\"linearGradient\",\"directions\":[\"to\",\"right\"],\"values\":[\"rgb(255,0,0) 90px\",\"rgb(0,0,255) 60%\"]}]}"
      },
      ".gradient4": {
        "background": "{\"values\":[{\"type\":\"repeatingLinearGradient\",\"directions\":[\"to\",\"right\"],\"values\":[\"rgba(255,255,0,1) 30px\",\"rgba(0,0,255,0.5) 60px\"]}]}"
      },
      ".shared-transition-style": {
        "sharedTransitionEffect": "static",
        "sharedTransitionName": "shared-transition"
      },
      "@FONT-FACE": [
        {
          "fontFamily": "HWfont",
          "src": "url(/common/HWfont.ttf)"
        }
      ],
      ".txt": {
        "fontFamily": "HWfont"
      },
      ".shadow": {
        "boxShadowBlur": "30px",
        "boxShadowColor": "#888888",
        "boxShadowH": "100px",
        "boxShadowSpread": "40px",
        "boxShadowV": "100px"
      },
      ".transform-origin-style1":{
        "transformOrigin": "left"
      },
      ".transform-origin-style2":{
        "transformOrigin": "left bottom"
      },
      ".transform-origin-style3":{
        "transformOrigin": "right 90px"
      },
      ".transform-style1":{
        "transform": "{\"translate3d\":\"1px 2px 3px\"}"
      },
      ".transform-style2":{
        "transform": "{\"matrix\":\"1 2 3 4 5 6\"}"
      },
      ".transform-style3":{
        "transform": "{\"matrix3d\":\"1 0 0 0 0 1 6 0 0 0 1 0 50 100 0 1.1\"}"
      },
      ".transform-style4":{
        "transform": "{}"
      },
      ".transform-style5":{
        "transform": "{\"rotate3d\":\"1 1 1 30deg\",\"translate3d\":\"1px 2px 3px\",\"scale3d\":\"1.5 1.5 1.5\",\"perspective\":\"800px\"}"
      },
      ".simple-animation1":{
        "animationDuration": "3s",
        "animationTimingFunction": "ease-in",
        "animationDelay": "1s",
        "animationIterationCount": 2,
        "animationDirection": "reverse",
        "animationFillMode": "both",
        "animationPlayState": "paused",
        "animationName": "slidein"
      },
      ".simple-animation2":{
        "animationDuration": "3s",
        "animationTimingFunction": "linear",
        "animationDelay": "1s",
        "animationDirection": "normal",
        "animationPlayState": "running",
        "animationIterationCount": 1,
        "animationFillMode": "none",
        "animationName": "test_05"
      },
      ".simple-animation3":{
        "animationDuration": "3s",
        "animationDelay": "0ms",
        "animationDirection": "normal",
        "animationTimingFunction": "ease",
        "animationPlayState": "running",
        "animationIterationCount": 1,
        "animationFillMode": "none",
        "animationName": "sliding-vertically"
      },
      ".mask-image-url1": {
        "maskImage": "common/mask.svg"
      }
    }
  }
}
