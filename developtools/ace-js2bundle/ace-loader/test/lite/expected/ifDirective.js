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

{"render": "function (vm) { var _vm = vm || this; return _c('div', [_i((function () {return _vm.conditionVar===1}),function(){return _c('text', {'attrs' : {'value' : function () {return _vm.componentData.if}}} )}),_c('div', {'staticClass' : [\"item-content\"]} , [_i((function () {return _vm.conditionVar===1}),function(){return _c('text', {'attrs' : {'value' : function () {return _vm.componentData.if}}} )}),_i((function () {return _vm.conditionVar===2&&!(_vm.conditionVar===1)}),function(){return _c('text', {'attrs' : {'value' : function () {return _vm.componentData.elif}}} )}),_i((function () {return !(_vm.conditionVar===2)&&!(_vm.conditionVar===1)}),function(){return _c('text', {'attrs' : {'value' : function () {return _vm.componentData.else}}} )})] ),_i((function () {return _vm.showTest}),function(){return _c('div', [_l((function () {return _vm.list}),function($item,$idx){return _c('div', [_c('text', {'attrs' : {'value' : function () {return ($idx) + decodeURI('.') + ($item.name)}}} )] )})] )}),_l((function () {return _vm.list}),function($item,$idx){return _c('div', [_i((function () {return _vm.showTest}),function(){return _c('div', [_c('text', {'attrs' : {'value' : function () {return ($idx) + decodeURI('.') + ($item.name)}}} )] )})] )}),_l((function () {return _vm.list}),function(personItem,personIndex){return _c('div', [_i((function () {return personIndex==1}),function(){return _c('div', [_c('text', {'attrs' : {'value' : function () {return personItem.name}}} )] )})] )})] ) }"}