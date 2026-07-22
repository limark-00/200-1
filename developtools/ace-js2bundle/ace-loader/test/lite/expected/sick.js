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
  "change": "function change() {\n    _system[\"default\"].replace({\n      uri: 'pages/music/music'\n    });\n  }",
  "data": {
    "dizzinessColor": "#F5B041",
    "marginLeft": "77px"
  },
  "render": "function (vm) { var _vm = vm || this; var i18ns = []; i18ns.push( _vm.$t('strings.choose_body_state') );i18ns.push( _vm.$t('css.measureHome_hand_top') );i18ns.push( _vm.$t('strings.chest_tightness') );i18ns.push( _vm.$t('css.judgeIos_height') );i18ns.push( _vm.$t('strings.dizziness') );i18ns.push( (i18ns[4]) + decodeURI('%20:%E5%A4%B4%E7%97%9B') );i18ns.push( (i18ns[2]) + decodeURI('%20+%20') + (i18ns[4]) ); return _c('list', {'attrs' : {'ref' : \"list\"},'staticClass' : [\"container\"],'onBubbleEvents' : {'swipe' : _vm.touchMove}} , [_c('list-item', {'staticClass' : [\"head_t\"]} , [_c('text', {'attrs' : {'value' : i18ns[0]},'staticClass' : [\"head_t_b\"],'staticStyle' : {'marginTop' : i18ns[1],'color' : 16711680}, 'dynamicStyle' :{'marginLeft' : function () {return _vm.marginLeft}}} )] ),_c('list-item', {'staticClass' : [\"list\"]} , [_c('text', {'attrs' : {'value' : i18ns[2]},'staticClass' : [\"listL\"],'staticStyle' : {'width' : i18ns[3]}, } )] ),_c('list-item', {'staticClass' : [\"list\"]} , [_c('text', {'attrs' : {'value' : i18ns[4]},'staticClass' : [\"listL\"],'staticStyle' : {'width' : i18ns[3]}, 'dynamicStyle' :{'color' : function () {return _vm.dizzinessColor}}} )] ),_c('list-item', {'staticClass' : [\"list\"]} , [_c('text', {'attrs' : {'value' : i18ns[5]},'staticClass' : [\"listL\"],'staticStyle' : {'width' : i18ns[3]}, } )] ),_c('list-item', {'staticClass' : [\"list\"]} , [_c('text', {'attrs' : {'value' : i18ns[6]},'staticClass' : [\"listL\"],'staticStyle' : {'width' : i18ns[3]}, } )] ),_c('list-item', {'staticClass' : [\"buttonContainerStyle\"]} , [_c('input', {'attrs' : {'type' : \"button\",'value' : \"下一页\"},'staticClass' : [\"buttonStyle\"],'onBubbleEvents' : {'click' : _vm.change}} )] )] ) }",
  "styleSheet": {
    "classSelectors": {
      "buttonContainerStyle": {
        "height": 80,
        "width": 454
      },
      "buttonStyle": {
        "height": 60,
        "marginLeft": 130,
        "width": 200
      },
      "container": {
        "height": 454,
        "width": 454
      },
      "head_t": {
        "flexDirection": "column",
        "height": 100,
        "width": 454
      },
      "head_t_b": {
        "textAlign": "center",
        "width": 300
      },
      "list": {
        "height": 112,
        "justifyContent": "center",
        "width": 454
      },
      "listL": {
        "fontSize": 38,
        "marginTop": 28,
        "textAlign": "center"
      }
    }
  }
}