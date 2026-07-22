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
  "@app-component/privateAttr": {
    "_descriptor": {},
    "data": {},
    "template": {
      "type": "div",
        "attr": {
          "className": "container",
          "debugLine": "pages/privateAttr/privateAttr:1"
        },
      "classList": [
        "container"
      ],
        "children": [
          {
            "type": "list",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:3",
              "scrollpage": "function () {return this.scrollpage}",
              "cachedcount": "function () {return this.cachedcount}",
              "scrollbar": "function () {return this.scrollbar}",
              "scrolleffect": "function () {return this.scrolleffect}",
              "indexer": "function () {return this.indexer}",
              "shapemode": "function () {return this.shapemode}",
              "updateeffect": "function () {return this.updateeffect}",
              "initialindex": "function () {return this.initialindex}",
              "initialoffset": "function () {return this.initialoffset}"
            },
            "children": [
              {
                "type": "list-item-group",
                "attr": {
                  "debugLine": "pages/privateAttr/privateAttr:5",
                  "type": "function () {return this.type}"
                }
              },
              {
                "type": "list-item",
                "attr": {
                  "debugLine": "pages/privateAttr/privateAttr:6",
                  "type": "function () {return this.type}",
                  "primary": "function () {return this.primary}",
                  "section": "function () {return this.section}",
                  "sticky": "function () {return this.sticky}",
                  "stickyradius": "function () {return this.stickyradius}",
                  "clickeffect": "function () {return this.clickeffect}"
                }
              }
            ]
          },
          {
            "type": "swiper",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:10",
              "index": "function () {return this.index}",
              "autoplay": "function () {return this.autoplay}",
              "interval": "function () {return this.interval}",
              "indicator": "function () {return this.indicator}",
              "digital": "function () {return this.digital}",
              "loop": "function () {return this.loop}",
              "duration": "function () {return this.duration}",
              "vertical": "function () {return this.vertical}",
              "indicatordisabled": "true"
            }
          },
          {
            "type": "tabs",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:15",
              "index": "function () {return this.index}",
              "vertical": "function () {return this.vertical}"
            },
            "children": [
              {
                "type": "tab-bar",
                "attr": {
                  "debugLine": "pages/privateAttr/privateAttr:16",
                  "mode": "function () {return this.mode}"
                }
              },
              {
                "type": "tab-content",
                "attr": {
                  "debugLine": "pages/privateAttr/privateAttr:17",
                  "scrollable": "function () {return this.scrollable}"
                }
              }
            ]
          },
          {
            "type": "popup",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:21",
              "target": "title",
              "placement": "function () {return this.placement}",
              "keepalive": "true",
              "clickable": "false",
              "arrowoffset": "20px"
            }
          },
          {
            "type": "refresh",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:24",
              "offset": "function () {return this.offset}",
              "refreshing": "function () {return this.refreshing}",
              "type": "auto",
              "lasttime": "function () {return this.lasttime}",
              "friction": "function () {return this.friction}"
            }
          },
          {
            "type": "image",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:27",
              "alt": "img",
              "src": "function () {return this.src}"
            }
          },
          {
            "type": "image-animator",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:30",
              "images": "function () {return this.images}",
              "iteration": "function () {return this.iteration}",
              "reverse": "function () {return this.reverse}",
              "fixedsize": "function () {return this.fixedsize}",
              "duration": "function () {return this.duration}"
            }
          },
          {
            "type": "progress",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:33",
              "type": "horizontal",
              "percent": "function () {return this.percent}",
              "secondarypercent": "function () {return this.secondarypercent}"
            }
          },
          {
            "type": "progress",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:36",
              "type": "scale-ring",
              "percent": "function () {return this.percent}",
              "secondarypercent": "function () {return this.secondarypercent}",
              "clockwise": "function () {return this.clockwise}"
            }
          },
          {
            "type": "progress",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:39",
              "type": "arc",
              "percent": "function () {return this.percent}"
            }
          },
          {
            "type": "rating",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:42",
              "numstars": "function () {return this.numstars}",
              "rating": "function () {return this.rating}",
              "stepsize": "function () {return this.stepsize}",
              "indicator": "function () {return this.indicator}"
            }
          },
          {
            "type": "marquee",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:45",
              "scrollamount": "function () {return this.scrollamount}",
              "loop": "function () {return this.loop}",
              "direction": "function () {return this.direction}"
            }
          },
          {
            "type": "divider",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:48",
              "vertical": "function () {return this.vertical}"
            }
          },
          {
            "type": "search",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:51",
              "icon": "function () {return this.icon}",
              "hint": "function () {return this.hint}",
              "value": "function () {return this.value}",
              "searchbutton": "content"
            }
          },
          {
            "type": "menu",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:54",
              "target": "function () {return this.target}",
              "type": "function () {return this.type}",
              "title": "function () {return this.title}"
            }
          },
          {
            "type": "chart",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:57",
              "type": "line",
              "options": "function () {return this.options}",
              "datasets": "function () {return this.datasets}"
            }
          },
          {
            "type": "input",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:60",
              "type": "time",
              "checked": "function () {return this.checked}",
              "name": "function () {return this.name}",
              "value": "function () {return this.value}",
              "placeholder": "function () {return this.placeholder}",
              "maxlength": "function () {return this.maxlength}",
              "enterkeytype": "default",
              "headericon": "function () {return this.headericon}",
              "showcounter": "true"
            }
          },
          {
            "type": "button",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:65",
              "type": "capsule",
              "value": "function () {return this.value}",
              "icon": "function () {return this.icon}"
            }
          },
          {
            "type": "label",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:68",
              "target": "function () {return this.target}"
            }
          },
          {
            "type": "select",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:71"
            },
            "children": [
              {
                "type": "option",
                "attr": {
                  "debugLine": "pages/privateAttr/privateAttr:72",
                  "selected": "function () {return this.selected}",
                  "value": "function () {return this.value}",
                  "icon": "function () {return this.icon}",
                  "action": "show",
                  "focusable": "function () {return this.focusable}",
                  "disabled": "true"
                }
              }
            ]
          },
          {
            "type": "slider",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:76",
              "min": "function () {return this.min}",
              "max": "function () {return this.max}",
              "step": "function () {return this.step}",
              "value": "function () {return this.value}",
              "type": "continuous",
              "minicon": "function () {return this.minicon}",
              "maxicon": "function () {return this.maxicon}"
            }
          },
          {
            "type": "switch",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:79",
              "checked": "function () {return this.checked}",
              "showtext": "function () {return this.showtext}",
              "texton": "function () {return this.texton}",
              "textoff": "function () {return this.textoff}"
            }
          },
          {
            "type": "textarea",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:82",
              "placeholder": "function () {return this.placeholder}",
              "maxlength": "function () {return this.maxlength}",
              "headericon": "function () {return this.headericon}",
              "extend": "function () {return this.extend}",
              "showcounter": "true"
            }
          },
          {
            "type": "picker",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:85",
              "type": "text",
              "range": "function () {return this.range}",
              "selected": "function () {return this.selected}",
              "value": "function () {return this.value}"
            }
          },
          {
            "type": "picker",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:88",
              "type": "date",
              "start": "function () {return this.start}",
              "end": "function () {return this.end}",
              "selected": "function () {return this.selected}",
              "value": "function () {return this.value}",
              "lunar": "function () {return this.lunar}",
              "lunarswitch": "function () {return this.lunarswitch}"
            }
          },
          {
            "type": "picker",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:91",
              "type": "time",
              "containsecond": "function () {return this.containsecond}",
              "selected": "function () {return this.selected}",
              "value": "function () {return this.value}",
              "hours": "function () {return this.hours}"
            }
          },
          {
            "type": "picker",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:94",
              "type": "datetime",
              "selected": "function () {return this.selected}",
              "value": "function () {return this.value}",
              "hours": "function () {return this.hours}",
              "lunar": "function () {return this.lunar}",
              "lunarswitch": "function () {return this.lunarswitch}"
            }
          },
          {
            "type": "picker",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:97",
              "type": "multi-text",
              "columns": "function () {return this.columns}",
              "range": "function () {return this.range}",
              "selected": "function () {return this.selected}",
              "value": "function () {return this.value}"
            }
          },
          {
            "type": "picker-view",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:100",
              "type": "text",
              "range": "function () {return this.range}",
              "selected": "function () {return this.selected}",
              "indicatorprefix": "function () {return this.indicatorprefix}",
              "indicatorsuffix": "function () {return this.indicatorsuffix}"
            }
          },
          {
            "type": "picker-view",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:103",
              "type": "date",
              "start": "function () {return this.start}",
              "end": "function () {return this.end}",
              "selected": "function () {return this.selected}",
              "lunar": "function () {return this.lunar}",
              "lunarswitch": "function () {return this.lunarswitch}"
            }
          },
          {
            "type": "picker-view",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:106",
              "type": "time",
              "containsecond": "function () {return this.containsecond}",
              "selected": "function () {return this.selected}",
              "hours": "function () {return this.hours}"
            }
          },
          {
            "type": "picker-view",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:109",
              "type": "datetime",
              "selected": "function () {return this.selected}",
              "hours": "function () {return this.hours}",
              "lunar": "function () {return this.lunar}",
              "lunarswitch": "function () {return this.lunarswitch}"
            }
          },
          {
            "type": "picker-view",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:112",
              "type": "multi-text",
              "columns": "function () {return this.columns}",
              "range": "function () {return this.range}",
              "selected": "function () {return this.selected}"
            }
          },
          {
            "type": "qrcode",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:115",
              "value": "function () {return this.value}",
              "type": "rect"
            }
          },
          {
            "type": "video",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:118",
              "muted": "function () {return this.muted}",
              "src": "function () {return this.src}",
              "autoplay": "function () {return this.autoplay}",
              "poster": "function () {return this.poster}",
              "controls": "function () {return this.controls}"
            }
          },
          {
            "type": "badge",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:121",
              "placement": "right",
              "count": "2",
              "visible": "true",
              "maxcount": "90"
            }
          },
          {
            "type": "panel",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:124",
              "type": "foldable",
              "mode": "mini",
              "dragbar": "true",
              "miniheight": "300px"
            }
          },
          {
            "type": "stepper",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:127",
              "index": "1"
            }
          },
          {
            "type": "xcomponent",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:130",
              "name": "function () {return this.name}",
              "type": "texture"
            }
          },
          {
            "type": "web",
            "attr": {
              "debugLine": "pages/privateAttr/privateAttr:133",
              "src": "function () {return this.src}"
            }
          }
        ]
    }
  }
}