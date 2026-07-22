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

const fs = require('fs');
const path = require('path');
const SingleEntryPlugin = require('webpack/lib/SingleEntryPlugin');

const CUSTOM_THEME_PROP_GROUPS = require('./theme/customThemeStyles');
const OHOS_THEME_PROP_GROUPS = require('./theme/ohosStyles');

const FILE_EXT_NAME = ['.js', '.css', '.jsx', '.less', '.sass', '.scss', '.md', '.DS_Store', '.hml'];
const red = '\u001b[31m';
const reset = '\u001b[39m';
let input = '';
let output = '';
let manifestFilePath = '';
let shareThemePath = '';
let internalThemePath = '';

function copyFile(input, output) {
  try {
    if (fs.existsSync(input)) {
      const parent = path.join(output, '..');
      if (!(fs.existsSync(parent) && fs.statSync(parent).isDirectory())) {
        mkDir(parent);
      }
      const pathInfo = path.parse(input);
      const entryObj = addPageEntryObj();
      const indexPath = pathInfo.dir + path.sep + pathInfo.name + '.hml?entry';
      for (const key in entryObj) {
        if (entryObj[key] === indexPath) {
          return;
        }
      }
      if (pathInfo.ext === '.json' && (pathInfo.dir === shareThemePath ||
        pathInfo.dir === internalThemePath)) {
        if (themeFileBuild(input, output)) {
          return;
        }
      }
      const readStream = fs.createReadStream(input);
      const writeStream = fs.createWriteStream(output);
      readStream.pipe(writeStream);
      readStream.on('close', function() {
        writeStream.end();
      });
    }
  } catch (e) {
    console.error(red, `Failed to build file ${input}.`, reset);
    throw e.message;
  }
}

function mkDir(path_) {
  const parent = path.join(path_, '..');
  if (!(fs.existsSync(parent) && !fs.statSync(parent).isFile())) {
    mkDir(parent);
  }
  fs.mkdirSync(path_);
}

function circularFile(inputPath, outputPath, ext) {
  const realPath = path.join(inputPath, ext);
  const localI18n = path.join(input, 'i18n');
  if (!fs.existsSync(realPath) || realPath === output || realPath === localI18n) {
    return;
  }
  fs.readdirSync(realPath).forEach(function(file_) {
    const file = path.join(realPath, file_);
    const fileStat = fs.statSync(file);
    if (fileStat.isFile()) {
      const baseName = path.basename(file);
      const extName = path.extname(file);
      if (FILE_EXT_NAME.indexOf(extName) < 0 && baseName !== '.DS_Store') {
        const outputFile = path.join(outputPath, ext, path.basename(file_));
        if (outputFile === path.join(output, 'manifest.json')) {
          return;
        }
        if (fs.existsSync(outputFile)) {
          const outputFileStat = fs.statSync(outputFile);
          if (outputFileStat.isFile() && fileStat.size !== outputFileStat.size) {
            copyFile(file, outputFile);
          }
        } else {
          copyFile(file, outputFile);
        }
      }
    } else if (fileStat.isDirectory()) {
      circularFile(inputPath, outputPath, path.join(ext, file_));
    }
  });
}

class ResourcePlugin {
  constructor(input_, output_, manifestFilePath_) {
    input = input_;
    output = output_;
    manifestFilePath = manifestFilePath_;
    shareThemePath = path.join(input_, '../share/resources/styles');
    internalThemePath = path.join(input_, 'resources/styles');
  }
  apply(compiler) {
    compiler.hooks.beforeCompile.tap('resource Copy', () => {
      circularFile(input, output, '');
      circularFile(input, output, '../share');
    });
    compiler.hooks.normalModuleFactory.tap('OtherEntryOptionPlugin', () => {
      if (process.env.DEVICE_LEVEL === 'card') {
        return;
      }
      addPageEntryObj();
      for (const key in entryObj) {
        if (!compiler.options.entry[key]) {
          const singleEntry = new SingleEntryPlugin('', entryObj[key], key);
          singleEntry.apply(compiler);
        }
      }
    });
    compiler.hooks.done.tap('copyManifest', () => {
      copyManifest();
      if (fs.existsSync(path.join(output, 'app.js'))) {
        fs.utimesSync(path.join(output, 'app.js'), new Date(), new Date());
      }
    });
  }
}

function copyManifest() {
  copyFile(manifestFilePath, path.join(output, 'manifest.json'));
}

let entryObj = {};

function addPageEntryObj() {
  entryObj = {};
  if (process.env.abilityType === 'page') {
    if (!fs.existsSync(manifestFilePath)) {
      throw Error('ERROR: missing manifest').message;
    }
    const jsonString = fs.readFileSync(manifestFilePath).toString();
    const obj = JSON.parse(jsonString);
    const pages = obj.pages;
    if (pages === undefined) {
      throw Error('ERROR: missing pages').message;
    }
    pages.forEach((element) => {
      const sourcePath = element;
      const hmlPath = path.join(input, sourcePath + '.hml');
      const aceSuperVisualPath = process.env.aceSuperVisualPath || '';
      const visualPath = path.join(aceSuperVisualPath, sourcePath + '.visual');
      const isHml = fs.existsSync(hmlPath);
      const isVisual = fs.existsSync(visualPath);
      if (isHml && isVisual) {
        logWarn(this, [{
          reason: 'ERROR: ' + sourcePath + ' cannot both have hml && visual',
        }]);
      } else if (isHml) {
        entryObj['./' + element] = hmlPath + '?entry';
      } else if (isVisual) {
        entryObj['./' + element] = visualPath + '?entry';
      }
    });
  }
  if (process.env.isPreview !== 'true' && process.env.DEVICE_LEVEL === 'rich') {
    loadWorker(entryObj);
  }
  return entryObj;
}

function loadWorker(entryObj) {
  const workerPath = path.resolve(input, 'workers');
  if (fs.existsSync(workerPath)) {
    const workerFiles = [];
    readFile(workerPath, workerFiles);
    workerFiles.forEach((item) => {
      if (/\.js$/.test(item)) {
        const relativePath = path.relative(workerPath, item).replace(/\.js$/, '');
        entryObj[`./workers/` + relativePath] = item;
      }
    });
  }
}

function readFile(dir, utFiles) {
  try {
    const files = fs.readdirSync(dir);
    files.forEach((element) => {
      const filePath = path.join(dir, element);
      const status = fs.statSync(filePath);
      if (status.isDirectory()) {
        readFile(filePath, utFiles);
      } else {
        utFiles.push(filePath);
      }
    });
  } catch (e) {
    console.error(e.message);
  }
}

function themeFileBuild(customThemePath, customThemeBuild) {
  if (fs.existsSync(customThemePath)) {
    const themeContent = JSON.parse(fs.readFileSync(customThemePath));
    const newContent = {};
    if (themeContent && themeContent['style']) {
      newContent['style'] = {};
      const styleContent = themeContent['style'];
      Object.keys(styleContent).forEach(function(key) {
        const customKey = CUSTOM_THEME_PROP_GROUPS[key];
        const ohosKey = OHOS_THEME_PROP_GROUPS[key];
        if (ohosKey) {
          newContent['style'][ohosKey] = styleContent[key];
        } else if (customKey) {
          newContent['style'][customKey] = styleContent[key];
        } else {
          newContent['style'][key] = styleContent[key];
        }
      });
      fs.writeFileSync(customThemeBuild, JSON.stringify(newContent, null, 2));
      return true;
    }
  }
  return false;
}

module.exports = ResourcePlugin;
