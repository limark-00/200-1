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
const isType = require('../lite/lite-utils');
const rulePath = process.env.RULE_PATH;
const smartvisionTag = {
  camera: {
    events: ['error'],
  },
  video: {
    events: [
      'prepared',
      'start',
      'pause',
      'finish',
      'error',
      'seeking',
      'seeked',
      'timeupdate',
    ],
    attrs: {
      autoplay: {
        enum: ['false', 'true'],
      },
      controls: {
        enum: ['true', 'false'],
      },
      muted: {
        enum: ['false', 'true'],
      },
      src: { checkPath: true },
    },
  },
};

const litewearableTag = {
  'div': {},
  'canvas': {},
  'stack': {},
  'qrcode': {
    atomic: true,
    selfClosing: true,
    uevents: ['click', 'longpress', 'swipe'],
    attrs: {
      value: {
        required: true,
      },
      type: {
        enum: ['rect', 'circle'],
      },
    },
  },
  'list': {
    events: ['scrollend'],
    children: ['list-item'],
  },
  'list-item': {
    excludeRoot: true,
    parents: ['list'],
  },
  'swiper': {
    unSupportedChildren: ['list'],
    events: ['change'],
    attrs: {
      index: {
        checkFunc: 'number',
      },
      loop: {
        enum: ['true', 'false'],
      },
      duration: {
        checkFunc: 'number',
      },
      vertical: {
        enum: ['false', 'true'],
      },
    },
  },
  'tabs': {
    events: ['change'],
    children: ['tab-content', 'tab-bar'],
  },
  'tab-bar': {
    parents: ['tabs'],
    children: ['text'],
    attrs: {
      mode: {
        enum: ['fixed'],
      },
    },
  },
  'tab-content': {
    parents: ['tabs'],
    children: ['div', 'stack'], // to be checked
  },
  'image-animator': {
    atomic: true,
    selfClosing: true,
    events: ['stop'],
    attrs: {
      images: {
        required: true,
      },
      iteration: {},
      reverse: {
        enum: ['false', 'true'],
      },
      fixedsize: {
        enum: ['true', 'false'],
      },
      duration: {
        required: true,
      },
      fillmode: {
        enum: ['none', 'forwards'],
      },
    },
  },
  'image': {
    alias: ['img'],
    atomic: true,
    selfClosing: true,
    attrs: {
      src: {
        checkPath: true,
      },
    },
  },
  'progress': {
    atomic: true,
    selfClosing: true,
    attrs: {
      type: {
        enum: ['horizontal', 'arc'],
      },
      percent: {
        checkFunc: 'number',
      },
    },
  },
  'text': {
    atomic: true,
    textContent: true,
    attrs: {
      type: {
        enum: ['text', 'html'],
      },
      value: {},
    },
  },
  'marquee': {
    atomic: true,
    attrs: {
      scrollamount: {
        def: 6,
        checkFunc: 'number',
      },
    },
  },
  'analog-clock': {
    attrs: {
      hour: {
        checkFunc: 'number',
      },
      min: {
        checkFunc: 'number',
      },
      sec: {
        checkFunc: 'number',
      },
    },
  },
  'clock-hand': {
    parents: ['analog-clock'],
    attrs: {
      type: {
        enum: ['hour', 'min', 'sec'],
      },
      src: {
        checkPath: true,
      },
    },
  },
  'calendar': {
    atomic: true,
    selfClosing: true,
    events: ['selectedchange', 'goto', 'requestdata'],
    uevents: [],
    attrs: {
      date: {
        checkFunc: 'date',
      },
      dateadapter: {},
      holidays: {},
      cardcalendar: {
        def: 'true',
        enum: ['true', 'false'],
      },
      type : {
        def: 'normal',
        enum: ['normal', 'simple'],
      },
      calendardata: {},
      holidays: {},
      offdays: {},
      showholiday: {},
      showlunar: {},
      startdayofweek: {},
      direction: {
        def: 'horizontal',
        enum: ['vertical', 'horizontal'],
      },
      workdays: {},
    },
  },
  'chart': {
    atomic: true,
    selfClosing: true,
    attrs: {
      type: {
        enum: ['line', 'bar'],
      },
      datasets: {},
      options: {},
    },
  },
  'input': {
    atomic: true,
    selfClosing: true,
    events: ['change'],
    attrs: {
      checked: {
        enum: ['false', 'true'],
      },
      type: {
        enum: ['button', 'checkbox', 'radio'],
      },
      name: {},
      value: {},
    },
  },
  'slider': {
    atomic: true,
    selfClosing: true,
    events: ['change'],
    attrs: {
      min: {
        def: 0,
        checkFunc: 'number',
      },
      max: {
        def: 100,
        checkFunc: 'number',
      },
      value: {
        def: 0,
        checkFunc: 'number',
      },
    },
  },
  'switch': {
    events: ['change'],
    atomic: true,
    selfClosing: true,
    attrs: {
      checked: {
        enum: ['false', 'true'],
      },
    },
  },
  'picker-view': {
    atomic: true,
    selfClosing: true,
    uevents: ['change'],
    attrs: {
      type: {
        enum: ['text', 'time'],
      },
      range: {},
      selected: {},
    },
  },
};

const liteCommonTag = {
  events: [
    'click',
    'longpress',
    'touchstart',
    'touchmove',
    'touchcancel',
    'touchend',
    'key',
    'swipe',
  ],
  attrs: {
    id: {},
    style: {},
    class: {},
    ref: {},
    if: {
      excludeRoot: true,
      def: 'true',
    },
    elif: {
      def: 'true',
    },
    else: {
      excludeRoot: true,
    },
    for: {
      excludeRoot: true,
    },
    tid: {},
    show: {
      excludeRoot: true,
      def: 'true',
    },
  },
};

/**
 * Rules for adapting to different environments. If it is `liteWearable` device type,
 * set to this type of verification rule.
 * @param {String} deviceType device type.
 * @return {Object} Validation rules.
 */
function select(deviceType) {
  tag = {
    liteWearable: litewearableTag,
    smartVision: { ...litewearableTag, ...smartvisionTag },
  };
  return tag[deviceType];
}
let liteNativeTag = select(process.env.DEVICE_TYPE);

/**
 * Whether the file exists, get customized rules.
 */
(function checkFile() {
  if (rulePath) {
    const customTag = require(rulePath);
    isExtends(customTag);
  }
})();

/**
 * Get the component types supported by the current verification rule.
 * @return {Array} Supported component name.
 */
function getKeys() {
  const res = [];
  const keys = Object.keys(liteNativeTag);
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    res.push(key);
  }
  res.push('attrs');
  return res;
}

/**
 * According to user-defined rules, combine into new verification rules.
 * @param {Object} customTag User-defined rule object.
 */
function isExtends(customTag) {
  if (customTag.extends == 'recommended') {
    const nativekeys = getKeys();
    merge(liteNativeTag, customTag.rules, nativekeys);
  } else {
    liteNativeTag = customTag.rules;
  }
}
/**
 * Combine the original rules and user-defined rules.
 * @param {Object} object Original rules.
 * @param {Object} source user-defined rules.
 * @param {Array} nativekeys Supported component name.
 * @return {Array} Merged object.
 */
function merge(object, source, nativekeys) {
  const keys = Object.keys(source);
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    const value = source[key];
    let target = object[key];
    if (target != null && !nativekeys.includes(key)) {
      console.error(
          `\u001b[31mError in .literc.js: \n` +
          `Attribute '${key}' already exists and cannot be modified\u001b[39m`,
      );
      process.exit(1);
    } else if (isType.isObject(value)) {
      target = isType.isObject(target) ? target : {};
      object[key] = merge(target, value, nativekeys);
    } else if (!(isType.isNull(value) || isType.isUndefined(value))) {
      object[key] = value;
    }
  }
  return object;
}

module.exports = {
  liteNativeTag: liteNativeTag,
  liteCommonTag: liteCommonTag,
};
