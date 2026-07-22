/*
 * Copyright (c) 2020 Huawei Device Co., Ltd.
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

"use strict";

const fs = require("fs");
const path = require("path");
const sinon = require("sinon");
const { expect } = require('chai');

function getJsBundle(componentName) {
  const filePath = path.join(
    __dirname,
    "testcase/build/pages",
    `${componentName}`,
    `${componentName}.js`
  );
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const fileString = fileContent.toString();
  return fileString;
}

function getExpectedObj(componentName) {
  const filepath = path.join(__dirname, "expected", `${componentName}.js`);
  const expectedContent = fs.readFileSync(filepath, "utf-8");
  const expectedObj = JSON.parse(expectedContent.toString());
  return expectedObj;
}

function getActualObj(data) {
  const actualString = JSON.stringify(data, function (key, value) {
    if (typeof value === "function") {
      value = value.toString();
    }
    return value;
  });
  const actualObj = JSON.parse(actualString);
  return actualObj;
}

describe("build", () => {
  let viewModelOptions;
  function ViewModel(options) {
    viewModelOptions = options;
  }
  const requireNative = sinon.stub();
  function expectActual(componentName) {
    const actualStr = getJsBundle(componentName);
    const fn = new Function("ViewModel", "requireNative", actualStr);
    fn(ViewModel, requireNative);
    expect(getActualObj(viewModelOptions)).eql(
      getExpectedObj(componentName)
    );
  }
  it("attribute test", () => {
    expectActual("attribute");
  });
  it("class test", () => {
    expectActual("class");
  });
  it("event test", () => {
    expectActual("event");
  });
  it("expression test", () => {
    expectActual("expression");
  });
  it("exteriorStyle test", () => {
    expectActual("exteriorStyle");
  });
  it("for directive", () => {
    expectActual("forDirective");
  });
  it("if directive", () => {
    expectActual("ifDirective");
  });
  it("importJS test", () => {
    expectActual("importJS");
  });
  it("inlineStyle test", () => {
    expectActual("inlineStyle");
  });
  it("bubbleEvent test", () => {
    expectActual("bubble");
  });
  it("globalization performance optimization music test", () => {
    expectActual("music");
  });
  it("globalization performance optimization sick test", () => {
    expectActual("sick");
  });
});
