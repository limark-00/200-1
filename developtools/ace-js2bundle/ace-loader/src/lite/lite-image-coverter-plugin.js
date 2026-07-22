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

const _path = require('path');
const fs = require('fs');
const registerRequireContextHook = require('babel-plugin-require-context-hook/register');
const { REGEXP_PNG } = require('./lite-enum');
const iconPath = process.env.iconPath || '';
const img2bin = require('./lite-image2bin');

registerRequireContextHook();
/**
 * Convert picture to bin format.
 */
class ImageCoverterPlugin {
  /**
   * constructor of the ImageCoverterPlugin class.
   * @param {String} options The object of build folder.
   */
  constructor(options) {
    this.options = options;
  }
  /**
   * Find all image paths in png、jpg、bmp、jpeg format in the directory.
   * @param {String} buildPath The path of build folder.
   * @return {Array} Image path array.
   */
  getDir(buildPath) {
    const pngPath = global.__requireContext('', buildPath, true, REGEXP_PNG);
    const pathArray = pngPath.keys().map((element) => {
      return _path.join(buildPath, element);
    });
    return pathArray;
  }
  /**
   * Convert image format asynchronously, return code 0 successfully, otherwise return 1.
   * @param {Object} compiler API specification, all configuration information of Webpack environment.
   */
  apply(compiler) {
    const buildPath = this.options.build;
    const getDir = this.getDir;
    compiler.hooks.done.tap('image coverter', function(compilation, callback) {
      const pathArray = getDir(buildPath);
      const writeResult = (content) => {
        fs.writeFile(_path.resolve(buildPath, 'image_convert_result.txt'), content, (err) => {
          if (err) {
            return console.error(err);
          }
        });
      };
      const totalImageCount = pathArray.length;
      if (totalImageCount > 0) {
        const promiseArray = pathArray.map((path) => {
          return img2bin(path);
        });
        Promise.all(promiseArray).then(() => {
          writeResult('{exitCode:0}');
        }).catch(() => {
          writeResult('{exitCode:1}');
        });
      } else {
        writeResult('{exitCode:0}');
      }
      if (iconPath !== '') {
        const iconArray = getDir(iconPath);
        iconArray.forEach((path) => {
          img2bin(path);
        });
      }
    });
  }
}
module.exports = ImageCoverterPlugin;
