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

const Stats = require('webpack/lib/Stats');
const fs = require('fs');
const path = require('path');
const { DEVICE_LEVEL } = require('./lite/lite-enum');

const REG = /\([^\)]+\)/;
let mStats;
let mErrorCount = 0;
let mWarningCount = 0;
let isShowError = true;
let isShowWarning = true;
let isShowNote = true;
let warningCount = 0;
let noteCount = 0;
let errorCount = 0;

class ResultStates {
  constructor(options) {
    this.options = options;
  }

  apply(compiler) {
    const buildPath = this.options.build;
    compiler.hooks.done.tap('Result States', (stats) => {
      mStats = stats;
      warningCount = 0;
      noteCount = 0;
      errorCount = 0;
      if (mStats.compilation.errors) {
        mErrorCount = mStats.compilation.errors.length;
      }
      if (mStats.compilation.warnings) {
        mWarningCount = mStats.compilation.warnings.length;
      }
      if (process.env.error === 'false') {
        isShowError = false;
      }
      if (process.env.warning === 'false') {
        isShowWarning = false;
      }
      if (process.env.note === 'false') {
        isShowNote = false;
      }
      printResult(buildPath);
    });
  }
}

const red = '\u001b[31m';
const yellow = '\u001b[33m';
const blue = '\u001b[34m';
const reset = '\u001b[39m';

const writeError = (buildPath, content) => {
  fs.writeFile(path.resolve(buildPath, 'compile_error.log'), content, (err) => {
    if (err) {
      return console.error(err);
    }
  });
};

function printResult(buildPath) {
  printWarning();
  printError(buildPath);
  if (errorCount + warningCount + noteCount > 0) {
    let result;
    const resultInfo = {};
    if (errorCount > 0) {
      resultInfo.ERROR = errorCount;
      result = 'FAIL ';
    } else {
      result = 'SUCCESS ';
    }
    if (warningCount > 0) {
      resultInfo.WARN = warningCount;
    }

    if (noteCount > 0) {
      resultInfo.NOTE = noteCount;
    }
    console.log(blue, 'COMPILE RESULT:' + result + JSON.stringify(resultInfo), reset);
  } else {
    console.log(blue, 'COMPILE RESULT:SUCCESS ', reset);
  }
}

function printWarning() {
  if (mWarningCount > 0) {
    const warnings = mStats.compilation.warnings;
    const length = warnings.length;
    for (let index = 0; index < length; index++) {
      let message = warnings[index].message
      if (message.match(/noteStart(([\s\S])*)noteEnd/) !== null) {
        noteCount++;
        if (isShowNote) {
          console.info(' ' + message.match(/noteStart(([\s\S])*)noteEnd/)[1].trim(), reset, '\n')
        }
      } else if (message.match(/warnStart(([\s\S])*)warnEnd/) !== null) {
        warningCount++;
        if (isShowWarning) {
          console.warn(yellow, message.match(/warnStart(([\s\S])*)warnEnd/)[1].trim(), reset, '\n')
        }
      }
    }
    if (mWarningCount > length) {
      warningCount = warningCount + mWarningCount - length;
    }
  }
}

function printError(buildPath) {
  if (mErrorCount > 0) {
    const errors = mStats.compilation.errors;
    const length = errors.length;
    if (isShowError) {
      let errorContent = '';
      for (let index = 0; index < length; index++) {
        if (errors[index]) {
          let message = errors[index].message
          if (message) {
            if (message.match(/errorStart(([\s\S])*)errorEnd/) !== null) {
              const errorMessage = message.match(/errorStart(([\s\S])*)errorEnd/)[1];
              console.error(red, errorMessage.trim(), reset, '\n');
            } else {
              const messageArrary = message.split('\n')
              let logContent = ''
              messageArrary.forEach(element => {
                if (!(/^at/.test(element.trim()))) {
                  logContent = logContent + element + '\n'
                }
              });
              console.error(red, logContent, reset, '\n');
            }
            errorCount ++;
            errorContent += message
          }
        }
      }
      writeError(buildPath, errorContent);
    }
  }
}

module.exports = ResultStates;
