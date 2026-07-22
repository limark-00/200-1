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

const reg = '{{{((.|\n)+?)}}}|{{((.|\n)+?)}}'
const dataReg = new RegExp(reg, 'g')
const expressionReg = new RegExp(reg)

/**
 * Parse expression in hml text
 */
function parseData(v) {
  v.match(dataReg).forEach(element => {
    const repElement = element.toString().trim().replace(/\n/g, '')
    v = v.replace(element, repElement)
  })

  if (!expressionReg.test(v)) {
    return null
  }
  let start
  let next = 0
  const res = []
  dataReg.lastIndex = 0
  for (let i = next; i < v.length; i++) {
    let match = dataReg.exec(v)
    if (!match) {
      break
    }
    start = match.index
    getValue(next, start, v, res)
    parseValue(match, res)
    next = start + match[0].length
  }
  getValue(next, v.length, v, res)
  return res
}

function getValue(begin, end, v, res) {
  if (begin < end) {
    res.push({
      value: v.slice(begin, end)
    })
  }
}

function parseValue(match, res) {
  let three= /^{{{.*}}}$/.test(match[0])
  let v = three ? match[1] : match[3]
  res.push({
    tag: true,
    value: v.trim()
  })
}

exports.parseText = parseData
