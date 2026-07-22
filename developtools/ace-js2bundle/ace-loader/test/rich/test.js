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

'use strict';

const fs = require('fs');
const path =require('path');

const chai = require('chai');
const sinon = require('sinon');
const sinonChai = require('sinon-chai');
const expect = chai.expect;
chai.use(sinonChai);

function getActualString(componentName) {
  const filePath = path.join(__dirname, 'testcase/build/pages', `${componentName}`, `${componentName}.js`);
  const fileContent = fs.readFileSync(filePath, 'utf-8');
  const fileString = fileContent.toString();
  return fileString;
}

function getExpectJSON(componentName) {
  const filepath = path.join(__dirname, 'expected', `${componentName}.js`);
  const expectedContent = fs.readFileSync(filepath, 'utf-8');
  const expectedObj = JSON.parse(expectedContent.toString());
  return expectedObj;
}

function stringifyActual(json) {
  return JSON.stringify(json, function(key, value) {
    if (typeof value === 'function') {
      value = value.toString();
    }
    return value;
  }, ' ');
}

describe('build', () => {
  let $app_define$;
  let $app_bootstrap$;
  let components;
  let requireStub;
  let bootstrapStub;

  function expectActual(name) {
    const actualStr = getActualString(name);
    const fn = new Function('$app_define$', '$app_bootstrap$', actualStr);
    fn($app_define$, $app_bootstrap$);
    const expectJSON = getExpectJSON(name);
    expect(JSON.parse(stringifyActual(components))).eql(expectJSON);
    expect(components).to.include.keys($app_bootstrap$.firstCall.args[0]);
    return actualStr;
  }

  beforeEach(() => {
    components = {};
    requireStub = sinon.stub();
    bootstrapStub = sinon.stub();

    $app_define$ = function(componentName, deps, factory) {
      if (components[componentName]) {
        throw new Error(`${componentName} is defined repeatly`);
      }

      let $app_require$ = requireStub;
      let $app_exports$ = {};
      let $app_module$ = {exports : $app_exports$};

      factory($app_require$, $app_exports$, $app_module$);
      components[componentName] = $app_module$.exports;
    }

    $app_bootstrap$ = bootstrapStub;
  });

  it('class', () => {
    expectActual('class');
  });
  it('event', () => {
    expectActual('event');
  });
  it('expression', () => {
    expectActual('expression');
  });
  it('commonAttr', () => {
    expectActual('commonAttr');
  });
  it('uncommonAttr', () => {
    expectActual('uncommonAttr');
  });
  it('privateAttr', () => {
    expectActual('privateAttr');
  });
  it('forDirective', () => {
    expectActual('forDirective');
  });
  it('ifDirective', () => {
    expectActual('ifDirective');
  });
  it('importJS', () => {
    expectActual('importJS');
  });
  it('inlineStyle', () => {
    expectActual('inlineStyle');
  });
  it('exteriorStyle', () => {
    expectActual('exteriorStyle');
  });
  it('importCSS', () => {
    expectActual('importCSS');
  });
  it('mediaQuery', () => {
    expectActual('mediaQuery');
  });
});