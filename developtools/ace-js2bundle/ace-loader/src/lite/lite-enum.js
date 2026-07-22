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

const SPECIAL_STYLE = {
  OPACITY: 'opacity',
  BORDEROPACITY: 'borderOpacity',
  ANIMATION_DELAY: 'animationDelay',
  ANIMATION_DURATION: 'animationDuration',
  ANIMATION_ITERATION_COUNT: 'animationIterationCount',
  BACKGROUND_IMAGE: 'backgroundImage',
  BACKGROUND_IMAGE_ACTIVE: 'backgroundImage:active',
  BACKGROUND_IMAGE_CHECKED: 'backgroundImage:checked',
};
const DEVICE_LEVEL = {
  RICH: 'rich',
  LITE: 'lite',
  CARD: 'card',
};
const DEVICE_TYPE = {
  LITEWEARABLE: 'liteWearable',
  SMARTVISION: 'smartVision',
};

const PLATFORM = {
  VERSION3: 'Version3',
  VERSION4: 'Version4',
  VERSION5: 'Version5',
  VERSION6: 'Version6',
};

const REGEXP_NUMBER_PX = /^[-+]?[0-9]*\.?[0-9]+(px|cm|em|deg|rad)?$/;
const REGEXP_COLOR = /^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$/;
const REGEXP_UNIT = /px|cm|em|deg|rad/;
const REGEXP_PNG = /(\.png|\.jpg|\.bmp|\.jpeg|\.BMP|\.JPG|\.PNG|\.JPEG)$/;
const REGXP_QUOTES = /"|'/g;
const REGXP_LANGUAGE = /\$t/;
const REGXP_LANGUAGE_KEY = /_vm\.\$t\([^()]+?\)/g;
const REGXP_FUNC_RETURN = /return(.*)}/g;

exports.SPECIAL_STYLE = SPECIAL_STYLE;
exports.REGEXP_NUMBER_PX = REGEXP_NUMBER_PX;
exports.REGEXP_COLOR = REGEXP_COLOR;
exports.REGEXP_UNIT = REGEXP_UNIT;
exports.DEVICE_LEVEL = DEVICE_LEVEL;
exports.REGEXP_PNG = REGEXP_PNG;
exports.REGXP_QUOTES = REGXP_QUOTES;
exports.DEVICE_TYPE = DEVICE_TYPE;
exports.REGXP_LANGUAGE = REGXP_LANGUAGE;
exports.REGXP_LANGUAGE_KEY = REGXP_LANGUAGE_KEY;
exports.REGXP_FUNC_RETURN = REGXP_FUNC_RETURN;
exports.PLATFORM = PLATFORM;
