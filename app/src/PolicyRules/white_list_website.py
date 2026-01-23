import re
import ipaddress
import urllib.parse
from typing import List, Tuple

from src.AppConfig.app_config_store import AppConfigStore


class WebsiteWhitelistChecker:
    """网站白名单检查器

    支持多种白名单格式：
    - 普通域名: qq.com
    - IP网段: 1.1.1.0/24
    - IP范围: 3.4.5.6 -> 9.4.8.7
    - 子域名通配符: all>qq.com
    - 顶级域名通配符: top>.cn

    Args:
        entries: 来自配置的白名单条目列表。
    """

    def __init__(self, entries=None):
        self.white_sites = []
        self.ip_ranges = []
        self.ip_ranges_manual = []
        self.subdomain_patterns = []
        self.tld_patterns = []
        self._config_version = -1
        self.url_patterns = [
            re.compile(r'https?://(?:www\.)?([a-zA-Z0-9.-]+)'),
            re.compile(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'),
            re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        ]
        self.load_sites(entries)

    def load_sites(self, entries=None):
        """加载白名单网站"""
        config = AppConfigStore.get()
        if entries is None:
            entries = config.get("website_whitelist", [])

        self._reset_config()
        for line in entries:
            line = str(line).strip()
            if not line or line.startswith("#"):
                continue
            self._parse_config_line(line)
        self._config_version = AppConfigStore.version()

    def _parse_config_line(self, line: str):
        """解析配置行"""
        try:
            # IP网段格式: 1.1.1.0/24
            if '/' in line and self._is_ip_cidr(line):
                network = ipaddress.IPv4Network(line, strict=False)
                self.ip_ranges.append(network)
                return

            # IP范围格式: 3.4.5.6 -> 9.4.8.7
            if ' -> ' in line:
                start_ip, end_ip = line.split(' -> ')
                start_ip = start_ip.strip()
                end_ip = end_ip.strip()
                if self._is_ip_address(start_ip) and self._is_ip_address(end_ip):
                    self.ip_ranges_manual.append((
                        ipaddress.IPv4Address(start_ip),
                        ipaddress.IPv4Address(end_ip)
                    ))
                    return

            # 子域名模式: all>qq.com
            if line.startswith('all>'):
                domain = self._normalize_domain(line[4:].strip())
                if not domain:
                    return
                self.subdomain_patterns.append(domain)
                return

            # 顶级域名模式: top>.cn
            if line.startswith('top>'):
                tld = self._normalize_domain(line[4:].strip())
                if not tld:
                    return
                self.tld_patterns.append(tld)
                return

            # 普通域名
            normalized = self._normalize_domain(line)
            if not normalized:
                return
            if self._is_ip_address(normalized):
                ip = ipaddress.IPv4Address(normalized)
                self.ip_ranges_manual.append((ip, ip))
                return
            self.white_sites.append(normalized)

        except Exception as e:
            # 模块中使用异常而不是print，让调用者决定如何处理
            pass

    def _is_ip_cidr(self, text: str) -> bool:
        """检查是否是IP CIDR格式"""
        try:
            ipaddress.IPv4Network(text, strict=False)
            return True
        except:
            return False

    def _is_ip_address(self, text: str) -> bool:
        """检查是否是IP地址"""
        try:
            ipaddress.IPv4Address(text)
            return True
        except:
            return False

    def _normalize_domain(self, value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        if "://" in text:
            parsed = urllib.parse.urlparse(text)
            text = parsed.netloc or parsed.path
        if "/" in text:
            text = text.split("/")[0]
        if ":" in text:
            text = text.split(":")[0]
        if text.startswith("www."):
            text = text[4:]
        return text.lower()

    def _reset_config(self):
        """重置配置"""
        self.white_sites = []
        self.ip_ranges = []
        self.ip_ranges_manual = []
        self.subdomain_patterns = []
        self.tld_patterns = []

    def _ensure_latest(self):
        AppConfigStore.get()
        if AppConfigStore.version() != self._config_version:
            self.load_sites()

    def extract_domains_and_ips(self, message: str) -> Tuple[List[str], List[str]]:
        """提取消息中的域名和IP地址"""
        domains = []
        ips = []

        for pattern in self.url_patterns:
            matches = pattern.findall(message)
            for match in matches:
                if self._is_ip_address(match):
                    ips.append(match)
                else:
                    domains.append(match)

        return list(set(domains)), list(set(ips))

    def _check_ip_whitelist(self, ip_str: str) -> bool:
        """检查IP是否在白名单中"""
        try:
            ip = ipaddress.IPv4Address(ip_str)

            # 检查IP网段
            for network in self.ip_ranges:
                if ip in network:
                    return True

            # 检查IP范围
            for start_ip, end_ip in self.ip_ranges_manual:
                if start_ip <= ip <= end_ip:
                    return True

            return False
        except:
            return False

    def _check_domain_whitelist(self, domain: str) -> bool:
        """检查域名是否在白名单中"""
        domain = self._normalize_domain(domain)
        if not domain:
            return False

        # 检查普通域名
        for white_site in self.white_sites:
            if domain == white_site or domain.endswith('.' + white_site):
                return True

        # 检查子域名模式 (all>qq.com)
        for pattern in self.subdomain_patterns:
            pattern = pattern.lower()
            if domain == pattern or domain.endswith('.' + pattern):
                return True

        # 检查顶级域名模式 (top>.cn)
        for tld in self.tld_patterns:
            tld = tld.lower()
            if domain.endswith(tld):
                return True

        return False

    def check_whitelist(self, message: str) -> Tuple[bool, List[str]]:
        """检查消息中的网站/IP是否在白名单"""
        self._ensure_latest()
        domains, ips = self.extract_domains_and_ips(message)
        all_targets = domains + ips

        if not all_targets:
            return True, []

        # 检查域名
        for domain in domains:
            if not self._check_domain_whitelist(domain):
                return False, all_targets

        # 检查IP
        for ip in ips:
            if not self._check_ip_whitelist(ip):
                return False, all_targets

        return True, all_targets

    def is_target_whitelisted(self, target: str) -> bool:
        """检查单个目标（域名或IP）是否在白名单"""
        self._ensure_latest()
        if self._is_ip_address(target):
            return self._check_ip_whitelist(target)
        return self._check_domain_whitelist(target)

    def add_site(self, site: str):
        """添加白名单网站"""
        site = site.strip()
        self._ensure_latest()
        if site not in self.white_sites:
            self.white_sites.append(site)
            self._save_sites()

    def add_ip_range(self, ip_range: str):
        """添加IP范围"""
        ip_range = ip_range.strip()
        self._ensure_latest()
        try:
            if '/' in ip_range:
                network = ipaddress.IPv4Network(ip_range, strict=False)
                if network not in self.ip_ranges:
                    self.ip_ranges.append(network)
                    self._save_sites()
            elif ' -> ' in ip_range:
                start_ip, end_ip = ip_range.split(' -> ')
                start_ip = start_ip.strip()
                end_ip = end_ip.strip()
                ip_tuple = (ipaddress.IPv4Address(start_ip), ipaddress.IPv4Address(end_ip))
                if ip_tuple not in self.ip_ranges_manual:
                    self.ip_ranges_manual.append(ip_tuple)
                    self._save_sites()
                    return True
        except Exception:
            return False
        return False

    def add_subdomain_pattern(self, domain: str):
        """添加子域名模式"""
        domain = domain.strip()
        self._ensure_latest()
        if domain not in self.subdomain_patterns:
            self.subdomain_patterns.append(domain)
            self._save_sites()

    def add_tld_pattern(self, tld: str):
        """添加顶级域名模式"""
        tld = tld.strip()
        self._ensure_latest()
        if tld not in self.tld_patterns:
            self.tld_patterns.append(tld)
            self._save_sites()

    def remove_site(self, site: str):
        """移除白名单网站"""
        site = site.strip()
        self._ensure_latest()
        if site in self.white_sites:
            self.white_sites.remove(site)
            self._save_sites()

    def _save_sites(self):
        """保存网站配置到文件"""
        config = AppConfigStore.get()
        entries = []

        entries.extend(self.white_sites)
        entries.extend([str(network) for network in self.ip_ranges])
        entries.extend([f"{start} -> {end}" for start, end in self.ip_ranges_manual])
        entries.extend([f"all>{pattern}" for pattern in self.subdomain_patterns])
        entries.extend([f"top>{tld}" for tld in self.tld_patterns])

        config["website_whitelist"] = entries
        AppConfigStore.save(config)
        self._config_version = AppConfigStore.version()
        return True

    def get_config_summary(self) -> dict:
        """获取配置摘要"""
        self._ensure_latest()
        return {
            'domains': self.white_sites.copy(),
            'ip_ranges': [str(network) for network in self.ip_ranges],
            'ip_ranges_manual': [f'{start} -> {end}' for start, end in self.ip_ranges_manual],
            'subdomain_patterns': self.subdomain_patterns.copy(),
            'tld_patterns': self.tld_patterns.copy()
        }


# 模块导出
__all__ = ['WebsiteWhitelistChecker']
