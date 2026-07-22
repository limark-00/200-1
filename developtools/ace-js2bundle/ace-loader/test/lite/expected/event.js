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

{"render": "function (vm) { var _vm = vm || this; return _c('div', [_c('div', {'onBubbleEvents' : {'click' : _vm.test}} ),_c('div', {'onBubbleEvents' : {'click' : function (evt) {_vm.test(_vm.value,evt)}}} ),_c('div', {'onBubbleEvents' : {'click' : function (evt) {_vm.test(_vm.value,_vm.time,evt)}}} ),_c('input', {'onBubbleEvents' : {'click' : function (evt) {_vm.handleInput('(',evt)}}} ),_c('input', {'onBubbleEvents' : {'click' : function (evt) {_vm.handleInput('（',evt)}}} ),_c('input', {'onBubbleEvents' : {'click' : function (evt) {_vm.handleInput(')',evt)}}} ),_c('input', {'onBubbleEvents' : {'click' : function (evt) {_vm.handleInput('）',evt)}}} ),_c('input', {'onBubbleEvents' : {'click' : function (evt) {_vm.handleInput('kk',_vm.value,'dd',evt)}}} ),_c('input', {'onBubbleEvents' : {'click' : function (evt) {_vm.handleInput(_vm.value,_vm.time,'(',evt)}}} ),_c('input', {'onBubbleEvents' : {'click' : function (evt) {_vm.handleInput('(',_vm.value,_vm.time,evt)}}} )] ) }"}