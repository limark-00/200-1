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

var parser = require("@babel/parser")
var traverse = require("@babel/traverse").default
var generate = require("@babel/generator").default

function parseExpression(expression, isEventFunc) {
  const keyWordsReg = new RegExp(`^(NaN\\b|isNaN\\b|isFinite\\b|decodeURI\\b|decodeURIComponent\\b|Math\\b|Date\\b|this\\b|true\\b|false\\b|
    encodeURI\\b|encodeURIComponent\\b|parseInt\\b|parseFloat\\b|null\\b|undefined\\b|Infinity\\b)`, 'g')
  const internalKeyWords = new RegExp(`^(var\\b|while\\b|with\\b|yield\\b|enum\\b|await\\b|implements\\b|package\\b|for\\b|function\\b|if\\b|import\\b|
    protected\\b|static\\b|interface\\b|private\\b|public\\b|break\\b|case\\b|class\\b|catch\\b|const\\b|continue\\b|debugger\\b|
    default\\b|delete\\b|do\\b|else\\b|export\\b|extends\\b|finally\\b|in\\b|instanceof\\b|let\\b|return\\b|super\\b|switch\\b|throw\\b|try\\b)`, 'g')
  const reservedKeyWords = new RegExp(`^(var\\b|while\\b|with\\b|yield\\b|enum\\b|await\\b|implements\\b|package\\b|for\\b|function\\b|if\\b|import\\b|
    protected\\b|static\\b|interface\\b|private\\b|public\\b|break\\b|case\\b|class\\b|catch\\b|const\\b|continue\\b|debugger\\b|
    default\\b|delete\\b|do\\b|else\\b|export\\b|extends\\b|finally\\b|in\\b|instanceof\\b|let\\b|return\\b|super\\b|switch\\b|throw\\b|try\\b|show\\b|tid\\b)$`, 'g')
  try {
    if (reservedKeyWords.test(expression)) {
      throw Error("A data binding parsing error occurred. Do not use the reserved:" + expression).message
    }
    let expAst = isEventFunc ? parser.parse('(' + expression + ')') : parser.parse(expression)
    traverse(expAst, {
      enter(path) {
        if (path.parent && path.node.type === "Identifier") {
          let flag = false
          if (['ConditionalExpression', 'BinaryExpression'].includes(path.parent.type) ||
            path.parent.type === 'CallExpression' && path.parent.callee === path.node) {
            flag = true
          }
          else if (path.parent.type === "ObjectProperty" && !path.parent.computed && path.parent.value === path.node) {
            flag = true
          }
          else {
            flag = addPrefix(path.node, path.parent)
          }
          if (flag && !keyWordsReg.test(path.node.name)) {
            path.node.name = 'this.' + path.node.name
          }
        }
      }
    })
    return generate(expAst, { compact: true }).code.replace(';', '').replace(/\"/g, '\'').replace(/\n/g, '')
  } catch (e) {
    if (isEventFunc) {
      throw internalKeyWords.test(expression) ? Error("An event parsing error occurred. Do not use the reserved:" + expression).message :
        Error("An event parsing error occurred:" + expression).message
    } else {
      throw internalKeyWords.test(expression) ? Error("A data binding parsing error occurred. Do not use the reserved:" + expression).message :
        Error("A data binding parsing error occurred:" + expression).message
    }
  }
}

function addPrefix(node, parent) {
  const attrArr1 = ['expression', 'argument', 'arguments', 'expressions', 'elements', 'left', 'right']
  const attrArr2 = ['object', 'property', 'id', 'key']
  let keyArr = Object.keys(parent)
  for (let i = 0; i < attrArr1.length; i++) {
    if (keyArr.includes(attrArr1[i])) {
      if (parent[attrArr1[i]] === node || ['expressions', 'elements'].includes(attrArr1[i]) &&
        parent[attrArr1[i]].includes(node)) {
        return true
      }
      //support cases like <text style="width:{{1 === count? test(prop):'300px'}}"/>
      if ('arguments' === attrArr1[i] && parent.arguments[0].type === 'Identifier') {
        return true
      }
    }
  }
  for (let i = 0; i < attrArr2.length; i++) {
    if (keyArr.includes(attrArr2[i])) {
      if (parent.computed && parent[attrArr2[i]] === node) {
        return true
      } else {
        if (parent.type === "Property" && parent.key.range[0] === parent.value.range[0] &&
          parent.key.range[1] === parent.value.range[1]) {
          node.name = node.name + ":this." + node.name
        } else if (parent.object === node) {
          return true
        }
      }
    }
  }
  return false
}

exports.parseExpression = parseExpression
