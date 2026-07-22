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

module.exports = function(argv) {
  return new Promise(function(resolve, reject) {
    const path = require('path');
    const fs = require('fs');
    process.env.aceModuleRoot = path.resolve(__dirname, '../../../sample/lite');
    const webpack = require('webpack');
    const config = require('../../../webpack.lite.config')({}, argv);
    const compiler = webpack(config);
    let flag = false;
    compiler.run((err, stats) => {
      if (err) return void reject(err);
      flag = fs.existsSync(
          path.resolve(__dirname, '../../../sample/lite/build/app.js.map'),
      );
      resolve(flag);
    });
  });
};
