import customtkinter as ctk
from tkinter import messagebox, filedialog
import requests
import json
import random
import re
import time
import os
import sys
import uuid
import threading
from datetime import datetime
from urllib.parse import quote, urlencode
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═════════════════════════════════════════════════════════
# CẤU HÌNH CHUNG
# ═════════════════════════════════════════════════════════
TIMEOUT = 120
TOTAL_PAGES_TARGET = 15
NEST_PROXY_KEY_FILE = 'nestproxykey.txt'

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ═════════════════════════════════════════════════════════
# MÀU SẮC
# ═════════════════════════════════════════════════════════
COLOR_BG          = "#080b10"
COLOR_BG_2        = "#0d1218"
COLOR_PANEL       = "#11171f"
COLOR_PANEL_2     = "#161d27"
COLOR_PANEL_3     = "#1e2733"
COLOR_PANEL_4     = "#252f3d"
COLOR_BORDER      = "#1f2937"
COLOR_BORDER_2    = "#2a3544"
COLOR_BORDER_3    = "#374151"

COLOR_SUCCESS     = "#22e07a"
COLOR_SUCCESS_2   = "#16a34a"
COLOR_ERROR       = "#ff5c5c"
COLOR_ERROR_2     = "#dc2626"
COLOR_WARNING     = "#fbbf24"
COLOR_INFO        = "#38bdf8"
COLOR_TEXT        = "#f1f5f9"
COLOR_TEXT_2      = "#cbd5e1"
COLOR_MUTED       = "#94a3b8"
COLOR_MUTED_2     = "#64748b"
COLOR_MUTED_3     = "#475569"

COLOR_ACCENT      = "#10b981"
COLOR_ACCENT_H    = "#34d399"
COLOR_BLUE        = "#3b82f6"
COLOR_BLUE_H      = "#60a5fa"
COLOR_RED         = "#ef4444"
COLOR_RED_H       = "#f87171"
COLOR_PURPLE      = "#8b5cf6"
COLOR_PURPLE_H    = "#a78bfa"

# ═════════════════════════════════════════════════════════
# USER AGENT GENERATOR
# ═════════════════════════════════════════════════════════
class UserAgentGenerator:
    BRANDS = ["Samsung", "Xiaomi", "OnePlus", "Google", "Motorola", "Nokia", "Sony", "LG", "Huawei", "Oppo", "Vivo", "Realme"]
    MODELS = {
        "Samsung": ["SM-S928B", "SM-S926B", "SM-S921B", "SM-G998B", "SM-G996B", "SM-G991B", "SM-A556B", "SM-A546B", "SM-A536B", "SM-A256B"],
        "Xiaomi": ["Xiaomi14", "Xiaomi13", "Xiaomi12", "Xiaomi11", "RedmiNote13", "RedmiNote12", "POCOX6", "POCOF5"],
        "OnePlus": ["OnePlus12", "OnePlus11", "OnePlus10", "OnePlus9"],
        "Google": ["Pixel 8 Pro", "Pixel 8", "Pixel 7 Pro", "Pixel 7", "Pixel 6 Pro"],
        "Motorola": ["Moto G84", "Moto G54", "Moto Edge 40"],
        "Nokia": ["Nokia G60", "Nokia X30", "Nokia G50"],
        "Sony": ["Xperia 5 IV", "Xperia 1 IV", "Xperia 5 III"],
        "LG": ["LG V60", "LG Wing", "LG Velvet"],
        "Huawei": ["Huawei P60", "Huawei P50", "Huawei Mate 60"],
        "Oppo": ["Oppo Find X6", "Oppo Find X5", "Oppo Reno11"],
        "Vivo": ["Vivo X90", "Vivo X80", "Vivo V29"],
        "Realme": ["Realme GT5", "Realme GT3", "Realme 12 Pro"]
    }
    CARRIERS = ["Viettel", "Vinaphone", "Mobifone", "Vietnamobile", "AT&T", "Verizon", "T-Mobile", "Vodafone", "Orange"]
    LOCALES = ["vi_VN", "en_US", "en_GB", "es_ES", "fr_FR", "de_DE", "pt_BR", "id_ID", "th_TH"]
    ANDROID_VERSIONS = [
        ("15", "AP3A.240905.015"), ("14", "UP1A.231005.007"), ("14", "UQ1A.231205.015"),
        ("13", "TQ3A.230901.001"), ("13", "TQ2A.230505.002"), ("12", "SP1A.210812.016"),
        ("12", "SQ3A.220705.003")
    ]
    FB_VERSIONS = [
        ("569", "0.0.42.72"), ("568", "0.0.40.68"), ("567", "0.0.38.65"),
        ("566", "0.0.35.58"), ("565", "0.0.33.52")
    ]

    @staticmethod
    def generate():
        brand = random.choice(UserAgentGenerator.BRANDS)
        model = random.choice(UserAgentGenerator.MODELS.get(brand, ["SM-S928B"]))
        carrier = random.choice(UserAgentGenerator.CARRIERS)
        locale = random.choice(UserAgentGenerator.LOCALES)
        android_ver, build = random.choice(UserAgentGenerator.ANDROID_VERSIONS)
        fb_ver, fb_build = random.choice(UserAgentGenerator.FB_VERSIONS)
        density = random.choice(["3.0", "2.75", "2.5"])
        width = random.choice([1080, 1440, 2340, 2400])
        height = random.choice([1920, 2340, 2400, 3120])
        return f"Dalvik/2.1.0 (Linux; U; Android {android_ver}; {model} Build/{build}) [FBAN/FB4A;FBAV/{fb_ver}.{fb_build};FBPN/com.facebook.katana;FBLC/{locale};FBBV/600000000;FBCR/{carrier};FBMF/{brand};FBBD/{brand};FBDV/{model};FBSV/{android_ver};FBCA/arm64-v8a;FBDM/{{density={density},width={width},height={height}}};FB_FW/1;FBRV/0;]"

# ═════════════════════════════════════════════════════════
# HẰNG SỐ BLOKS API
# ═════════════════════════════════════════════════════════
BLOKS_VERSION = "338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d"
DEFAULT_CATEGORY = "180164648685982"

# ═════════════════════════════════════════════════════════
# NEST PROXY
# ═════════════════════════════════════════════════════════
def load_nest_proxy_key():
    if os.path.exists(NEST_PROXY_KEY_FILE):
        with open(NEST_PROXY_KEY_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None

def save_nest_proxy_key(key):
    with open(NEST_PROXY_KEY_FILE, 'w', encoding='utf-8') as f:
        f.write(key.strip())

def get_nest_proxy(proxy_key):
    try:
        url = f"https://nestproxy.com/api/client/proxy/available?proxy_key={proxy_key}"
        response = requests.get(url, timeout=10)
        result = response.json()
        if 'proxy' in result:
            return {'success': True, 'proxy': result['proxy']}
        elif 'error' in result and result['error'] == 'TooManyRequests':
            return {'success': False, 'error': 'rate_limit', 'retry_after': result.get('retryAfter', 60)}
        else:
            return {'success': False, 'error': 'unknown', 'proxy': None}
    except Exception:
        return {'success': False, 'error': 'exception', 'proxy': None}

# ═════════════════════════════════════════════════════════
# TOKEN HELPERS
# ═════════════════════════════════════════════════════════
def extract_tokens_from_input(lines):
    tokens = []
    seen = set()
    patterns = [
        r'EAAAAU[a-zA-Z0-9%*_\-]+ZDZD',
        r'EAAAAY[a-zA-Z0-9%*_\-]+ZDZD',
        r'EAAD[a-zA-Z0-9%*_\-]+ZD(?:ZD)?',
    ]
    for line in lines:
        for pattern in patterns:
            for t in re.findall(pattern, line):
                t = t.strip()
                if t and t not in seen:
                    seen.add(t)
                    tokens.append(t)
    return tokens

def get_proxy_from_token_line(line):
    if '|' in line:
        parts = line.split('|')
        token = parts[0].strip()
        proxy_str = parts[1].strip() if len(parts) > 1 else None
        if proxy_str:
            proxy_parts = proxy_str.split(':')
            if len(proxy_parts) == 4:
                ip, port, user, password = proxy_parts
                return token, {
                    'http': f'http://{user}:{password}@{ip}:{port}',
                    'https': f'http://{user}:{password}@{ip}:{port}'
                }, proxy_str
            elif len(proxy_parts) == 2:
                ip, port = proxy_parts
                return token, {
                    'http': f'http://{ip}:{port}',
                    'https': f'http://{ip}:{port}'
                }, proxy_str
    return line.strip(), None, 'Không dùng proxy'

def count_pages(token):
    try:
        url = f"https://graph.facebook.com/v19.0/me/accounts?access_token={token}"
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            return len(response.json().get('data', []))
        return 0
    except Exception:
        return 0

def get_name_from_token(token):
    try:
        url = f"https://graph.facebook.com/me?fields=name,id&access_token={token}"
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            js = resp.json()
            if "error" not in js:
                return js.get("id"), js.get("name")
        return None, None
    except Exception:
        return None, None

def generate_random_name():
    ho = ["Nguyễn", "Trần", "Lê", "Phạm", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Trương", "Lưu", "Hà", "Cao", "Đinh"]
    tendemnam = ["Văn", "Hữu", "Minh", "Quang", "Đức", "Thanh", "Hoàng", "Ngọc", "Anh", "Gia", "Trung", "Khánh", "Việt", "Hải", "Tùng", "Tuấn", "Thành", "Chí", "Bảo", "Duy", "Công", "Trường", "Phúc", "Nhật", "Hồng", "Kiên", "Nam", "Phát", "Hùng", "Tấn", "Thái", "Đạt", "Tiến", "Khoa", "Vĩnh", "Quốc", "Thịnh", "Hoài", "Đông", "Nguyên", "Đình", "Khôi", "Nhân", "Quý", "Long", "Thiên", "Thế", "Vương", "Trọng", "Bình", "Cường", "Phương", "Xuân", "Dũng", "Tài", "Huy", "Thiện"]
    tendemnu = ["Thị", "Ngọc", "Thu", "Hồng", "Kim", "Lan", "Mai", "Thanh", "Bích", "Phương", "Thúy", "Vy", "Diệu", "Như", "Nguyệt", "Trang", "Hoài", "Trúc", "Quỳnh", "Yến", "Nhung", "Thảo", "Xuân", "Thùy", "Ngân", "Nhật", "Diễm", "Anh", "Thi", "Hà", "Minh", "Quyên", "Khánh", "Hạnh", "Ly", "Châu", "Bảo", "Trâm", "Uyên", "Diệp", "Thuý", "Tú"]
    tennam = ["An", "Bảo", "Cường", "Dũng", "Đức", "Hải", "Huy", "Khải", "Khánh", "Kiên", "Long", "Minh", "Nam", "Nguyên", "Nhân", "Phong", "Quang", "Quốc", "Sơn", "Thành", "Thiện", "Thọ", "Thịnh", "Tiến", "Tùng", "Tuấn", "Trường", "Trung", "Vinh", "Vũ", "Hưng", "Hoàng", "Đạt", "Đình", "Tài", "Vương", "Bình", "Thiên", "Phúc", "Ngọc", "Anh", "Chí", "Đông", "Hiếu", "Hùng", "Khang", "Kiệt", "Lâm", "Lộc", "Nhật", "Phát", "Phú", "Quyết", "Quân", "Sang", "Tân", "Thái", "Trọng", "Trí", "Vĩ", "Việt", "Vĩnh", "Xuân", "Yên", "Bằng", "Công", "Giang", "Hào", "Khôi", "Khoa", "Thắng", "Thiên"]
    tennu = ["Anh", "Bảo", "Châu", "Diệu", "Dung", "Giang", "Hà", "Hạnh", "Hằng", "Hồng", "Hoa", "Hoài", "Huệ", "Khánh", "Kiều", "Lan", "Linh", "Ly", "Mai", "Minh", "My", "Ngọc", "Nhung", "Nga", "Quỳnh", "Phương", "Thảo", "Thi", "Thủy", "Trang", "Trinh", "Trúc", "Uyên", "Vân", "Vy", "Xuân", "Yến"]
    gioi_tinh = random.choice(['nam', 'nu'])
    ho_chon = random.choice(ho)
    if gioi_tinh == 'nam':
        ten_dem = random.choice(tendemnam) if random.random() < 0.5 else ''
        ten = random.choice(tennam)
    else:
        ten_dem = random.choice(tendemnu) if random.random() < 0.5 else ''
        ten = random.choice(tennu)
    return f"{ho_chon} {ten_dem} {ten}".strip() if ten_dem else f"{ho_chon} {ten}"

# ═════════════════════════════════════════════════════════
# BLOKS API
# ═════════════════════════════════════════════════════════
def _build_variables(page_name: str) -> str:
    inner_params = (
        '{"client_input_params":{'
        '"page_id":"0","profile_plus_id":"0","cp_upsell_declined":0,'
        '"off_platform_creator_reachout_id":"",'
        f'"category_ids":["{DEFAULT_CATEGORY}"],'
        '"nav_chain":"..."'
        '},"server_params":{'
        '"referrer":"pages_tab_launch_point",'
        '"INTERNAL__latency_qpl_marker_id":36707139,'
        '"creation_source":"android",'
        f'"name":"{page_name}",'
        '"variant":5,"screen":"category",'
        '"INTERNAL__latency_qpl_instance_id":5.5098533200051e13'
        '}}'
    )
    outer_params = {
        "params": inner_params,
        "bloks_versioning_id": BLOKS_VERSION,
        "app_id": "com.bloks.www.additional.profile.plus.creation.action.category.submit",
    }
    nt_context = {
        "using_white_navbar": True,
        "styles_id": "588d028b36bed0e1889e09b60e0f9aea",
        "pixel_ratio": 2, "is_push_on": True,
        "debug_tooling_metadata_token": None,
        "is_flipper_enabled": False,
        "theme_params": [{"value": [], "design_system_name": "FDS"}],
        "bloks_version": BLOKS_VERSION,
    }
    return json.dumps({"params": outer_params, "scale": "2", "nt_context": nt_context})

def _decode_unicode(s):
    if not s: return s
    result = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 5 < len(s) and s[i+1] == 'u':
            try:
                result.append(chr(int(s[i+2:i+6], 16)))
                i += 6
                continue
            except ValueError:
                pass
        result.append(s[i])
        i += 1
    return "".join(result)

def _extract_action_string(js):
    try:
        data = js.get("data") or {}
        bloks_action = data.get("fb_bloks_action") or {}
        root_action = bloks_action.get("root_action") or {}
        action_obj = root_action.get("action") or {}
        bundle = action_obj.get("action_bundle") or {}
        bloks_str = bundle.get("bloks_bundle_action")
        if not bloks_str:
            bloks_str = data.get("bloks_bundle_action")
        if not bloks_str:
            raw = json.dumps(js)
            m = re.search(r'"bloks_bundle_action"\s*:\s*"((?:[^"\\]|\\.)+)"', raw)
            if m:
                bloks_str = m.group(1).encode().decode("unicode_escape")
        if not bloks_str:
            return None
        try:
            bloks_obj = json.loads(bloks_str)
        except Exception:
            bloks_str2 = bloks_str.replace('\\"', '"').replace("\\\\", "\\")
            bloks_obj = json.loads(bloks_str2)
        action = (bloks_obj.get("layout") or {}).get("bloks_payload", {}).get("action", "")
        if not action:
            action = bloks_obj.get("action", "")
        return action or None
    except Exception:
        return None

def _extract_id(action_str, js, field):
    pat1 = rf'\(bk\.action\.bloks\.WriteGlobalConsistencyStore,\s*"ADDITIONAL_PROFILE_PLUS_CREATION:{field}"\s*,\s*"(\d+)"\)'
    m = re.search(pat1, action_str)
    if m: return m.group(1)
    pat2 = rf'\(dq8\s+"ADDITIONAL_PROFILE_PLUS_CREATION:{field}"\s+"(\d+)"\)'
    m = re.search(pat2, action_str)
    if m: return m.group(1)
    raw = str(js)
    m = re.search(rf'"{field}"\s*[:=]\s*"?(\d{{6,}})"?', raw)
    if m: return m.group(1)
    return None

def _parse_response(js, page_name):
    try:
        action_str = _extract_action_string(js)
        if action_str is None:
            return False, None, "Vui lòng kiểm tra lại tài khoản fb"
        toast_match = re.search(r'\(bk\.action\.io\.Toast,\s*"([^"]+)"', action_str)
        if toast_match:
            return False, None, _decode_unicode(toast_match.group(1))
        if "create_error" in action_str:
            return False, None, "Tạo page thất bại (create_error)"
        if "profile_creation_error" in action_str:
            return False, None, "Lỗi tạo profile"
        page_id = _extract_id(action_str, js, "page_id")
        profile_plus = _extract_id(action_str, js, "profile_plus_id")
        page_uid = profile_plus or page_id
        if "create_success" in action_str or page_uid:
            return True, page_uid, None
        return False, None, f"Không tìm thấy page_id"
    except Exception as exc:
        return False, None, f"Lỗi parse: {exc}"

def create_facebook_page_token(token, page_name, proxy, user_agent):
    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent,
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"OAuth {token}",
    })
    if proxy:
        session.proxies = proxy
    data = {
        "method": "post", "pretty": "false", "format": "json",
        "server_timestamps": "true", "locale": "vi_VN",
        "client_doc_id": "119940804239956818821550724",
        "variables": _build_variables(page_name),
    }
    try:
        resp = session.post("https://graph.facebook.com/graphql",
                            data=urlencode(data), timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            session.close()
        except Exception:
            pass


# ═════════════════════════════════════════════════════════
# WORKER
# ═════════════════════════════════════════════════════════
class RegWorker:
    def __init__(self, tokens_data, proxy_mode, proxy_key, delay_min, delay_max,
                 log_callback, done_callback, update_table_callback,
                 countdown_callback=None, countdown_clear_callback=None):
        self.tokens_data = tokens_data
        self.proxy_mode = proxy_mode
        self.proxy_key = proxy_key
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.log = log_callback
        self.done = done_callback
        self.update_table = update_table_callback
        self.countdown = countdown_callback
        self.countdown_clear = countdown_clear_callback
        self.stop_flag = threading.Event()

    def stop(self):
        self.stop_flag.set()

    def check_token(self, data):
        token = data['token']
        idx = data['index']
        user_id, user_name = get_name_from_token(token)
        if not user_id or not user_name:
            self.log(f"Token #{idx} - DIE - BỎ QUA", "error")
            return None
        page_count = count_pages(token)
        pages_needed = TOTAL_PAGES_TARGET - page_count
        if pages_needed <= 0:
            self.log(f"Token #{idx} - {user_name} - {user_id} - {page_count} PAGE - ĐÃ ĐỦ {TOTAL_PAGES_TARGET} PAGE", "success")
            return None
        ua = UserAgentGenerator.generate()
        proxy_str = data.get('proxy_str', 'Không dùng proxy')
        self.log(f"Token #{idx} - {user_name} - {user_id} - {page_count} PAGE - REG THÊM {pages_needed} PAGE - {proxy_str}", "success")
        data.update({
            'user_id': user_id, 'user_name': user_name,
            'page_count': page_count, 'pages_needed': pages_needed,
            'user_agent': ua
        })
        return data

    def get_proxy_nest(self):
        while not self.stop_flag.is_set():
            result = get_nest_proxy(self.proxy_key)
            if self.stop_flag.is_set():
                return None, None
            if result['success']:
                proxy_str = result['proxy']
                parts = proxy_str.split(':')
                if len(parts) == 4:
                    ip, port, user, pw = parts
                    return {'http': f'http://{user}:{pw}@{ip}:{port}',
                            'https': f'http://{user}:{pw}@{ip}:{port}'}, proxy_str
                elif len(parts) == 2:
                    ip, port = parts
                    return {'http': f'http://{ip}:{port}',
                            'https': f'http://{ip}:{port}'}, proxy_str
            elif result.get('error') == 'rate_limit':
                wait = result.get('retry_after', 60)
                self.log(f"NEST PROXY - RATE LIMIT - ĐỢI {wait}S", "warning")
                for remaining in range(wait, 0, -1):
                    if self.stop_flag.is_set(): break
                    if self.countdown:
                        self.countdown(f"Nest Proxy rate limit - đợi {remaining} giây...")
                    time.sleep(1)
                if self.countdown_clear:
                    self.countdown_clear()
                continue
            else:
                self.log("LỖI LẤY PROXY - THỬ LẠI SAU 5S", "warning")
                for remaining in range(5, 0, -1):
                    if self.stop_flag.is_set(): break
                    if self.countdown:
                        self.countdown(f"Thử lại sau {remaining} giây...")
                    time.sleep(1)
                if self.countdown_clear:
                    self.countdown_clear()
        return None, None

    def reg_page(self, token_data, page_num, proxy_dict, proxy_str):
        if self.stop_flag.is_set():
            return False
        token = token_data['token']
        idx = token_data['index']
        user_name = token_data['user_name']
        ua = token_data['user_agent']
        page_name = generate_random_name()

        if self.proxy_mode == "token" and proxy_str and proxy_str != 'Không dùng proxy':
            self.log(f"Token #{idx} [{user_name}] tạo page: {page_name} - {proxy_str}", "info")
        else:
            self.log(f"Token #{idx} [{user_name}] tạo page: {page_name}", "info")

        js = create_facebook_page_token(token, page_name, proxy_dict, ua)
        if "error" in js and not isinstance(js.get("error"), dict):
            err = str(js.get("error", ""))
            self.log(f"Token #{idx}. TẠO THẤT BẠI - LỖI: {err}", "error")
            return False
        success, page_uid, err = _parse_response(js, page_name)
        if success:
            self.log(f"Token #{idx}. TẠO THÀNH CÔNG: {page_name} - {page_uid}", "success")
            return True
        else:
            self.log(f"Token #{idx}. TẠO THẤT BẠI - LỖI: {err}", "error")
            return False

    def run(self):
        try:
            sep = "─" * 60
            self.log(sep, "info")
            self.log("BẮT ĐẦU KIỂM TRA TOKEN...", "info")
            self.log(sep, "info")

            active = []
            with ThreadPoolExecutor(max_workers=min(len(self.tokens_data), 50) or 1) as ex:
                futures = [ex.submit(self.check_token, d) for d in self.tokens_data]
                for f in as_completed(futures):
                    try:
                        r = f.result()
                        if r: active.append(r)
                    except Exception:
                        pass

            if self.stop_flag.is_set():
                self.log("DỪNG BỞI NGƯỜI DÙNG", "warning")
                self.done()
                return

            if not active:
                self.log("KHÔNG CÓ TOKEN NÀO CẦN REG", "warning")
                self.done()
                return

            total_needed = sum(t['pages_needed'] for t in active)
            self.log(f"CÓ {len(active)} TOKEN CẦN REG, TỔNG CỘNG {total_needed} PAGE", "success")
            self.log(sep, "info")

            total_success = 0
            total_error = 0
            max_rounds = max(t['pages_needed'] for t in active)

            for round_num in range(1, max_rounds + 1):
                if self.stop_flag.is_set():
                    self.log("DỪNG BỞI NGƯỜI DÙNG", "warning")
                    break

                self.log(sep, "info")
                self.log(f"VÒNG {round_num}/{max_rounds}", "info")
                self.log(sep, "info")

                tasks = [(t, round_num) for t in active if t['pages_needed'] >= round_num]
                if not tasks:
                    continue

                if self.proxy_mode == 'nest':
                    self.log(f"ĐANG LẤY PROXY TỪ NEST PROXY CHO VÒNG {round_num}...", "info")
                    proxy_dict, proxy_str = self.get_proxy_nest()
                    if not proxy_dict:
                        break
                    self.log(f"PROXY VÒNG {round_num}: {proxy_str}", "success")

                    with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
                        futures = [ex.submit(self.reg_page, t, pn, proxy_dict, proxy_str) for t, pn in tasks]
                        for f in as_completed(futures):
                            try:
                                if f.result(): total_success += 1
                                else: total_error += 1
                            except Exception:
                                total_error += 1
                else:
                    with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
                        futures = []
                        for t, pn in tasks:
                            p_dict = t.get('proxy')
                            p_str = t.get('proxy_str', 'Không dùng proxy')
                            futures.append(ex.submit(self.reg_page, t, pn, p_dict, p_str))
                        for f in as_completed(futures):
                            try:
                                if f.result(): total_success += 1
                                else: total_error += 1
                            except Exception:
                                total_error += 1

                if self.stop_flag.is_set():
                    self.log("DỪNG BỞI NGƯỜI DÙNG", "warning")
                    break

                if round_num < max_rounds and not self.stop_flag.is_set():
                    wait = random.randint(self.delay_min, self.delay_max) if self.delay_max > 0 else self.delay_min
                    if wait > 0:
                        self.log(f"REG XONG VÒNG {round_num}/{max_rounds}, ĐỢI {wait}S ĐỂ REG TIẾP...", "info")
                        for remaining in range(wait, 0, -1):
                            if self.stop_flag.is_set():
                                break
                            if self.countdown:
                                self.countdown(f"Đợi {remaining} giây...")
                            time.sleep(1)
                        if self.countdown_clear:
                            self.countdown_clear()
                        if not self.stop_flag.is_set():
                            self.log(f"ĐÃ HẾT DELAY - TIẾP TỤC VÒNG {round_num + 1}", "success")

            if self.stop_flag.is_set():
                self.log("DỪNG BỞI NGƯỜI DÙNG", "warning")
                self.done()
                return

            self.log(sep, "info")
            self.log("ĐANG KIỂM TRA KẾT QUẢ CUỐI CÙNG...", "info")
            self.log(sep, "info")

            final = []
            def recheck(d):
                pc = count_pages(d['token'])
                uid, un = get_name_from_token(d['token'])
                return {'index': d['index'], 'name': un, 'id': uid, 'page_count': pc,
                        'status': 'ĐẠT' if pc >= TOTAL_PAGES_TARGET else 'CHƯA ĐẠT'}

            with ThreadPoolExecutor(max_workers=min(len(self.tokens_data), 50) or 1) as ex:
                futures = [ex.submit(recheck, d) for d in self.tokens_data]
                for f in as_completed(futures):
                    try:
                        r = f.result()
                        if r and r['id'] and r['name']:
                            final.append(r)
                    except Exception:
                        pass

            final.sort(key=lambda x: x['index'])
            self.update_table(final)

            self.log(sep, "info")
            self.log(f"TỔNG KẾT: {total_success} THÀNH CÔNG - {total_error} THẤT BẠI", "success")
            self.log(sep, "info")
            self.done()

        except Exception as e:
            self.log(f"LỖI WORKER: {e}", "error")
            self.done()


# ═════════════════════════════════════════════════════════
# MAIN GUI APP
# ═════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🚀 REG PAGE FACEBOOK TOKEN")
        self.geometry("1480x920")
        self.minsize(1320, 800)
        self.configure(fg_color=COLOR_BG)

        self.tokens_list = []
        self.proxy_mode = "nest"
        self.worker = None
        self.is_running = False

        self._countdown_active = False
        self._countdown_pos = None

        self._build_ui()

    def _build_ui(self):
        # ═══ HEADER ═══
        header = ctk.CTkFrame(self, fg_color=COLOR_PANEL, height=90, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        left_hdr = ctk.CTkFrame(header, fg_color="transparent")
        left_hdr.pack(side="left", padx=(25, 0), pady=15)

        logo_box = ctk.CTkFrame(left_hdr, fg_color=COLOR_PURPLE, width=52, height=52, corner_radius=14)
        logo_box.pack(side="left", padx=(0, 15))
        logo_box.pack_propagate(False)
        ctk.CTkLabel(logo_box, text="🚀", font=ctk.CTkFont(size=26)).pack(expand=True)

        title_block = ctk.CTkFrame(left_hdr, fg_color="transparent")
        title_block.pack(side="left")

        title_row = ctk.CTkFrame(title_block, fg_color="transparent")
        title_row.pack(anchor="w")

        ctk.CTkLabel(title_row, text="REG PAGE FACEBOOK",
                     font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_TEXT).pack(side="left")

        ctk.CTkLabel(title_block, text="Auto Reg Page  ·  v4.0",
                     font=ctk.CTkFont(size=11), text_color=COLOR_MUTED, anchor="w").pack(anchor="w", pady=(2, 0))

        right_hdr = ctk.CTkFrame(header, fg_color="transparent")
        right_hdr.pack(side="right", padx=25, pady=15)

        self.status_badge = ctk.CTkFrame(right_hdr, fg_color=COLOR_PANEL_3, corner_radius=22,
                                         border_width=1, border_color=COLOR_BORDER_2, height=42)
        self.status_badge.pack()

        self.status_icon = ctk.CTkLabel(self.status_badge, text="●", text_color=COLOR_MUTED_2,
                                        font=ctk.CTkFont(size=16))
        self.status_icon.pack(side="left", padx=(18, 6), pady=8)

        self.status_label = ctk.CTkLabel(self.status_badge, text="Sẵn sàng",
                                         text_color=COLOR_TEXT_2, font=ctk.CTkFont(size=13, weight="bold"))
        self.status_label.pack(side="left", padx=(0, 20), pady=8)

        # ═══ MAIN ═══
        main = ctk.CTkFrame(self, fg_color=COLOR_BG)
        main.pack(fill="both", expand=True, padx=20, pady=20)
        main.grid_columnconfigure(0, weight=0, minsize=420)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # ═══ LEFT PANEL ═══
        self.left_panel = ctk.CTkScrollableFrame(main, fg_color=COLOR_PANEL, width=420, corner_radius=16,
                                                 border_width=1, border_color=COLOR_BORDER)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        left = self.left_panel

        # ─ Card 0: Chọn chế độ Proxy
        self._card(left, "🌐", "CHẾ ĐỘ PROXY", "Chọn cách sử dụng proxy", COLOR_INFO)

        mode_row = ctk.CTkFrame(left, fg_color="transparent")
        mode_row.pack(fill="x", padx=20, pady=(10, 12))

        self.mode_nest_btn = ctk.CTkButton(
            mode_row, text="🔑  Nest Proxy", height=44,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_H,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=10, command=lambda: self._set_proxy_mode("nest"))
        self.mode_nest_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.mode_token_btn = ctk.CTkButton(
            mode_row, text="📌  Token|Proxy", height=44,
            fg_color=COLOR_PANEL_3, hover_color=COLOR_BORDER_2,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=10, command=lambda: self._set_proxy_mode("token"))
        self.mode_token_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Divider sau 2 nút mode
        self._divider(left)

        # ═══ DELAY SECTION (đóng vai trò mốc để proxy_card chèn trước) ═══
        self.delay_section = ctk.CTkFrame(left, fg_color="transparent")
        self.delay_section.pack(fill="x")

        # ═══ BUILD PROXY CARD — pack vào left TRƯỚC delay_section ═══
        self.proxy_card = None
        self._build_proxy_card()

        # ─ Card 2: Delay
        self._card(self.delay_section, "⏱️", "DELAY GIỮA CÁC VÒNG", "Random từ Min đến Max (giây)", COLOR_WARNING)

        delay_row = ctk.CTkFrame(self.delay_section, fg_color="transparent")
        delay_row.pack(fill="x", padx=20, pady=(10, 10))

        min_box = ctk.CTkFrame(delay_row, fg_color=COLOR_PANEL_2, corner_radius=10,
                               border_width=1, border_color=COLOR_BORDER_2)
        min_box.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkLabel(min_box, text="MIN", text_color=COLOR_MUTED,
                     font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=14, pady=(10, 0))

        self.delay_min_entry = ctk.CTkEntry(min_box, height=36, placeholder_text="300",
                                            fg_color=COLOR_BG_2, border_color=COLOR_BORDER,
                                            border_width=1, corner_radius=8,
                                            font=ctk.CTkFont(size=14, weight="bold"),
                                            text_color=COLOR_TEXT)
        self.delay_min_entry.pack(fill="x", padx=10, pady=(4, 10))
        self.delay_min_entry.insert(0, "300")

        max_box = ctk.CTkFrame(delay_row, fg_color=COLOR_PANEL_2, corner_radius=10,
                               border_width=1, border_color=COLOR_BORDER_2)
        max_box.pack(side="left", fill="x", expand=True, padx=(6, 0))

        ctk.CTkLabel(max_box, text="MAX", text_color=COLOR_MUTED,
                     font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=14, pady=(10, 0))

        self.delay_max_entry = ctk.CTkEntry(max_box, height=36, placeholder_text="500",
                                            fg_color=COLOR_BG_2, border_color=COLOR_BORDER,
                                            border_width=1, corner_radius=8,
                                            font=ctk.CTkFont(size=14, weight="bold"),
                                            text_color=COLOR_TEXT)
        self.delay_max_entry.pack(fill="x", padx=10, pady=(4, 10))
        self.delay_max_entry.insert(0, "500")

        self._divider(left)

        # ─ Card 3: Token
        self._card(left, "📋", "QUẢN LÝ TOKEN", "Thêm / xoá token", COLOR_ACCENT)

        badge_box = ctk.CTkFrame(left, fg_color=COLOR_PANEL_2, corner_radius=12,
                                 border_width=1, border_color=COLOR_BORDER_2)
        badge_box.pack(fill="x", padx=20, pady=(10, 12))

        badge_inner = ctk.CTkFrame(badge_box, fg_color="transparent")
        badge_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(badge_inner, text="TỔNG TOKEN", text_color=COLOR_MUTED,
                     font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")

        self.token_count_label = ctk.CTkLabel(badge_inner, text="0", text_color=COLOR_INFO,
                                              font=ctk.CTkFont(size=24, weight="bold"))
        self.token_count_label.pack(side="right")

        token_row = ctk.CTkFrame(left, fg_color="transparent")
        token_row.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(token_row, text="➕  Thêm", height=44,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_H,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      corner_radius=10, command=self._open_token_dialog
                      ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(token_row, text="🗑️  Xoá All", height=44,
                      fg_color=COLOR_RED, hover_color=COLOR_RED_H,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      corner_radius=10, command=self._clear_tokens
                      ).pack(side="left", fill="x", expand=True, padx=(5, 0))

        self._divider(left)

        # ─ Card 4: Action
        self._card(left, "▶️", "HÀNH ĐỘNG", "Bắt đầu / dừng tool", COLOR_PURPLE)

        self.start_btn = ctk.CTkButton(left, text="▶   BẮT ĐẦU CHẠY", height=56,
                                       fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_H,
                                       font=ctk.CTkFont(size=16, weight="bold"),
                                       corner_radius=12, command=self._start)
        self.start_btn.pack(fill="x", padx=20, pady=(10, 10))

        self.stop_btn = ctk.CTkButton(left, text="⏹   DỪNG", height=48,
                                      fg_color=COLOR_RED, hover_color=COLOR_RED_H,
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      corner_radius=12, state="disabled", command=self._stop)
        self.stop_btn.pack(fill="x", padx=20, pady=(0, 20))

        # ═══ RIGHT PANEL ═══
        right = ctk.CTkFrame(main, fg_color=COLOR_PANEL, corner_radius=16,
                             border_width=1, border_color=COLOR_BORDER)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=3)
        right.grid_rowconfigure(3, weight=2)
        right.grid_columnconfigure(0, weight=1)

        log_header = ctk.CTkFrame(right, fg_color="transparent", height=54)
        log_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 0))
        log_header.pack_propagate(False)

        log_left = ctk.CTkFrame(log_header, fg_color="transparent")
        log_left.pack(side="left", fill="y")

        icon_box = ctk.CTkFrame(log_left, fg_color=COLOR_PANEL_3, width=36, height=36, corner_radius=10)
        icon_box.pack(side="left", padx=(0, 10))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="🐛", font=ctk.CTkFont(size=18)).pack(expand=True)

        txt_box = ctk.CTkFrame(log_left, fg_color="transparent")
        txt_box.pack(side="left")
        ctk.CTkLabel(txt_box, text="DEBUG LOG", text_color=COLOR_TEXT,
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(txt_box, text="Nhật ký hoạt động", text_color=COLOR_MUTED,
                     font=ctk.CTkFont(size=10), anchor="w").pack(anchor="w")

        ctk.CTkButton(log_header, text="🗑️  Clear", width=100, height=36,
                      fg_color=COLOR_PANEL_3, hover_color=COLOR_BORDER_2,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      corner_radius=10, command=self._clear_log).pack(side="right", pady=9)

        log_wrapper = ctk.CTkFrame(right, fg_color=COLOR_BG_2, corner_radius=12,
                                   border_width=1, border_color=COLOR_BORDER)
        log_wrapper.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 14))

        self.log_box = ctk.CTkTextbox(log_wrapper, fg_color="transparent", border_width=0,
                                      font=ctk.CTkFont(family="Consolas", size=11),
                                      text_color=COLOR_TEXT_2, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=12, pady=12)

        self.log_box.tag_config("success", foreground=COLOR_SUCCESS)
        self.log_box.tag_config("error",   foreground=COLOR_ERROR)
        self.log_box.tag_config("warning", foreground=COLOR_WARNING)
        self.log_box.tag_config("info",    foreground=COLOR_INFO)
        self.log_box.tag_config("debug",   foreground=COLOR_MUTED)
        self.log_box.tag_config("countdown", foreground=COLOR_WARNING)

        table_header = ctk.CTkFrame(right, fg_color="transparent", height=54)
        table_header.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 0))
        table_header.pack_propagate(False)

        table_left = ctk.CTkFrame(table_header, fg_color="transparent")
        table_left.pack(side="left", fill="y")

        icon_box2 = ctk.CTkFrame(table_left, fg_color=COLOR_PANEL_3, width=36, height=36, corner_radius=10)
        icon_box2.pack(side="left", padx=(0, 10))
        icon_box2.pack_propagate(False)
        ctk.CTkLabel(icon_box2, text="📑", font=ctk.CTkFont(size=18)).pack(expand=True)

        txt_box2 = ctk.CTkFrame(table_left, fg_color="transparent")
        txt_box2.pack(side="left")
        ctk.CTkLabel(txt_box2, text="KẾT QUẢ CUỐI CÙNG", text_color=COLOR_TEXT,
             font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(txt_box2, text="Chi tiết từng token", text_color=COLOR_MUTED,
             font=ctk.CTkFont(size=10), anchor="w").pack(anchor="w")

        # ═══ Nút Clear bảng kết quả ═══
        ctk.CTkButton(table_header, text="🗑️  Clear", width=100, height=36,
                      fg_color=COLOR_PANEL_3, hover_color=COLOR_BORDER_2,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      corner_radius=10, command=self._clear_table).pack(side="right", pady=9)

        table_wrapper = ctk.CTkFrame(right, fg_color=COLOR_BG_2, corner_radius=12,
                                     border_width=1, border_color=COLOR_BORDER)
        table_wrapper.grid(row=3, column=0, sticky="nsew", padx=20, pady=(10, 20))

        self.table_frame = ctk.CTkScrollableFrame(table_wrapper, fg_color="transparent", corner_radius=10)
        self.table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self._render_table_header()

    # ═══════════ PROXY CARD BUILDER ═══════════
    def _build_proxy_card(self):
        """Build proxy card — pack vào left TRƯỚC delay_section"""
        self.proxy_card = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.proxy_card.pack(fill="x", before=self.delay_section)

        self._card(self.proxy_card, "🔑", "NEST PROXY KEY", "Nhập key để lấy proxy", COLOR_BLUE)

        self.proxy_key_entry = ctk.CTkEntry(self.proxy_card, placeholder_text="Nhập Nest Proxy Key...",
                                            height=46, font=ctk.CTkFont(size=13),
                                            fg_color=COLOR_BG_2, border_color=COLOR_BORDER_2,
                                            border_width=1, corner_radius=10,
                                            text_color=COLOR_TEXT, placeholder_text_color=COLOR_MUTED_2)
        self.proxy_key_entry.pack(fill="x", padx=20, pady=(10, 12))

        saved_key = load_nest_proxy_key()
        if saved_key:
            self.proxy_key_entry.insert(0, saved_key)

        proxy_row = ctk.CTkFrame(self.proxy_card, fg_color="transparent")
        proxy_row.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(proxy_row, text="💾  Lưu Key", height=40,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_H,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      corner_radius=10, command=self._save_key
                      ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(proxy_row, text="🧪  Test", height=40,
                      fg_color=COLOR_BLUE, hover_color=COLOR_BLUE_H,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      corner_radius=10, command=self._test_key
                      ).pack(side="left", fill="x", expand=True, padx=(5, 0))

        divider1 = ctk.CTkFrame(self.proxy_card, fg_color=COLOR_BORDER, height=1)
        divider1.pack(fill="x", padx=20, pady=12)

    # ═══════════ MODE PROXY ═══════════
    def _set_proxy_mode(self, mode):
        if self.proxy_mode == mode:
            return

        self.proxy_mode = mode

        if mode == "nest":
            self.mode_nest_btn.configure(fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_H)
            self.mode_token_btn.configure(fg_color=COLOR_PANEL_3, hover_color=COLOR_BORDER_2)
            # DESTROY proxy_card cũ (nếu có) → build lại
            if self.proxy_card is not None and self.proxy_card.winfo_exists():
                self.proxy_card.destroy()
            self.proxy_card = None
            self._build_proxy_card()
            self.log("[MODE] Đã chuyển sang chế độ NEST PROXY", "info")
        else:
            self.mode_nest_btn.configure(fg_color=COLOR_PANEL_3, hover_color=COLOR_BORDER_2)
            self.mode_token_btn.configure(fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_H)
            # DESTROY proxy_card — biến mất hoàn toàn, không chiếm chỗ
            if self.proxy_card is not None and self.proxy_card.winfo_exists():
                self.proxy_card.destroy()
            self.proxy_card = None
            self.log("[MODE] Đã chuyển sang chế độ TOKEN|PROXY", "info")

    # ═══════════ UI HELPERS ═══════════
    def _card(self, parent, icon, title, subtitle=None, accent=None):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.pack(fill="x", padx=20, pady=(16, 4))

        icon_box = ctk.CTkFrame(box, fg_color=accent or COLOR_PANEL_3, width=32, height=32, corner_radius=9)
        icon_box.pack(side="left", padx=(0, 10))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=ctk.CTkFont(size=15)).pack(expand=True)

        txt = ctk.CTkFrame(box, fg_color="transparent")
        txt.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(txt, text=title, text_color=COLOR_TEXT,
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(txt, text=subtitle, text_color=COLOR_MUTED,
                         font=ctk.CTkFont(size=10), anchor="w").pack(anchor="w")

    def _divider(self, parent):
        line = ctk.CTkFrame(parent, fg_color=COLOR_BORDER, height=1)
        line.pack(fill="x", padx=20, pady=12)

    def _save_key(self):
        if self.proxy_card is None or not self.proxy_card.winfo_exists():
            return
        key = self.proxy_key_entry.get().strip()
        if not key:
            messagebox.showwarning("Cảnh báo", "Key rỗng")
            return
        save_nest_proxy_key(key)
        self.log("[CONFIG] Đã lưu key Nest Proxy", "success")
        messagebox.showinfo("OK", "Đã lưu key")

    def _test_key(self):
        if self.proxy_card is None or not self.proxy_card.winfo_exists():
            return
        key = self.proxy_key_entry.get().strip()
        if not key:
            messagebox.showwarning("Cảnh báo", "Chưa nhập key")
            return
        self.log("[CONFIG] Đang test key...", "info")

        def _test():
            r = get_nest_proxy(key)
            if r['success']:
                self.log(f"[CONFIG] OK - Proxy: {r['proxy']}", "success")
            elif r.get('error') == 'rate_limit':
                self.log(f"[CONFIG] Rate limit, đợi {r.get('retry_after', 60)}s", "warning")
            else:
                self.log("[CONFIG] Key không hợp lệ", "error")

        threading.Thread(target=_test, daemon=True).start()

    def _open_token_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("➕ THÊM TOKEN")
        dialog.geometry("820x680")
        dialog.configure(fg_color=COLOR_BG)
        dialog.transient(self)
        dialog.grab_set()

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 820) // 2
        y = self.winfo_y() + (self.winfo_height() - 680) // 2
        dialog.geometry(f"+{x}+{y}")

        hdr = ctk.CTkFrame(dialog, fg_color=COLOR_PANEL, height=80, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="both", expand=True, padx=28, pady=16)

        icon_box = ctk.CTkFrame(hdr_inner, fg_color=COLOR_ACCENT, width=40, height=40, corner_radius=11)
        icon_box.pack(side="left", padx=(0, 14))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="📋", font=ctk.CTkFont(size=20)).pack(expand=True)

        hdr_txt = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        hdr_txt.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(hdr_txt, text="THÊM TOKEN FACEBOOK",
                     font=ctk.CTkFont(size=16, weight="bold"), text_color=COLOR_TEXT, anchor="w").pack(anchor="w")

        subtitle = ("Mỗi dòng 1 token · Hỗ trợ EAAAAU, EAAAAY, EAAD"
                    if self.proxy_mode == "nest"
                    else "Mỗi dòng: token|ip:port:user:pass hoặc token|ip:port")
        ctk.CTkLabel(hdr_txt, text=subtitle,
                     font=ctk.CTkFont(size=11), text_color=COLOR_MUTED, anchor="w").pack(anchor="w", pady=(2, 0))

        text_container = ctk.CTkFrame(dialog, fg_color="transparent")
        text_container.pack(fill="both", expand=True, padx=24, pady=(20, 10))

        textbox = ctk.CTkTextbox(text_container, fg_color=COLOR_PANEL, border_color=COLOR_BORDER,
                                 border_width=1, font=ctk.CTkFont(family="Consolas", size=12),
                                 text_color=COLOR_TEXT, corner_radius=12)
        textbox.pack(fill="both", expand=True)

        bottom = ctk.CTkFrame(dialog, fg_color="transparent", height=64)
        bottom.pack(fill="x", padx=24, pady=(0, 22))
        bottom.pack_propagate(False)

        counter_box = ctk.CTkFrame(bottom, fg_color=COLOR_PANEL_3, corner_radius=10,
                                    border_width=1, border_color=COLOR_BORDER_2)
        counter_box.pack(side="left", padx=(0, 10), pady=10)

        counter_label = ctk.CTkLabel(counter_box, text="Số token: 0",
                                     text_color=COLOR_INFO, font=ctk.CTkFont(size=12, weight="bold"))
        counter_label.pack(padx=16, pady=8)

        def update_count(*args):
            content = textbox.get("1.0", "end").strip()
            lines = [l for l in content.split("\n") if l.strip()]
            tokens = extract_tokens_from_input(lines)
            cnt = len(tokens) if tokens else len(lines)
            counter_label.configure(text=f"Số token: {cnt}")

        textbox.bind("<KeyRelease>", update_count)

        def _paste():
            try:
                clip = self.clipboard_get()
                textbox.insert("end", clip + "\n")
                update_count()
            except Exception:
                pass

        def _clear():
            textbox.delete("1.0", "end")
            update_count()

        def _add():
            content = textbox.get("1.0", "end").strip()
            if not content:
                messagebox.showwarning("Cảnh báo", "Chưa nhập token")
                return
            lines = [l for l in content.split("\n") if l.strip()]

            added = 0
            if self.proxy_mode == "nest":
                tokens = extract_tokens_from_input(lines)
                if not tokens:
                    tokens = lines
                existing = set(self.tokens_list)
                for t in tokens:
                    t = t.strip()
                    if t and t not in existing:
                        self.tokens_list.append(t)
                        existing.add(t)
                        added += 1
            else:
                existing = set(self.tokens_list)
                for line in lines:
                    line = line.strip()
                    if not line or line in existing:
                        continue
                    tokens = extract_tokens_from_input([line])
                    if tokens:
                        self.tokens_list.append(line)
                        existing.add(line)
                        added += 1

            self._update_token_count()
            self.log(f"[TOKEN] Đã thêm {added} token - Tổng: {len(self.tokens_list)}", "success")
            dialog.destroy()

        ctk.CTkButton(bottom, text="📋  Dán", width=110, height=44,
                      fg_color=COLOR_PANEL_3, hover_color=COLOR_BORDER_2,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      corner_radius=10, command=_paste).pack(side="left", padx=0, pady=10)

        ctk.CTkButton(bottom, text="🗑️  Xoá", width=100, height=44,
                      fg_color=COLOR_RED, hover_color=COLOR_RED_H,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      corner_radius=10, command=_clear).pack(side="left", padx=(10, 0), pady=10)

        ctk.CTkButton(bottom, text="➕  THÊM", width=150, height=44,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_H,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      corner_radius=10, command=_add).pack(side="right", padx=(10, 0), pady=10)

        ctk.CTkButton(bottom, text="✖  Đóng", width=100, height=44,
                      fg_color=COLOR_PANEL_3, hover_color=COLOR_BORDER_2,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      corner_radius=10, command=dialog.destroy).pack(side="right", padx=0, pady=10)

        textbox.focus_set()

    def _clear_tokens(self):
        if not self.tokens_list:
            return
        if messagebox.askyesno("Xác nhận", f"Xoá tất cả {len(self.tokens_list)} token?"):
            self.tokens_list.clear()
            self._update_token_count()
            self.log("[TOKEN] Đã xoá tất cả token", "warning")

    def _update_token_count(self):
        self.token_count_label.configure(text=str(len(self.tokens_list)))

    def _start(self):
        if self.is_running:
            return

        if self.proxy_mode == "nest":
            if self.proxy_card is None or not self.proxy_card.winfo_exists():
                messagebox.showerror("Lỗi", "Card Nest Proxy Key bị lỗi")
                return
            proxy_key = self.proxy_key_entry.get().strip()
            if not proxy_key:
                messagebox.showerror("Lỗi", "Chưa nhập Nest Proxy Key")
                return
        else:
            proxy_key = None

        if not self.tokens_list:
            messagebox.showerror("Lỗi", "Chưa có token")
            return

        try:
            dmin = int(self.delay_min_entry.get().strip() or "300")
            dmax = int(self.delay_max_entry.get().strip() or "500")
            if dmin < 0 or dmax < 0 or dmin > dmax:
                raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi", "Delay không hợp lệ! (Min >= 0, Min <= Max)")
            return

        tokens_data = []
        for idx, line in enumerate(self.tokens_list, 1):
            if self.proxy_mode == "token":
                token, proxy, proxy_str = get_proxy_from_token_line(line)
                tokens_data.append({
                    'index': idx,
                    'token': token,
                    'proxy': proxy,
                    'proxy_str': proxy_str
                })
            else:
                token = extract_tokens_from_input([line])
                token = token[0] if token else line.strip()
                tokens_data.append({
                    'index': idx,
                    'token': token,
                    'proxy': None,
                    'proxy_str': 'Nest Proxy'
                })

        if self.proxy_mode == "nest":
            save_nest_proxy_key(proxy_key)

        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text="Đang chạy", text_color=COLOR_SUCCESS)
        self.status_icon.configure(text_color=COLOR_SUCCESS)

        self._clear_log()
        self._clear_table()
        self._countdown_active = False

        mode_name = "NEST PROXY" if self.proxy_mode == "nest" else "TOKEN|PROXY"
        self.log("[START] " + "─" * 60, "info")
        self.log(f"[START] BẮT ĐẦU - Mode: {mode_name} - {len(self.tokens_list)} token - Delay {dmin}-{dmax}s", "info")
        self.log("[START] " + "─" * 60, "info")

        self.worker = RegWorker(
            tokens_data=tokens_data,
            proxy_mode=self.proxy_mode,
            proxy_key=proxy_key,
            delay_min=dmin,
            delay_max=dmax,
            log_callback=self.log,
            done_callback=self._on_done,
            update_table_callback=self._render_table_data,
            countdown_callback=self.log_countdown,
            countdown_clear_callback=self.log_clear_last,
        )

        threading.Thread(target=self.worker.run, daemon=True).start()

    def _stop(self):
        if self.worker:
            self.worker.stop()
            self.log("[STOP] Đang dừng... chờ task hiện tại xong", "warning")
            self.stop_btn.configure(state="disabled")
            self.status_label.configure(text="Đang dừng...", text_color=COLOR_WARNING)
            self.status_icon.configure(text_color=COLOR_WARNING)

    def _on_done(self):
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="Hoàn thành", text_color=COLOR_SUCCESS)
        self.status_icon.configure(text_color=COLOR_SUCCESS)

    def log(self, msg, level="info"):
        def _append():
            ts = datetime.now().strftime("%H:%M:%S")
            icons = {"success": "✓", "error": "✗", "warning": "⚠", "info": "ℹ", "debug": "→"}
            icon = icons.get(level, "→")
            line = f"[{ts}] {icon} {msg}\n"

            start = self.log_box.index("end-1c")
            self.log_box.insert("end", line)
            end = self.log_box.index("end-1c")
            self.log_box.tag_add(level, start, end)
            self.log_box.see("end")

        if threading.current_thread() is threading.main_thread():
            _append()
        else:
            self.after(0, _append)

    def log_countdown(self, msg):
        def _do():
            ts = datetime.now().strftime("%H:%M:%S")
            new_line = f"[{ts}] ⏳ {msg}"

            if self._countdown_active and self._countdown_pos:
                try:
                    self.log_box.delete(self._countdown_pos, "end-1c")
                except Exception:
                    pass

            self.log_box.insert("end", new_line + "\n")
            self._countdown_pos = self.log_box.index("end-2l linestart")
            self._countdown_active = True

            start = self.log_box.index("end-2l linestart")
            end = self.log_box.index("end-1c")
            self.log_box.tag_add("countdown", start, end)
            self.log_box.see("end")

        if threading.current_thread() is threading.main_thread():
            _do()
        else:
            self.after(0, _do)

    def log_clear_last(self):
        def _do():
            if self._countdown_active and self._countdown_pos:
                try:
                    self.log_box.delete(self._countdown_pos, "end-1c")
                except Exception:
                    pass
            self._countdown_active = False
            self._countdown_pos = None

        if threading.current_thread() is threading.main_thread():
            _do()
        else:
            self.after(0, _do)

    def _clear_log(self):
        self.log_box.delete("1.0", "end")
        self._countdown_active = False
        self._countdown_pos = None

    def _clear_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
        self._render_table_header()

    def _render_table_header(self):
        headers = [("STT", 30), ("Tên FB", 230), ("UID", 200), ("PAGE", 80), ("TRẠNG THÁI", 100)]
        row = ctk.CTkFrame(self.table_frame, fg_color=COLOR_PANEL_3, corner_radius=10, height=42)
        row.pack(fill="x", pady=(0, 6))
        row.pack_propagate(False)
        for text, w in headers:
            ctk.CTkLabel(row, text=text, width=w, text_color=COLOR_INFO,
                         font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(side="left", padx=8, pady=10)

    def _render_table_data(self, data_list):
        def _render():
            self._clear_table()
            if not data_list:
                ctk.CTkLabel(self.table_frame, text="(Không có kết quả)",
                             text_color=COLOR_MUTED, font=ctk.CTkFont(size=12)).pack(pady=24)
                return

            for i, r in enumerate(data_list):
                bg = COLOR_PANEL_2 if i % 2 == 0 else COLOR_BG_2
                row = ctk.CTkFrame(self.table_frame, fg_color=bg, corner_radius=8, height=38)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)

                pc = r['page_count']
                color = COLOR_SUCCESS if pc >= TOTAL_PAGES_TARGET else COLOR_ERROR
                status_txt = f"● {r['status']}"

                values = [
                    (str(r['index']), 30, COLOR_MUTED),
                    (r['name'][:28], 230, COLOR_TEXT),
                    (r['id'], 200, COLOR_MUTED_2),
                    (str(pc), 80, COLOR_TEXT),
                    (status_txt, 100, color),
                ]
                for text, w, c in values:
                    ctk.CTkLabel(row, text=text, width=w, text_color=c,
                                 font=ctk.CTkFont(size=11), anchor="w").pack(side="left", padx=8, pady=8)

        if threading.current_thread() is threading.main_thread():
            _render()
        else:
            self.after(0, _render)


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        pass