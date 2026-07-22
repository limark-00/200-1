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
  "data": {
    "musics": [
      {
        "name": "Song1",
        "singer": "player1"
      },
      {
        "name": "Song2",
        "singer": "player2"
      },
      {
        "name": "Song3",
        "singer": "player3"
      },
      {
        "name": "Song4",
        "singer": "player4"
      },
      {
        "name": "Song5",
        "singer": "player5"
      },
      {
        "name": "Song6",
        "singer": "player6"
      },
      {
        "name": "Song7",
        "singer": "player7"
      },
      {
        "name": "Song8",
        "singer": "player8"
      }
    ]
  },
  "render": "function (vm) { var _vm = vm || this; var i18ns = []; i18ns.push( _vm.$t('strings.dizziness') ); return _c('div', {'staticClass' : [\"wrapper\"]} , [_l((function () {return _vm.musics}),function(value,$idx){return _c('div', {'staticClass' : [\"music-list-item\"]} , [_c('div', {'staticStyle' : {'height' : 400,'width' : 454,'flexDirection' : \"column\"}, } , [_c('text', {'attrs' : {'value' : function () {return _vm.$t('value.name')}},'staticClass' : [\"content\"]} ),_c('text', {'attrs' : {'value' : function () {return value.name}},'staticClass' : [\"content\"]} ),_c('text', {'attrs' : {'value' : i18ns[0]},'staticClass' : [\"content\"]} ),_c('text', {'attrs' : {'value' : function () {return value.singer}},'staticClass' : [\"content\"]} )] )] )})] ) }",
  "styleSheet": {
    "classSelectors": {
      "content": {
        "fontSize": 30,
        "height": 50,
        "textAlign": "center",
        "width": 454
      },
      "music-list-item": {
        "height": 300,
        "width": 454
      },
      "wrapper": {
        "flexDirection": "column",
        "height": 3000,
        "width": 454
      }
    }
  }
}