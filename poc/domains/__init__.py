"""业务领域包注册表。

新增业务领域三步：
1. 新建 ``domains/<业务名>/`` 包（tools / prompts / schemas / domain）；
2. 实现 :class:`engine.DomainPackage` 子类；
3. 在下方 ``DOMAIN_REGISTRY`` 登记。

引擎通过 ``load_domain`` 拿到领域包，其余业务无关。
"""

from __future__ import annotations

from typing import Type

from engine.domain import DomainPackage

from .stock_qa.domain import StockQaDomain
from .weather.domain import WeatherDomain

DOMAIN_REGISTRY: dict[str, Type[DomainPackage]] = {
    StockQaDomain.name: StockQaDomain,
    WeatherDomain.name: WeatherDomain,
}


def list_domains() -> list[str]:
    """返回全部可用领域名（有序）。"""
    return sorted(DOMAIN_REGISTRY)


def load_domain(name: str) -> DomainPackage:
    """按名称实例化领域包；未知名称抛出 ValueError。"""
    try:
        domain_cls = DOMAIN_REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"未知领域 '{name}'，可选：{', '.join(list_domains())}",
        ) from None
    return domain_cls()


__all__ = ["DOMAIN_REGISTRY", "DomainPackage", "list_domains", "load_domain"]
