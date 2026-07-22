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
 * Customize the compiled template code into a render function. There are some detailed rules to explain:
 * 1. Convert all numeric strings to numbers, such as:"32px" convert to number 32; "11" convert to number 11;
 * 2. Convert all hex color to decimal number;
 * 3. Convert all boolean strings to boolean type;
 * 4. compile events, the value of event Cannot be enclosed in double quotes;
 */
const { isFunction, isObject, isUndefined } = require('./lite-utils');
const {
  SPECIAL_STYLE,
  REGEXP_NUMBER_PX,
  REGEXP_COLOR,
  REGEXP_UNIT,
  REGXP_QUOTES,
  REGXP_LANGUAGE,
  REGXP_LANGUAGE_KEY,
  REGXP_FUNC_RETURN,
} = require('./lite-enum');
const parameterArray = [];
let parameter1 = '';
let parameter2 = '';
let i18nMapping = {};
const ATTRBUTES = 'attrs';
const EVENTS_ON_FUNC = 'on';
const KEY = 'key';
const AST_KEY = {
  ATTR: 'attr',
  CLASSLIST: 'classList',
  STYLE: 'style',
  EVENTS: 'events',
  TYPE: 'type',
  CHILDREN: 'children',
  KEY: 'key',
};
const EVENT_KEY = [
  'onBubbleEvents',
  'catchBubbleEvents',
  'onCaptureEvents',
  'catchCaptureEvents',
];

const optionRules = {
  [AST_KEY.ATTR]: function(dataContent, node, key) {
    if (Object.keys(node.attr).length !== 0) {
      dataContent += `'${ATTRBUTES}' : ${transformProps(node.attr)},`;
    }
    return dataContent;
  },
  [AST_KEY.CLASSLIST]: function(dataContent, node, key) {
    dataContent += sortClass(node[key]);
    return dataContent;
  },
  [AST_KEY.STYLE]: function(dataContent, node, key) {
    dataContent += sortStyle(node[key]);
    return dataContent;
  },
  [AST_KEY.EVENTS]: function(dataContent, node, key) {
    dataContent += `'${EVENTS_ON_FUNC}' : ${transformEvents(node.events)},`;
    return dataContent;
  },
  [AST_KEY.KEY]: function(dataContent, node, key) {
    dataContent += `'${KEY}' : ${node.key},`;
    return dataContent;
  },
};

const styleRules = [
  {
    match: function(key, value) {
      return key === SPECIAL_STYLE.ANIMATION_DELAY || key === SPECIAL_STYLE.ANIMATION_DURATION;
    },
    action: function(staticStyle, key, value) {
      staticStyle += `'${key}' : ${JSON.stringify(value)},`;
      return staticStyle;
    },
  },
  {
    match: function(key, value) {
      return key === SPECIAL_STYLE.ANIMATION_ITERATION_COUNT;
    },
    action: function(staticStyle, key, value) {
      if (value === -1) {
        value = 'infinite';
      }
      staticStyle += `'${key}' : ${JSON.stringify(value)},`;
      return staticStyle;
    },
  },
  {
    match: function(key, value) {
      return key === SPECIAL_STYLE.BACKGROUND_IMAGE;
    },
    action: function(staticStyle, key, value) {
      staticStyle += `'${key}' : ${checkType(value.replace(REGXP_QUOTES, ''))},`;
      return staticStyle;
    },
  },
  {
    match: function(key, value) {
      return true;
    },
    action: function(staticStyle, key, value) {
      staticStyle += `'${key}' : ${checkType(value)},`;
      return staticStyle;
    },
  },
];

(function() {
  EVENT_KEY.map(function(event) {
    optionRules[event] = function(dataContent, node, key) {
      dataContent += `'${event}' : ${transformEvents(node[event])},`;
      return dataContent;
    };
  });
})();

/**
 * Compile the ast object into an executable function.
 * @param {Obejct} value template object compiled ast.
 * @return {String} template string.
 */
function transformTemplate(value) {
  const ast = Function(`return ${value}`)();
  let template = isObject(ast) ? transformNode(ast) : `_c('div')`;
  template = template.replace(/,$/, '');
  const cachedI18nPushStrings = Object.values(i18nMapping);
  const I18nContect = cachedI18nPushStrings.length === 0 ? '' : ` var i18ns = []; ${cachedI18nPushStrings.join(';')};`;
  const res = `function (vm) { var _vm = vm || this;${I18nContect} return ${template} }`;
  i18nMapping = {};
  return res;
}

/**
 * Divided into if\for\ordinary three kinds node transform.
 * @param {Obejct} node template object compiled ast.
 * @return {String} template string.
 */
function transformNode(node) {
  if (node.repeat && !node.forCompiled) {
    return transformFor(node);
  } else if (node.shown && !node.ifCompiled) {
    return transformIf(node);
  } else {
    return transformNodeDetail(node);
  }
}

/**
 * Divide node into type/child/data three parts and compiled separately.
 * @param {Obejct} node ordinary node.
 * @return {String} ordinary node string.
 */
function transformNodeDetail(node) {
  const type = node.type;
  const options = transformOptions(node);
  const children = transformChildren(node);
  const render = `_c('${type}'${options ? `, ${options} ` : ``}${children ? `, ${children} ` : ``}),`;
  return render;
}

/**
 * Compile node all key-value datas.
 * @param {Obejct} node ordinary node.
 * @return {String} ordinary node attributes string.
 */
function transformOptions(node) {
  let dataContent = '';
  parameter2 = parameterArray[parameterArray.length - 1];
  if (node.attr && node.attr.tid && parameter2 !== '') {
    node['key'] = `${parameter2}.${node.attr['tid']}`;
    delete node.attr.tid;
  }
  for (const key of Object.keys(node)) {
    if (key !== AST_KEY.TYPE && key !== AST_KEY.CHILDREN) {
      if (optionRules[key]) {
        dataContent = optionRules[key](dataContent, node, key);
      }
    }
  }
  if (dataContent === '') {
    return null;
  }
  dataContent = '{' + dataContent.replace(/,$/, '') + '}';
  return dataContent;
}

/**
 * Compile node classList, divided into dynamicClass and staticClass.
 * @param {Function|String} classList the object of class list.
 * @return {String} class list string.
 */
function sortClass(classList) {
  let classStr = '';
  const DYNAMIC_CLASS = 'dynamicClass';
  const STATIC_CLASS = 'staticClass';
  const value = checkType(classList);
  // Divid into two parts dynamicClass and staticClass depending on whether it is a method type
  if ((isFunction(classList) || isUndefined(classList)) && !REGXP_LANGUAGE.test(classList)) {
    classStr += `'${DYNAMIC_CLASS}' : ${formatForFunc(value)},`;
  } else {
    classStr += `'${STATIC_CLASS}' : ${value},`;
  }
  return classStr;
}

/**
 * Compile node style, divided into staticStyle and staticStyle.
 * @param {Object} props the object of style.
 * @return {String} style list string.
 */
function sortStyle(props) {
  let staticStyle = '';
  let dynamicStyle = '';
  const STASTIC_STYLE = 'staticStyle';
  const DYNAMIC_STYLE = 'dynamicStyle';
  for (const key of Object.keys(props)) {
    const value = props[key];
    // Divid into two parts staticStyle and dynamicStyle depending on whether it is a method type
    if (isFunction(value) && !REGXP_LANGUAGE.test(value)) {
      dynamicStyle += `'${key}' : ${formatForFunc(value)},`;
    } else {
      for (let i = 0; i < styleRules.length; i++) {
        if (styleRules[i].match(key, value)) {
          staticStyle = styleRules[i].action(staticStyle, key, value);
          break;
        }
      }
    }
  }
  if (staticStyle !== '') {
    staticStyle = `'${STASTIC_STYLE}' : {${staticStyle.replace(/,$/, '')}}, `;
  }
  if (dynamicStyle !== '') {
    dynamicStyle = `'${DYNAMIC_STYLE}' :{${dynamicStyle.replace(/,$/, '')}},`;
  }
  return staticStyle + dynamicStyle;
}

/**
 * general method ,judge type and compile, There are some special rules defined here,
 * such as:"32px" convert to number 32; "11" convert to number 11; "#ffffff" convert to number 16777215.
 * @param {*} value Value to be formatted.
 * @return {*} Formatted value.
 */
function checkType(value) {
  if (isFunction(value) || isUndefined(value)) {
    return formatForFunc(value);
    // Use recursive conversion of object type values
  } else if (isObject(value)) {
    return transformProps(value);
    // Convert all numeric strings to numbers
  } else if (!isNaN(Number(value))) {
    return Number(value);
  } else if (REGEXP_NUMBER_PX.test(value)) {
    return parseInt(value.replace(REGEXP_UNIT, ''), 10);
    // Convert all colors to numbers
  } else if (REGEXP_COLOR.test(value)) {
    return parseInt(value.slice(1), 16);
    // Convert all boolean strings to boolean type
  } else if (value === 'true') {
    return true;
  } else if (value === 'false') {
    return false;
  } else {
    return JSON.stringify(value);
  }
}

/**
 * general method, compile data of object type, and compile node attributes.
 * apart from The case where key is "value".
 * @param {Object} props Value to be formatted.
 * @return {String} Formatted value.
 */
function transformProps(props) {
  let propContent = '';
  const VALUE = 'value';
  for (const key of Object.keys(props)) {
    const propValue = props[key];
    // value is used to display, except for method types, no conversion is required
    if (key === VALUE) {
      if (isFunction(propValue) || isUndefined(propValue)) {
        propContent += `'${key}' : ${formatForFunc(props[key])},`;
      } else {
        propContent += `'${key}' : ${JSON.stringify(props[key])},`;
      }
    } else {
      propContent += `'${key}' : ${checkType(props[key])},`;
    }
  }
  propContent = `{${propContent.replace(/,$/, '')}}`;
  return propContent;
}

/**
 * compile events, divided into two types of conversion methods and string types.
 * @param {Object} props Value of events to be formatted.
 * @return {String} Formatted Value of events.
 */
function transformEvents(props) {
  let eventContent = '';
  for (const key of Object.keys(props)) {
    if (isFunction(props[key])) {
      /**
       * Method contains parameters and will be compiled into a method.
       * such as: onclick = "test(value)" => "click": function(evt){this.test(this.value, evt)}
       */
      eventContent += `'${key}' : ${formatForFunc(props[key])},`;
    } else {
      /**
       * The method contains no parameters and will be compiled into a string.
       * such as: onclick = "test" => "click": "test"
       */
      eventContent += `'${key}' : ${formatForString(props[key])},`;
    }
  }
  eventContent = `{${eventContent.replace(/,$/, '')}}`;
  return eventContent;
}

/**
 * Compile events of type string, add `_vm.` in front of ordinary events, such as: onclick="test" => "click": "_vm.test"
 * do nothing for the data in the `for` loop, such as: onclick="{{$item.click}}" =>  "click": "$item.click"
 * @param {Object} value string type of events to be formatted.
 * @return {String} Formatted Value of events.
 */
function formatForString(value) {
  let forCompiled = false;
  for (const parameter of parameterArray) {
    // '$' Needs to be escaped in regular expressions. The parameter in the for instruction may be '$idx' and '$item'
    const escape = parameter.charAt(0) === '$' ? '\\' : '';
    const itRE = new RegExp(escape + parameter);
    // Match the variable name in the stack, to determine whether it is ordinary event or an event in the for
    if (itRE.test(value)) {
      forCompiled = true;
      break;
    }
  }
  const res = forCompiled ? value : '_vm.' + value;
  return res;
}

/**
 * compile "for" direct, return the _l function.
 * @param {Object} node node obejct with "for" directive.
 * @return {String} string of _l function.
 */
function transformFor(node) {
  let exp = node.repeat.exp ? node.repeat.exp : node.repeat;
  parameterArray.push(node.repeat.key ? node.repeat.key : '$idx');
  parameterArray.push(node.repeat.value ? node.repeat.value : '$item');
  node.forCompiled = true;
  // Set context and stack to convert "this.index" to "index" in the for function
  exp = formatForFunc(exp);
  const children = transformNode(node).replace(/,$/, '');
  parameter2 = parameterArray[parameterArray.length - 1];
  parameter1 = parameterArray[parameterArray.length - 2];
  const comma = parameter1 !== '' && parameter2 !== '' ? ',' : '';
  parameterArray.pop();
  parameterArray.pop();
  return '_l' + '((' + exp + '),' + 'function(' + parameter2 + comma + parameter1 + '){' + 'return ' + children + '}),';
}

/**
 * compile "if" direct, return the _i function.
 * @param {Object} node node obejct with "if" directive.
 * @return {String} string of _i function.
 */
function transformIf(node) {
  node.ifCompiled = true;
  const children = transformNode(node).replace(/,$/, '');
  return '_i' + '((' + formatForFunc(node.shown) + '),' + 'function(){return ' + children + '}),';
}

/**
 * convert "this.index" to "index" in the for function. if the element is not in the for function,
 * there will be no value in parameterArray
 * @param {Object} value Value of function to be formatted.
 * @return {String} Formatted Value of events.
 */
function formatForFunc(value) {
  let func = value.toString();
  for (const parameter of parameterArray) {
    // '$' Needs to be escaped in regular expressions. The parameter in the for instruction may be '$idx' and '$item'
    const escape = parameter.charAt(0) === '$' ? '\\' : '';
    const itRE = new RegExp('this.' + escape + parameter + '\\b', 'g');
    /**
     * If it is a parameter in the for instruction, remove 'this'.
     * such as: {"value": function () {return this.$item.name}}  => {"value": function () {return $item.name}}
     */
    func = func.replace(itRE, parameter);
  }
  // Replace all "this" to "_vm"
  func = func.replace(/this\./g, '_vm.');
  // Internationalization performance optimization
  func = cacheI18nTranslation(func);
  return func;
}

/**
 * There is only one $t internationalizations in the processing function.
 * @param {String} i18nExpression match the value of $t in the internationalization method.
 * @param {Array} cachedI18nExpressions all keys of i18n Mapping object.
 * @return {String} treated internationalization method.
 */
function handleLangSingle(i18nExpression, cachedI18nExpressions) {
  let res = '';
  if (cachedI18nExpressions.includes(i18nExpression)) {
    // The i18nExpression already exists in cachedI18nExpressions
    const cachedI18nPushStrings = Object.values(i18nMapping);
    const cachedI18nPushString = i18nMapping[i18nExpression];
    res = `i18ns[${cachedI18nPushStrings.lastIndexOf(cachedI18nPushString)}]`;
  } else {
    // The i18nExpression does not exist in cachedI18nExpressions
    i18nMapping[
        i18nExpression
    ] = `i18ns.push( ${i18nExpression} )`;
    res = `i18ns[${Object.keys(i18nMapping).length - 1}]`;
  }
  return res;
}

/**
 * There are multiple $t internationalizations in the processing function..
 * @param {Array} i18nExpressions match the value of $t in the internationalization method.
 * @param {Array} cachedI18nExpressions all keys of i18n Mapping object.
 * @param {String} funcExpression return value in the internationalization method.
 * @param {String} func internationalization method.
 * @return {String} treated internationalization method.
 */
function handleLangMulti(i18nExpressions, cachedI18nExpressions, funcExpression, func) {
  let res = func;
  // The funcExpression already exists in cachedI18nExpressions
  if (cachedI18nExpressions.includes(funcExpression)) {
    const cachedI18nPushStrings = Object.values(i18nMapping);
    const cachedI18nPushString = i18nMapping[funcExpression];
    res = `i18ns[${cachedI18nPushStrings.lastIndexOf(cachedI18nPushString)}]`;
    // The funcExpression does not exist in cachedI18nExpressions
  } else {
    for (let i = 0; i < i18nExpressions.length; i++) {
      const i18nExpression = i18nExpressions[i];
      // The i18nExpression already exists in cachedI18nExpressions
      if (cachedI18nExpressions.includes(i18nExpression)) {
        const cachedI18nPushStrings = Object.values(i18nMapping);
        const cachedI18nPushString = i18nMapping[i18nExpression];
        res = res.replace(
            i18nExpression,
            `i18ns[${cachedI18nPushStrings.lastIndexOf(cachedI18nPushString)}]`,
        );
        // The i18nExpression does not exists in cachedI18nExpressions
      } else {
        i18nMapping[
            i18nExpression
        ] = `i18ns.push( ${i18nExpression} )`;
        res = res.replace(
            i18nExpression,
            `i18ns[${Object.keys(i18nMapping).length - 1}]`,
        );
      }
      // For the last $t, replace the func value
      if (i === i18nExpressions.length - 1 && !res.includes('_vm.')) {
        const funcReturnMatches = REGXP_FUNC_RETURN.exec(res);
        REGXP_FUNC_RETURN.lastIndex = 0;
        const funcReturnMatch = funcReturnMatches[1].trim();
        i18nMapping[funcExpression] = `i18ns.push( ${funcReturnMatch} )`;
        res = `i18ns[${Object.keys(i18nMapping).length - 1}]`;
      }
    }
  }
  return res;
}

/**
 * Internationalization performance optimization operation.
 * @param {String} func string for globalization method.
 * @return {String} Whether to use the parameters in 'for' instruction.
 */
function cacheI18nTranslation(func) {
  if (!REGXP_LANGUAGE.test(func)) {
    return func;
  }
  const i18nExpressions = func.match(REGXP_LANGUAGE_KEY);
  const cachedI18nExpressions = Object.keys(i18nMapping);
  const funcExpressions = REGXP_FUNC_RETURN.exec(func);
  REGXP_FUNC_RETURN.lastIndex = 0;
  const funcExpression = funcExpressions[1].trim();
  // If the 'for' parameter is used in $t, nothing will be done
  if (isUseForInstrucParam(funcExpression)) {
    return func;
  }
  // There is only one $t internationalization in the function.
  // such as:function () { return ( _vm.$t('i18n.text.value1')) }
  if (i18nExpressions.length === 1 && i18nExpressions[0] === funcExpression) {
    const i18nExpression = i18nExpressions[0];
    func = handleLangSingle(i18nExpression, cachedI18nExpressions);
    // There are multiple $t internationalization in the function.
    // such as: function () { return ( _vm.$t('i18n.text.value1') - _vm.$t('i18n.text.value2')); }
  } else {
    func = handleLangMulti(i18nExpressions, cachedI18nExpressions, funcExpression, func);
  }
  return func;
}

/**
 * Determine whether the parameters in the 'for' instruction are used in the globalization method.
 * @param {String} value string for globalization method.
 * @return {Blooean} Whether to use the parameters in 'for' instruction.
 */
function isUseForInstrucParam(value) {
  let isUseParam = false;
  for (const parameter of parameterArray) {
    const escape = parameter.charAt(0) === '$' ? '\\' : '';
    const itRE = new RegExp(escape + parameter);
    // Match the variable name in the stack, to determine whether it is ordinary event or an event in the for
    if (itRE.test(value)) {
      isUseParam = true;
      break;
    }
  }
  return isUseParam;
}

/**
 * compile node children.
 * @param {Object} node ordinary node.
 * @return {String} ordinary node children string.
 */
function transformChildren(node) {
  const children = node.children;
  if (!children) {
    return null;
  }
  let childContent = '';
  for (let i = 0; i < children.length; i++) {
    childContent += transformNode(children[i]);
  }
  childContent = '[' + childContent.replace(/,$/, '') + ']';
  return childContent;
}

exports.transformTemplate = transformTemplate;
