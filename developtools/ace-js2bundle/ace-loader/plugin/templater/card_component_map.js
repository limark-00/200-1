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

var cardNativeTag = {
  'div': {
    events: [],
    attrs: {}
  },
  'stack': {
    events: [],
    attrs: {}
  },
  'image': {
    alias: ['img'],
    atomic: true,
    selfClosing: true,
    events: ['error', 'complete'],
    attrs: {
      src: {},
      alt: {}
    }
  },
  'progress': {
    atomic: true,
    selfClosing: true,
    events: [],
    attrs: {
      type: {
        def: 'horizontal',
        enum: ['horizontal', 'circular', 'ring', 'scale-ring', 'arc', 'eclipse']
      },
      percent: {
        def: 0,
        checkFunc: 'number'
      },
      secondarypercent: {
        def: 0,
        checkFunc: 'number'
      },
      clockwise: {
        def: 'true',
        enum: ['true', 'false']
      },
    },
  },
  'text': {
    textContent: true,
    events: [],
    children: ['span'],
    attrs: {}
  },
  'span': {
    textContent: true,
    excludeRoot: true,
    parents: ['text', 'span'],
    events: [],
    children: ['span'],
    attrs: {},
  },
  'chart': {
    atomic: true,
    selfClosing: true,
    events: [],
    attrs: {
      type: {
        def: 'line',
        enum: ['line', 'bar', 'gauge', 'progress', 'loading', 'rainbow'],
        required: true
      },
      options: {},
      datasets: {},
      percent: {
        def: 0,
        checkFunc: 'number'
      },
      segments: {},
      effects: {
        def: 'true',
        enum: ['true', 'false']
      },
    }
  },
  'button': {
    textContent: true,
    atomic: true,
    selfClosing: true,
    attrs: {
      type: {
        enum: ['capsule', 'circle', 'text', 'arc']
      },
      value: {},
      icon: {},
      waiting: {
        def: 'false',
        enum: ['false', 'true']
      },
      placement: {
        def: 'end',
        enum: ['end', 'start', 'top', 'bottom'],
      },
    }
  },
  'badge': {
    attrs: {
      placement: {
        def: 'rightTop',
        enum: ['rightTop', 'right', 'left']
      },
      count: {
        def: 0,
        checkFunc: 'number'
      },
      visible: {
        def: 'false',
        enum: ["false", "true"]
      },
      maxcount: {
        def: 99,
        checkFunc: 'number',
      },
      config: {},
    },
  },
  'list': {
    children: ['list-item'],
    attrs: {
      cachedcount: {
        def: 0,
        checkFunc: 'number',
      },
      scrollbar: {
        def: 'off',
        enum: ['off', 'auto', 'on'],
      },
      scrolleffect: {
        def: 'spring',
        enum: ['spring', 'fade', 'no'],
      },
      divider: {
        def: 'false',
        enum: ['false', 'true'],
      },
      shapemode: {
        def: 'default',
        enum: ['default', 'rect', 'round'],
      },
      updateeffect: {
        def: 'false',
        enum: ['false', 'true'],
      },
      initialindex: {
        def: 0,
        checkFunc: 'number',
      },
      initialoffset: {
        def: 0,
        checkFunc: 'length',
      },
      selected: {}
    },
  },
  'list-item': {
    excludeRoot: true,
    parents: ['list'],
    attrs: {
      for: {},
      type: {
        def: 'default',
      },
      section: {},
      sticky: {
        def: 'none',
        enum: ['none', 'normal', 'opacity'],
      },
    },
  },
  'block': {
    excludeRoot: true,
    attrs: {},
  },
  'swiper': {
    unSupportedChildren: ['list'],
    attrs: {
      indicator: {
        def: 'true',
        enum: ['true', 'false'],
      },
      index: {
        def: 0,
        checkFunc: 'number',
      },
      duration: {
        checkFunc: 'number',
      },
      vertical: {
        def: 'false',
        enum: ['false', 'true'],
      },
      digital: {
        def: 'false',
        enum: ['false', 'true'],
      },
      loop: {
        def: 'true',
        enum: ['true', 'false'],
      },
      animationopacity: {
        def: 'true',
        enum: ['true', 'false'],
      }
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
  'clock': {
    atomic: true,
    attrs: {
      clockconfig: {
        required: true
      },
      showdigit: {
        def: 'true',
        enum: ['true', 'false'],
      },
      hourswest: {
        checkFunc: 'number',
      },
    },
  },
  'divider': {
    atomic: true,
    selfClosing: true,
    attrs: {
      vertical: {
        def: 'false',
        enum: ['false', 'true'],
      },
    },
  },
  'input': {
    atomic: true,
    selfClosing: true,
    events: ['change'],
    attrs: {
      checked: {
        def: 'false',
        enum: ['false', 'true'],
      },
      type: {
        def: 'radio',
        enum: ['radio'],
        required: true,
      },
      name: {},
      value: {},
    },
  },
}

var cardCommonTag = {
  'events': [
    'click'
  ],
  'attrs': {
    id: {},
    style: {},
    class: {},
    disabled: {
      def: 'false',
      enum: ['false', 'true']
    },
    if: {
      excludeRoot: true,
      def: 'true'
    },
    elif: {
      def: 'true'
    },
    else: {
      excludeRoot: true
    },
    show: {
      excludeRoot: true,
      def: 'true'
    },
    accessibilitygroup: {
      enum: ['false', 'true'],
    },
    accessibilitytext: {},
    accessibilitydescription: {},
    accessibilityimportance: {
      enum: ['auto', 'yes', 'no', 'no-hide-descendants'],
    },
  },
  'children': ['block', 'slot'],
  'parents': ['block']
}

module.exports = {
  cardCommonTag: cardCommonTag,
  cardNativeTag: cardNativeTag
}
