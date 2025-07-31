import os
import re
import threading
import time
import ipaddress
from typing import List, Tuple, Set


class WebsiteWhitelistChecker:
    """网站白名单检查器

    支持多种白名单格式：
    - 普通域名: qq.com
    - IP网段: 1.1.1.0/24
    - IP范围: 3.4.5.6 -> 9.4.8.7
    - 子域名通配符: all>qq.com
    - 顶级域名通配符: top>.cn

    Args:
        config_file: 配置文件路径，默认为 'config/website-white.txt'
        auto_create: 是否自动创建配置文件，默认为 True
        file_watch: 是否启用文件监控，默认为 True
    """

    def __init__(self, config_file=None, auto_create=True, file_watch=True):
        self.config_file = config_file or DEFAULT_CONFIG_PATH
        self.auto_create = auto_create
        self.file_watch = file_watch
        self.white_sites = []
        self.ip_ranges = []
        self.ip_ranges_manual = []
        self.subdomain_patterns = []
        self.tld_patterns = []
        self.file_timestamp = 0
        self.lock = threading.Lock()
        self.url_patterns = [
            re.compile(r'https?://(?:www\.)?([a-zA-Z0-9.-]+)'),
            re.compile(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'),
            re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        ]
        self.load_sites()
        if self.file_watch:
            self.start_file_watcher()

    def load_sites(self):
        """加载白名单网站"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            with self.lock:
                self.white_sites = []
                self.ip_ranges = []
                self.ip_ranges_manual = []
                self.subdomain_patterns = []
                self.tld_patterns = []

                for line in lines:
                    self._parse_config_line(line)

                self.file_timestamp = os.path.getmtime(self.config_file)

        except FileNotFoundError:
            if self.auto_create:
                self._create_default_config()
            else:
                with self.lock:
                    self._reset_config()
        except Exception as e:
            print(f"加载白名单网站失败: {e}")
            with self.lock:
                self._reset_config()

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
                domain = line[4:].strip()
                self.subdomain_patterns.append(domain)
                return

            # 顶级域名模式: top>.cn
            if line.startswith('top>'):
                tld = line[4:].strip()
                self.tld_patterns.append(tld)
                return

            # 普通域名
            self.white_sites.append(line)

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

    def _create_default_config(self):
        """创建默认配置文件"""
        if not self.auto_create:
            return

        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        default_config = '''# 白名单网站配置文件
# 支持以下格式：

# 1. 普通域名
qq.com
baidu.com
b23.tv

# 2. IP网段 (CIDR格式)
1.1.1.0/24
192.168.1.0/24

# 3. IP范围
3.4.5.6 -> 9.4.8.7
10.0.0.1 -> 10.0.0.100

# 4. 子域名通配符 (包含所有子域名)
all>qq.com
all>google.com

# 5. 顶级域名通配符
top>.cn
top>.edu
'''
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write(default_config)

        with self.lock:
            self._reset_config()
            self.white_sites = ['qq.com', 'baidu.com', 'b23.tv']
            self.ip_ranges = [
                ipaddress.IPv4Network('1.1.1.0/24', strict=False),
                ipaddress.IPv4Network('192.168.1.0/24', strict=False)
            ]
            self.ip_ranges_manual = [
                (ipaddress.IPv4Address('3.4.5.6'), ipaddress.IPv4Address('9.4.8.7')),
                (ipaddress.IPv4Address('10.0.0.1'), ipaddress.IPv4Address('10.0.0.100'))
            ]
            self.subdomain_patterns = ['qq.com', 'google.com']
            self.tld_patterns = ['.cn', '.edu']

    def _reset_config(self):
        """重置配置"""
        self.white_sites = []
        self.ip_ranges = []
        self.ip_ranges_manual = []
        self.subdomain_patterns = []
        self.tld_patterns = []

    def start_file_watcher(self):
        """启动文件监控"""

        def watch_file():
            while True:
                try:
                    if os.path.exists(self.config_file):
                        current_mtime = os.path.getmtime(self.config_file)
                        if current_mtime != self.file_timestamp:
                            print("检测到白名单配置变更，重新加载...")
                            self.load_sites()
                except Exception as e:
                    # 静默处理监控错误，避免模块输出过多信息
                    pass
                time.sleep(10)

        threading.Thread(target=watch_file, daemon=True).start()

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
        domain = domain.lower()

        # 检查普通域名
        for white_site in self.white_sites:
            if white_site.lower() in domain:
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
        domains, ips = self.extract_domains_and_ips(message)
        all_targets = domains + ips

        if not all_targets:
            return True, []

        with self.lock:
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
        with self.lock:
            if self._is_ip_address(target):
                return self._check_ip_whitelist(target)
            else:
                return self._check_domain_whitelist(target)

    def add_site(self, site: str):
        """添加白名单网站"""
        site = site.strip()
        with self.lock:
            if site not in self.white_sites:
                self.white_sites.append(site)
                self._save_sites()

    def add_ip_range(self, ip_range: str):
        """添加IP范围"""
        ip_range = ip_range.strip()
        with self.lock:
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
            except Exception as e:
                return False
        return False

    def add_subdomain_pattern(self, domain: str):
        """添加子域名模式"""
        domain = domain.strip()
        with self.lock:
            if domain not in self.subdomain_patterns:
                self.subdomain_patterns.append(domain)
                self._save_sites()

    def add_tld_pattern(self, tld: str):
        """添加顶级域名模式"""
        tld = tld.strip()
        with self.lock:
            if tld not in self.tld_patterns:
                self.tld_patterns.append(tld)
                self._save_sites()

    def remove_site(self, site: str):
        """移除白名单网站"""
        site = site.strip()
        with self.lock:
            if site in self.white_sites:
                self.white_sites.remove(site)
                self._save_sites()

    def _save_sites(self):
        """保存网站配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write('# 白名单网站配置文件\n')
                f.write('# 支持以下格式：\n\n')

                if self.white_sites:
                    f.write('# 普通域名\n')
                    for site in self.white_sites:
                        f.write(f'{site}\n')
                    f.write('\n')

                if self.ip_ranges:
                    f.write('# IP网段\n')
                    for network in self.ip_ranges:
                        f.write(f'{network}\n')
                    f.write('\n')

                if self.ip_ranges_manual:
                    f.write('# IP范围\n')
                    for start_ip, end_ip in self.ip_ranges_manual:
                        f.write(f'{start_ip} -> {end_ip}\n')
                    f.write('\n')

                if self.subdomain_patterns:
                    f.write('# 子域名模式\n')
                    for pattern in self.subdomain_patterns:
                        f.write(f'all>{pattern}\n')
                    f.write('\n')

                if self.tld_patterns:
                    f.write('# 顶级域名模式\n')
                    for tld in self.tld_patterns:
                        f.write(f'top>{tld}\n')
                    f.write('\n')

            self.file_timestamp = os.path.getmtime(self.config_file)
            return True
        except Exception as e:
            print(f"保存白名单配置失败: {e}")

    def get_config_summary(self) -> dict:
        """获取配置摘要"""
        with self.lock:
            return {
                'domains': self.white_sites.copy(),
                'ip_ranges': [str(network) for network in self.ip_ranges],
                'ip_ranges_manual': [f'{start} -> {end}' for start, end in self.ip_ranges_manual],
                'subdomain_patterns': self.subdomain_patterns.copy(),
                'tld_patterns': self.tld_patterns.copy()
            }


# 模块导出
__all__ = ['WebsiteWhitelistChecker']

# 可选的模块级别配置
DEFAULT_CONFIG_PATH = 'config/website-white.txt'