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

function getActualJSON(componentName, filaName) {
  const filePath = path.join(__dirname,"testcase/build/pages",`${componentName}`, filaName + `.json`);
  if(!fs.existsSync(filePath)){
    return {}
  }
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const fileString = fileContent.toString();
  return JSON.parse(fileString);
}

function getExpectJSON(componentName, filaName) {
  const filePath = path.join(__dirname, "expected", `${componentName}`, filaName + `.json`);
  if(!fs.existsSync(filePath)){
    return {}
  }
  const expectedContent = fs.readFileSync(filePath, "utf-8");
  const expectedObj = JSON.parse(expectedContent.toString());
  return expectedObj;
}

describe('build', () => {
  it('commonAttr', () => {
    const page = 'commonAttr'
    expect(getActualJSON(page, 'commonAttr')).eql(getExpectJSON(page, 'commonAttr'));
  });
  it('event', () => {
    const page = 'event'
    expect(getActualJSON(page, 'event')).eql(getExpectJSON(page, 'event'));
  });
  it('expression', () => {
    const page = 'expression'
    expect(getActualJSON(page, 'expression')).eql(getExpectJSON(page, 'expression'));
  });
  it('exteriorStyle', () => {
    const page = 'exteriorStyle'
    expect(getActualJSON(page, 'exteriorStyl')).eql(getExpectJSON(page, 'exteriorStyl'));
  });
  it('ifAttr', () => {
    const page = 'ifAttr'
    expect(getActualJSON(page, 'ifAttr')).eql(getExpectJSON(page, 'ifAttr'));
  });
  it('importCSS', () => {
    const page = 'importCSS'
    expect(getActualJSON(page, 'importCSS')).eql(getExpectJSON(page, 'importCSS'));
  });
  it('importLess', () => {
    const page = 'importLess'
    expect(getActualJSON(page, 'importLess')).eql(getExpectJSON(page, 'importLess'));
  });
  it('inlineStyle', () => {
    const page = 'inlineStyle'
    expect(getActualJSON(page, 'inlineStyle')).eql(getExpectJSON(page, 'inlineStyle'));
  });
  it('mediaQuery', () => {
    const page = 'mediaQuery'
    expect(getActualJSON(page, 'mediaQuer')).eql(getExpectJSON(page, 'mediaQuer'));
  });
  it('privateAttr', () => {
    const page = 'privateAttr'
    expect(getActualJSON(page, 'privateAttr')).eql(getExpectJSON(page, 'privateAttr'));
  });
  it('showAttr', () => {
    const page = 'showAttr'
    expect(getActualJSON(page, 'showAttr')).eql(getExpectJSON(page, 'showAttr'));
  });
  it('withJS', () => {
    const page = 'withJS'
    expect(getActualJSON(page, 'withJS')).eql(getExpectJSON(page, 'withJS'));
  })
});