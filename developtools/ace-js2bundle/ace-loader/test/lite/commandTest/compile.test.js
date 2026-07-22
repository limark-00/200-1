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

const assert = require('chai').assert;
const fn = require('./compile');
const argv = require('yargs').argv;
const argvSelect = {
  key1: {},
  key2: { buildMode: 'release' },
  key3: { buildMode: 'debug' },
  key4: { buildMode: 'develope' },
};
const compileResult = {
  key1: true,
  key2: false,
  key3: true,
  key4: true,
};
/**
 * Test whether the existence of the sourcemap file is reasonable when different 'buildMode' is passed in.
 * Only when the 'buildMode' is 'release', the sourcemap does not exist, otherwise it exists
 */
describe('Compilation result test', () => {
  it('sourcemap', (done) => {
    const key = argv.buildMode ? argv.buildMode : 'key1';
    fn(argvSelect[key])
        .then((flag) => {
          assert.equal(flag, compileResult[key], 'result pass');
          done();
        })
        .catch(done);
  });
});
