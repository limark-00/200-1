/*
 * Copyright (c) 2020 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License")
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

const content = require('./content')
const data = require('./data')
const { DEVICE_LEVEL } = require('../lite/lite-enum')
const card = process.env.DEVICE_LEVEL === DEVICE_LEVEL.CARD
const REG_CARD_ARRAY = /(\['.+?'\])|(\[".+?"\])/g

/**
 * Check if there is data binding.
 * @param {Object} initValue Hml text token information.
 * @param {Object} functionFlag Hml text token information.
 * @return {String} Compiled data binding
 */
function transExp(initValue, functionFlag, isValue, out, nodeLoc) {
  let value = initValue.toString().trim()
  const hasExpFlag = isExp(value)
  if (hasExpFlag) {
    value = parseExp(value, functionFlag, isValue, out, nodeLoc)
  }
  return value
}
/**
 * parse data binding.
 * @param {Object} value Hml text token information.
 * @param {Object} functionFlag Hml text token information.
 * @return {String} Compiled data binding
 */
function parseExp(value, functionFlag, isValue, out, nodeLoc) {
  const textArray = data.parseText(value)
  const explist = []
  for (let i = 0; i < textArray.length; i++) {
    const exp = textArray[i]
    let transValue
    if (exp.tag) {
      if (card) {
        checkCard(exp.value, out, nodeLoc)
      }
      transValue = card ? `{{${transCardArray(exp.value)}}}` : content.parseExpression(exp.value)
        if (textArray.length !== 1 && !card) {
          transValue = `(${transValue})`
        }
    } else {
      transValue = card ? exp.value : `decodeURI('${encodeURI(exp.value).replace(/\'/g, '%27')}')`
    }
    explist.push(transValue)
  }
  if (card && checkCardVersionLimit() && isValue) {
    if (explist.length > 1) {
      out.log.push({
        line: nodeLoc.line || 1,
        column: nodeLoc.col || 1,
        reason: 'ERROR: Variable concatenation is not supported currently.',
      })
    }
  }
  let func = explist.join(card ? '' : ' + ')
  if (functionFlag !== false && !card) {
    func = eval('(function () {return ' + func + '})')
  }
  func = card && textArray.length > 1 ? '$f(' + func + ')' : func

  return func
}

/**
 * Check if there is data binding in the list.
 * @param {String} initValue Hml text token information.
 * @return {String} Compiled data binding in list
 */
function transExpForList(initValue) {
  let value = initValue.toString().trim()
  const hasExpListFlag = containExp(value)
  if (hasExpListFlag) {
    value = parseExpList(value)
  }
  return value
}
/**
 * parse data binding in list.
 * @param {String} value Hml text token information.
 * @return {String} Compiled data binding in list
 */
function parseExpList(value) {
  const exprMatch = value.match(/{{{([\s\S]+?)}}}|{{([\s\S]+?)}}/g)
  const exprArray = value.replace(/{{{([\s\S]+?)}}}|{{([\s\S]+?)}}/g, '&e').split(/\s+/)
  let n = 0
  const result = []
  exprArray.forEach((item)=>{
    if (item.indexOf('&e') >= 0) {
      while (item.indexOf('&e') >= 0) {
        item = item.replace('&e', exprMatch[n++])
      }
      const textArray = data.parseText(item)
      const exprlist = []
      if (textArray) {
        textArray.forEach(function(text) {
          const transValue = text.tag ?
            card ? `{{${text.value}}}` : content.parseExpression(text.value) :
            card ? text.value : `'${text.value}'`
          exprlist.push(transValue)
        })
        result.push(exprlist.join('+'))
      }
    } else {
      const value = card ? item : `'${item}'`
      result.push(value)
    }
  })

  return card ? result : "(function () {return [" + result.join(", ") + "]})"
}

/**
 * Regexp determine whether there is data binding.
 * @param {String} value expression value.
 * @return {Boolean} Test results
 */
function isExp(value) {
  const REGEXP_DATABIND = /{{{([\s\S]+?)}}}|{{([\s\S]+?)}}/
  return REGEXP_DATABIND.test(value)
}

/**
 * Global regexp determine whether there is data binding.
 * @param {String} value expression value.
 * @return {Boolean} Test results
 */
function containExp(value) {
  const REGEXP_DATABIND_ALL = /{{{([\s\S]+?)}}}|{{([\s\S]+?)}}/g
  return REGEXP_DATABIND_ALL.test(value)
}

/**
 * Replace value on match.
 * @param {String} value expression value.
 * @return {String} The result after replacement
 */
function removeAllExpFix(value) {
  const REGEXP_PRE_DATABIND = /\{\{\{?|\}\}\}?/g
  return containExp(value) ? value.replace(REGEXP_PRE_DATABIND, '') : value
}

/**
 * Change array format in card
 * @param {String} value Array in card
 * @return {String} The card array format
 */
function transCardArray(value) {
  value = value.replace(REG_CARD_ARRAY, item => {
    return `.${item.slice(2, -2)}.`
  })
  if (value.charAt(value.length - 1) === '.') {
    value = value.slice(0, -1)
  }
  return value
}

function checkCard(value, out, nodeLoc) {
  if (!checkApi(value) && !checkIdxAndItem(value)) {
    if (checkCardVersionLimit() && !checkVariable(value)){
      out.log.push({
        line: nodeLoc.line || 1,
        column: nodeLoc.col || 1,
        reason: `ERROR: Version 5: The expression '${value}' is not supported. Only single variables are supported.`
      })
    } else if (!checkCardVersionLimit() && !checkExpression(value)) {
      out.log.push({
        line: nodeLoc.line || 1,
        column: nodeLoc.col || 1,
        reason: `ERROR: Version 6 and above: The expression '${value}' is not supported. Only the binocular expression, ` +
          `OR expression, AND expression and NOT expression are supported.`
      })
    }
  }
}

function checkCardVersionLimit() {
  return parseInt(process.env.PLATFORM_VERSION.replace('Version', '')) < 6
}

function checkApi(value) {
  return /^\$(tc|t|r)/m.test(value)
}

function checkExpression(value) {
  return checkVariable(value) || checkOR(value) || checkAND(value) || checkNOT(value) || checkBinocular(value)
}

function checkIdxAndItem(value) {
  return value === '$idx' || value === '$item'
}

function checkVariable(value) {
  return /^[a-zA-Z\$_][a-zA-Z\d_\.\[\]'"`\s]*$/.test(value)
}

function checkOR(value) {
  return /^[a-zA-Z\$_][a-zA-Z\d_\.\[\]'"`\s]*\|\|[a-zA-Z\$_\s][a-zA-Z\d_\.\[\]'"`\s]*$/m.test(value)
}

function checkAND(value) {
  return /^[a-zA-Z\$_][a-zA-Z\d_\.\[\]'"`\s]*&&[a-zA-Z\$_\s][a-zA-Z\d_\.\[\]'"`\s]*$/m.test(value)
}

function checkNOT(value) {
  return /^![a-zA-Z\$_][a-zA-Z\d_\.\[\]'"`\s]*$/m.test(value)
}

function checkBinocular(value) {
  return /^[a-zA-Z\$_][a-zA-Z\d_\.\[\]'"`\s]*\?[a-zA-Z\$_\s][a-zA-Z\d_\.\[\]'"`\s]*:[a-zA-Z\$_\s][a-zA-Z\d_\.\[\]'"`\s]*$/m.test(value)
}

transExp.checkApi = checkApi
transExp.checkExpression = checkExpression
transExp.checkIdxAndItem = checkIdxAndItem
transExp.checkVariable = checkVariable
transExp.checkAND = checkAND
transExp.checkOR = checkOR
transExp.checkNOT = checkNOT
transExp.isExp = isExp
transExp.containExp = containExp
transExp.removeAllExpFix = removeAllExpFix
transExp.transExpForList = transExpForList
transExp.transCardArray = transCardArray
module.exports = transExp
