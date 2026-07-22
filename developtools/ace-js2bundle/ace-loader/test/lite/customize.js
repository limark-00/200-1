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

// Enhance_Compiler_Test_008
module.exports = [];

// Enhance_Compiler_Test_009
module.exports = { rules: 123 };

// Enhance_Compiler_Test_010
module.exports = {
  extends: 'recommended',
  rules: {
    hello: 'String',
  },
};

// Enhance_Compiler_Test_011
module.exports = {
  extends: 'recommended',
  rules: {
    div: {
      name: 'jack',
    },
  },
};

// Enhance_Compiler_Test_012
module.exports = {
  rules: {
    hello: {},
  },
};

// Enhance_Compiler_Test_013
module.exports = {
  extends: 'recommended',
  rules: {
    example: {},
  },
};

// Enhance_Compiler_Test_014
module.exports = {
  extends: 'recommended',
  rules: {
    swiper: {
      attrs: {
        vertical: {
          enum: ['change'],
        },
      },
    },
  },
};

// Enhance_Compiler_Test_015
module.exports = {
  extends: 'recommended',
  rules: {
    swiper: {
      attrs: {
        display: {},
      },
    },
  },
};
