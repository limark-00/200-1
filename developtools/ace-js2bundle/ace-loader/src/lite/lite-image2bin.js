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

const Jimp = require('jimp');
const fs = require('fs');
const _path = require('path');
/**
 * Find all image paths in png、jpg、bmp、jpeg format in the directory.
 * @param {String} imgPath The path of build folder.
 * @return {Array} Image path array.
 */
async function img2bin(imgPath) {
  try {
    const image = await Jimp.read(imgPath);
    const HEAD_SIZE = 8;
    const PIXEL_SIZE = 4;// BRGA
    const DATA_SIZE = image.bitmap.width * image.bitmap.height * PIXEL_SIZE;
    const binSize = HEAD_SIZE + DATA_SIZE;
    const binBuffer = new ArrayBuffer(binSize);
    const binView = new DataView(binBuffer);

    const COLOR_MODE = 1 << 8 + 0;
    const WIDTH_BIT_OFFSET = 0;
    const HEIGHT_BIT_OFFSET = 16;
    const header = (image.bitmap.width << WIDTH_BIT_OFFSET) +
    (image.bitmap.height << HEIGHT_BIT_OFFSET);

    let binFileOffset = 0;
    binView.setUint32(binFileOffset, COLOR_MODE, true);
    binFileOffset += 4;
    binView.setUint32(binFileOffset, header, true);
    binFileOffset += 4;

    image.scan(0, 0, image.bitmap.width, image.bitmap.height, function(x, y, idx) {
      // eslint-disable-next-line no-invalid-this
      const blue = this.bitmap.data[idx + 2];
      binView.setUint8(binFileOffset, blue, true);
      binFileOffset += 1;

      // eslint-disable-next-line no-invalid-this
      const green = this.bitmap.data[idx + 1];
      binView.setUint8(binFileOffset, green, true);
      binFileOffset += 1;

      // eslint-disable-next-line no-invalid-this
      const red = this.bitmap.data[idx + 0];
      binView.setUint8(binFileOffset, red, true);
      binFileOffset += 1;

      // eslint-disable-next-line no-invalid-this
      const alpha = this.bitmap.data[idx + 3];
      binView.setUint8(binFileOffset, alpha, true);
      binFileOffset += 1;
    });
    const binPath = imgPath.replace(/(\.png|\.jpg|\.bmp|\.jpeg|\.BMP|\.JPG|\.PNG|\.JPEG)$/, '.bin');
    fs.writeFileSync(binPath, Buffer.from(binBuffer));
  } catch (err) {
    const imageName = _path.basename(imgPath);
    console.error('\u001b[31m', `Failed to convert image ${imageName}.`, '\u001b[39m');
    throw err;
  }
}

module.exports = img2bin;
