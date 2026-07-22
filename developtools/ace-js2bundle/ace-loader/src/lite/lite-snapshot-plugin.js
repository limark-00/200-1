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

const _require = require('child_process');
const exec = _require.exec;
const _path = require('path');
const snapshot = _path.join(__dirname, '..', '..', 'bin', 'jerry-snapshot');
const registerRequireContextHook = require('babel-plugin-require-context-hook/register');
registerRequireContextHook();
/**
 * Convert Javascript file to snapshot.
 */
class SnapshotPlugin {
  /**
   * constructor of the SnapshotPlugin class.
   * @param {String} options The object of build folder.
   */
  constructor(options) {
    this.options = options;
  }
  /**
   * Find all javacript file paths in the directory.
   * @param {Object} assets the object of javacript file path.
   * @param {String} buildPath The path of build folder.
   * @return {Array} Image path array.
   */
  getDir(assets, buildPath) {
    const pathArray = [];
    Object.keys(assets).map((item) => {
      if (/.js$/.test(item)) {
        pathArray.push(_path.join(buildPath, item));
      }
    });
    return pathArray;
  };
  /**
   * Convert javacript file asynchronously. If an error occurs, print an error message.
   * @param {Object} compiler API specification, all configuration information of Webpack environment.
   */
  apply(compiler) {
    const buildPath = this.options.build;
    compiler.hooks.done.tap('snapshot coverter', (stats) => {
      const pathArray = this.getDir(stats.compilation.assets, buildPath);
      pathArray.forEach((element) => {
        const bcPath = element.replace('.js', '.bc');
        const fileName = _path.basename(element);
        exec(`"${snapshot}" generate -o "${bcPath}" "${element}"`, (error) => {
          if (error) {
            console.error('\u001b[31m', `Failed to convert the ${fileName} file to a snapshot.`, '\u001b[39m');
          }
        });
      });
    });
  }
}
module.exports = SnapshotPlugin;
