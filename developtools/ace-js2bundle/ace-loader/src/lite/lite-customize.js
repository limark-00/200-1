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

const path = require('path');
const fs = require('fs');
const os = require('os');
const isType = require('./lite-utils');
/**
 * Check if the custom file exists.If it does not exist, follow the normal process.
 * If it exists, get the file content.
 */
function checkFilePath() {
  const rulePath = path.resolve(os.userInfo().homedir, '.literc.js');
  if (fs.existsSync(rulePath)) {
    process.env.RULE_PATH = rulePath;
    const customTag = require(rulePath);
    checkContent(customTag);
  }
}
/**
 * Check if the object thrown by the file is correct.
 * @param {Object} customTag User defined custom file content.
 */
function checkContent(customTag) {
  throwError(
      !isType.isObject(customTag),
      `The configuration in the '.literc.js' file is incorrect.(it should be an object.)`,
  );
  throwError(
      isType.isUndefined(customTag.rules),
      `You must write the 'rules' attribute in '.literc.js' file`,
  );
  throwError(
      !isType.isObject(customTag.rules),
      `The value of 'rules' in '.literc.js' file is incorrect.(it should be an object)`,
  );
  if (customTag.extends == 'recommended') {
    validatorCustomTag(customTag.rules);
  }
}

/**
 * Check whether the user-defined rules are correct.
 * @param {Object} rules User defined custom file content.
 */
function validatorCustomTag(rules) {
  const keys = Object.keys(rules);
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    const value = rules[key];
    throwError(
        !isType.isObject(value),
        `The value of '${key}' is incorrect, it should be an object.`,
    );
    const childs = Object.keys(value);
    for (let j = 0; j < childs.length; j++) {
      const child = childs[j];
      throwError(
          child != 'attrs',
          `'${key}' object can only contain 'attrs' attributes`,
      );
    }
  }
}
/**
 * Tool method, if the condition is true, throw an exception.
 * @param {Boolean} condition Analyzing conditions.
 * @param {String} reason Output wrong information.
 */
function throwError(condition, reason) {
  if (condition) {
    throw Error(`\u001b[31mError: ${reason} \u001b[39m`).message;
  }
}
exports.checkFilePath = checkFilePath;
