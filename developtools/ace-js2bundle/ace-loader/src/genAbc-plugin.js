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

const fs = require('fs')
const path = require('path')
const process = require('child_process')

const arkDir = path.join(__dirname, '..', 'bin', 'ark');
const forward = '(global.___mainEntry___ = function (globalObjects) {' + '\n' +
              '  var define = globalObjects.define;' + '\n' +
              '  var require = globalObjects.require;' + '\n' +
              '  var bootstrap = globalObjects.bootstrap;' + '\n' +
              '  var register = globalObjects.register;' + '\n' +
              '  var render = globalObjects.render;' + '\n' +
              '  var $app_define$ = globalObjects.$app_define$;' + '\n' +
              '  var $app_bootstrap$ = globalObjects.$app_bootstrap$;' + '\n' +
              '  var $app_require$ = globalObjects.$app_require$;' + '\n' +
              '  var history = globalObjects.history;' + '\n' +
              '  var Image = globalObjects.Image;' + '\n' +
              '  var OffscreenCanvas = globalObjects.OffscreenCanvas;' + '\n' +
              '  (function(global) {' + '\n' +
              '    "use strict";' + '\n'
const last = '\n' + '})(this.__appProto__);' + '\n' + '})'
const firstFileEXT = '_.js'
let output
let webpackPath
let isWin = false
let isMac = false
let isDebug = false

class GenAbcPlugin {
  constructor(output_, webpackPath_, isDebug_) {
    output = output_
    webpackPath = webpackPath_
    isDebug = isDebug_
  }
  apply(compiler) {
    if (fs.existsSync(path.resolve(webpackPath, 'ark/build-win'))) {
      isWin = true
    } else {
      if (fs.existsSync(path.resolve(webpackPath, 'ark/build-mac'))) {
        isMac = true
      } else  {
        if (!fs.existsSync(path.resolve(webpackPath, 'ark/build'))) {
          console.error('\u001b[31m', `find build fail`, '\u001b[39m')
          return
        }
      }
    }

    compiler.hooks.emit.tap('GenAbcPlugin', (compilation) => {
      const assets = compilation.assets
      const keys = Object.keys(assets)
      keys.forEach(key => {
        // choice *.js
        if (output && webpackPath && path.extname(key) === '.js') {
          let newContent = assets[key].source()
          if (key.search('./workers/') !== 0) {
            newContent = forward + newContent + last
          }
          const keyPath = key.replace(/\.js$/, firstFileEXT)
          writeFileSync(newContent, path.resolve(output, keyPath), key)
        }
      })
    })
  }
}

function writeFileSync(inputString, output, jsBundleFile) {
  const parent = path.join(output, '..')
  if (!(fs.existsSync(parent) && fs.statSync(parent).isDirectory())) {
    mkDir(parent)
  }
  fs.writeFileSync(output, inputString)
  if (fs.existsSync(output)) {
    js2abcFirst(output)
  } else {
    console.error('\u001b[31m', `Failed to convert file ${jsBundleFile} to bin. ${output} is lost`, '\u001b[39m')
  }
}

function mkDir(path_) {
  const parent = path.join(path_, '..')
  if (!(fs.existsSync(parent) && !fs.statSync(parent).isFile())) {
    mkDir(parent)
  }
  fs.mkdirSync(path_)
}

function js2abcFirst(inputPath) {
  let param = '-r'
  if (isDebug) {
    param += ' --debug'
  }

  let js2abc = path.join(arkDir, 'build', 'src', 'index.js');
  if (isWin) {
    js2abc = path.join(arkDir, 'build-win', 'src', 'index.js');
  } else if (isMac){
    js2abc = path.join(arkDir, 'build-mac', 'src', 'index.js');
  }

  const cmd = `node --expose-gc "${js2abc}" "${inputPath}" ${param}`;
  try {
    process.execSync(cmd)
    console.info(cmd)
  } catch (e) {
    console.error('\u001b[31m', `Failed to convert file ${inputPath} to abc`, '\u001b[39m')
  }
  if (fs.existsSync(inputPath)) {
    fs.unlinkSync(inputPath)
  } else {
    console.error('\u001b[31m', `Failed to convert file ${inputPath} to abc. ${inputPath} is lost`, '\u001b[39m')
  }
  let abcFile = inputPath.replace(/\.js$/, '.abc');
  if (fs.existsSync(abcFile)) {
    let abcFileNew = abcFile.replace(/\_.abc$/, '.abc');
    fs.renameSync(abcFile, abcFileNew)
  } else {
    console.error('\u001b[31m', `${abcFile} is lost`, '\u001b[39m')
  }
}

module.exports = GenAbcPlugin
