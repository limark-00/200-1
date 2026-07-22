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

/*
 * Customize the compiled style code into a styleSheet object, styleSheet object is divided into two parts, idSelectors
 * and classSelectors. There are some detailed rules to explain:
 * 1. Remove the "." And "#" symbols in front of the class selector and id selector;
 * 2. Convert all numeric strings to numbers, such as:"32px" convert to number 32; "11" convert to number 11;
 * 3. Convert all hex color to decimal number;
 * 4. Convert all boolean strings to boolean type;
 */
const {
  SPECIAL_STYLE,
  REGEXP_NUMBER_PX,
  REGEXP_COLOR,
  REGEXP_UNIT,
  REGXP_QUOTES,
} = require('./lite-enum');

/**
 * Split style into id Selectors and classSelectors.
 * @param {Obejct} value Preliminary compilation results of css files.
 * @return {String} String result stylesheet.
 */
function transformStyle(value) {
  const style = Function(`return ${value}`)();
  const idSelectors = {};
  const classSelectors = {};
  const styleSheet = {};
  let res = '';
  const KEYFRAMES = '@KEYFRAMES';
  const MEDIA_QUERY = '@MEDIA';
  const keys = Object.keys(style);
  for (const key of keys) {
    if (key.charAt(0) === '.') {
      classSelectors[key.slice(1)] = styleFormat(style[key]);
    } else if (key.charAt(0) === '#') {
      idSelectors[key.slice(1)] = styleFormat(style[key]);
    } else if (key === KEYFRAMES) {
      styleSheet['@keyframes'] = keyFrameFormat(style[key]);
    } else if (key === MEDIA_QUERY) {
      styleSheet['@media'] = mediaQueryFormat(style[key]);
    } else {
      // todo: Label style
    }
  }
  if (style != null && keys.length !== 0) {
    if (Object.keys(idSelectors).length !== 0) {
      styleSheet['idSelectors'] = idSelectors;
    }
    if (Object.keys(classSelectors).length !== 0) {
      styleSheet['classSelectors'] = classSelectors;
    }
  }
  res = JSON.stringify(styleSheet);
  return res;
}
/**
 * keyFrame style special compilation.
 * @param {Obejct} obj Preliminary compilation results of keyFrame style.
 * @return {Obejct} keyFrame style obejct.
 */
function keyFrameFormat(obj) {
  for (const key of Object.keys(obj)) {
    const value = obj[key];
    for (const styleValue of value) {
      for (const styleKey of Object.keys(styleValue)) {
        const innerValue = styleValue[styleKey];
        if (REGEXP_COLOR.test(innerValue)) {
          styleValue[styleKey] = parseInt(innerValue.slice(1), 16);
        }
        try {
          styleValue[styleKey] = JSON.parse(styleValue[styleKey]);
        } catch (e) {
          // Values cannot be converted to objects are not processed
        }
      }
    }
  }
  return obj;
}

/**
 * media query special compilation.
 * @param {Array} mediaQueries the array of media query
 * @return {Array} media query style object
 */
function mediaQueryFormat(mediaQueries) {
  const target = [];
  for (const mediaQuery of mediaQueries) {
    const { condition, ...selectors } = mediaQuery;
    const style = transformStyle(JSON.stringify(selectors));
    if (style) {
      style = JSON.parse(style);
      target.push({ condition, ...style });
    }
  }
  return target;
}

const rules = [
  {
    match: function(key, value) {
      return (
        key === SPECIAL_STYLE.ANIMATION_DELAY ||
        key === SPECIAL_STYLE.ANIMATION_DURATION
      );
    },
    action: function(obj, key, value) {
      obj[key] = value;
    },
  },
  {
    match: function(key, value) {
      return key === SPECIAL_STYLE.ANIMATION_ITERATION_COUNT;
    },
    action: function(obj, key, value) {
      if (value === -1) {
        value = 'infinite';
      }
      obj[key] = value.toString();
    },
  },
  {
    match: function(key, value) {
      return [
        SPECIAL_STYLE.BACKGROUND_IMAGE,
        SPECIAL_STYLE.BACKGROUND_IMAGE_ACTIVE,
        SPECIAL_STYLE.BACKGROUND_IMAGE_CHECKED,
      ].includes(key);
    },
    action: function(obj, key, value) {
      obj[key] = value.replace(REGXP_QUOTES, '');
    },
  },
  {
    match: function(key, value) {
      return !isNaN(Number(value));
    },
    action: function(obj, key, value) {
      obj[key] = Number(value);
    },
  },
  {
    match: function(key, value) {
      return REGEXP_NUMBER_PX.test(value);
    },
    action: function(obj, key, value) {
      obj[key] = parseInt(value.replace(REGEXP_UNIT, ''), 10);
    },
  },
  {
    match: function(key, value) {
      return REGEXP_COLOR.test(value);
    },
    action: function(obj, key, value) {
      obj[key] = parseInt(value.slice(1), 16);
    },
  },
  {
    match: function(key, value) {
      return value === 'true';
    },
    action: function(obj, key, value) {
      obj[key] = true;
    },
  },
  {
    match: function(key, value) {
      return value === 'false';
    },
    action: function(obj, key, value) {
      obj[key] = false;
    },
  },
];

/**
 * Loop and format style, There are two rules defined here, types of number+px and color convert to number 16777215.
 * @param {Obejct} obj Preliminary compilation results of style object.
 * @return {Obejct} style obejct.
 */
function styleFormat(obj) {
  let value = '';
  for (const key of Object.keys(obj)) {
    value = obj[key];
    for (let i = 0; i < rules.length; i++) {
      if (rules[i].match(key, value)) {
        rules[i].action(obj, key, value);
        break;
      }
    }
  }
  return obj;
}

exports.transformStyle = transformStyle;
