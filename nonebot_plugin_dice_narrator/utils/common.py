from typing import Dict

import yaml


def export_data2yml_str(data) -> str:
    """导出字典为yml字符串"""

    return yaml.dump(data, allow_unicode=True, sort_keys=False)


def read_yml_str2data(s: str) -> Dict:
    """读取yml字符串为字典"""

    return yaml.safe_load(s)
