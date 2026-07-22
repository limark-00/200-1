# -*- coding: utf-8 -*-
"""最小化测试：读取env004，并可选择向env004发送测试消息。"""
import argparse
import json
import sys

import bemfa_api
import config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", help="向env004发送一条测试消息，例如 --send pc_online")
    args = parser.parse_args()

    print(f"主题：{config.ENV_TOPIC}，类型：{config.BEMFA_TYPE}，模拟模式：{config.MOCK_MODE}")
    result = bemfa_api.get_topic_msg(config.ENV_TOPIC)
    print("读取结果：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("ok"):
        print("解析后的环境数据：")
        print(json.dumps(bemfa_api.parse_env_message(result.get("msg", "")), ensure_ascii=False, indent=2))

    if args.send:
        sent = bemfa_api.send_msg(config.ENV_TOPIC, args.send)
        print("发送结果：")
        print(json.dumps(sent, ensure_ascii=False, indent=2))
        if not sent.get("ok"):
            return 2

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
