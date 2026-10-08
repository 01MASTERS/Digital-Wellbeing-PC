"""Extract, cache, and serve Windows application icons and website favicons."""

from __future__ import annotations

import io
import logging
import os
import shutil
import sys
import winreg
from pathlib import Path

from PIL import Image, ImageDraw

try:
    import win32con  # type: ignore[import-untyped]
    import win32gui  # type: ignore[import-untyped]
    import win32ui  # type: ignore[import-untyped]
    _WIN32_AVAILABLE = True
except ImportError:
    _WIN32_AVAILABLE = False

LOGGER = logging.getLogger(__name__)

_EXE_PATH_CACHE: dict[str, str] = {}
_MEMORY_ICON_CACHE: dict[str, bytes] = {}
_CACHE_DIR: Path | None = None

PALETTES = (
    ("#eeeaff", "#6c56cd"),
    ("#e5f6ee", "#2e9572"),
    ("#fff0e7", "#c77d4c"),
    ("#e9f3ff", "#5686ce"),
    ("#ffe8ef", "#bd6283"),
    ("#edf0f5", "#697587"),
)

SITE_COLORS: dict[str, tuple[str, str]] = {
    "youtube.com": ("#ffebee", "#cc0000"),
    "reddit.com": ("#fff3e0", "#ff4500"),
    "github.com": ("#f0f0f0", "#24292e"),
    "x.com": ("#f5f5f5", "#000000"),
    "twitter.com": ("#e1f5fe", "#1da1f2"),
    "google.com": ("#e8f0fe", "#4285f4"),
    "wikipedia.org": ("#f5f5f5", "#333333"),
    "stackoverflow.com": ("#fff3e0", "#f48024"),
    "netflix.com": ("#ffebee", "#e50914"),
    "spotify.com": ("#e8f5e9", "#1db954"),
    "discord.com": ("#ede7f6", "#5865f2"),
    "amazon.com": ("#fff8e1", "#ff9900"),
    "chatgpt.com": ("#e0f2f1", "#10a37f"),
    "claude.ai": ("#fbe9e7", "#d97757"),
}


def set_cache_directory(directory: Path) -> None:
    """Set on-disk directory for cached PNG icons."""
    global _CACHE_DIR
    _CACHE_DIR = directory / "icons"
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def record_app_exe(app_id: str, exe_path: str) -> None:
    """Associate an app_id with its resolved executable path."""
    if app_id and exe_path and os.path.isfile(exe_path):
        _EXE_PATH_CACHE[app_id.casefold()] = exe_path


def _get_cached_on_disk(filename: str) -> bytes | None:
    if _CACHE_DIR is None:
        return None
    file_path = _CACHE_DIR / filename
    if file_path.is_file() and file_path.stat().st_size > 0:
        try:
            return file_path.read_bytes()
        except OSError:
            return None
    return None


import ctypes
from ctypes import wintypes

try:
    import psutil
except ImportError:
    psutil = None


class _SHFILEINFOW(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80),
    ]


def _save_cached_on_disk(filename: str, data: bytes) -> None:
    if _CACHE_DIR is None or not data:
        return
    try:
        (_CACHE_DIR / filename).write_bytes(data)
    except OSError:
        LOGGER.debug("Could not write cached icon for %s", filename)


def _find_executable_path(app_id: str) -> str | None:
    clean_id = app_id.casefold().strip()
    exe_name = clean_id if clean_id.endswith(".exe") else f"{clean_id}.exe"
    base_name = clean_id[:-4] if clean_id.endswith(".exe") else clean_id

    # 1. Check memory cache
    for k in (clean_id, exe_name, base_name):
        if k in _EXE_PATH_CACHE:
            p = _EXE_PATH_CACHE[k]
            if os.path.exists(p):
                return p

    # 2. Check active running processes (handles Store apps, games, custom installs)
    if psutil is not None:
        try:
            for proc in psutil.process_iter(["name", "exe"]):
                pname = (proc.info.get("name") or "").casefold()
                if pname in (clean_id, exe_name, base_name):
                    pexe = proc.info.get("exe")
                    if pexe and os.path.isfile(pexe):
                        _EXE_PATH_CACHE[clean_id] = pexe
                        _EXE_PATH_CACHE[exe_name] = pexe
                        return pexe
        except Exception:
            pass

    # 3. Check App Paths registry
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for name in (exe_name, clean_id, base_name):
            try:
                with winreg.OpenKey(
                    root, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{name}", 0, winreg.KEY_READ
                ) as key:
                    val, _ = winreg.QueryValueEx(key, "")
                    if val:
                        clean_val = val.strip('"')
                        if os.path.isfile(clean_val):
                            _EXE_PATH_CACHE[clean_id] = clean_val
                            return clean_val
            except (OSError, FileNotFoundError):
                continue

    # 4. Check Windows Uninstall keys (finds DisplayIcon for installed software)
    uninstall_roots = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for u_root, u_sub in uninstall_roots:
        try:
            with winreg.OpenKey(u_root, u_sub) as key:
                count = winreg.QueryInfoKey(key)[0]
                for i in range(count):
                    try:
                        kname = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, kname) as subkey:
                            dicon = ""
                            try:
                                dicon, _ = winreg.QueryValueEx(subkey, "DisplayIcon")
                            except OSError:
                                pass
                            if dicon:
                                clean_icon = dicon.split(",")[0].strip('"').strip()
                                if (base_name in clean_icon.casefold() or clean_id in clean_icon.casefold()) and os.path.exists(clean_icon):
                                    _EXE_PATH_CACHE[clean_id] = clean_icon
                                    return clean_icon
                    except OSError:
                        continue
        except OSError:
            continue

    # 5. Check Start Menu shortcuts (.lnk files)
    start_roots = [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("ProgramData", ""), r"Microsoft\Windows\Start Menu\Programs"),
    ]
    for s_root in start_roots:
        if not os.path.isdir(s_root):
            continue
        try:
            for root_dir, _, files in os.walk(s_root):
                for f in files:
                    if f.casefold().endswith(".lnk"):
                        stem = f[:-4].casefold()
                        if stem in (clean_id, exe_name, base_name) or base_name == stem:
                            lnk_p = os.path.join(root_dir, f)
                            _EXE_PATH_CACHE[clean_id] = lnk_p
                            return lnk_p
        except OSError:
            pass

    # 6. Check PATH / which
    for name in (exe_name, clean_id, base_name):
        found = shutil.which(name)
        if found and os.path.isfile(found):
            _EXE_PATH_CACHE[clean_id] = found
            return found

    # 7. Check common directory candidates
    system_root = os.environ.get("SYSTEMROOT", r"C:\Windows")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_app_data = os.environ.get("LOCALAPPDATA", "")

    candidates = [
        os.path.join(system_root, "System32", exe_name),
        os.path.join(system_root, exe_name),
        os.path.join(system_root, "SysWOW64", exe_name),
        os.path.join(program_files, exe_name),
        os.path.join(program_files_x86, exe_name),
    ]
    if local_app_data:
        candidates.extend([
            os.path.join(local_app_data, "Microsoft", "WindowsApps", exe_name),
            os.path.join(local_app_data, "Programs", exe_name),
            os.path.join(local_app_data, "Programs", base_name, exe_name),
            os.path.join(local_app_data, "Programs", "Microsoft VS Code", exe_name),
            os.path.join(local_app_data, "Spotify", exe_name),
            os.path.join(local_app_data, "Discord", exe_name),
        ])
    if program_files:
        candidates.extend([
            os.path.join(program_files, "Google", "Chrome", "Application", exe_name),
            os.path.join(program_files, "Microsoft", "Edge", "Application", exe_name),
            os.path.join(program_files, "Mozilla Firefox", exe_name),
            os.path.join(program_files, "BraveSoftware", "Brave-Browser", "Application", exe_name),
            os.path.join(program_files, "VideoLAN", "VLC", exe_name),
        ])
    if program_files_x86:
        candidates.extend([
            os.path.join(program_files_x86, "Google", "Chrome", "Application", exe_name),
            os.path.join(program_files_x86, "Microsoft", "Edge", "Application", exe_name),
            os.path.join(program_files_x86, "Steam", exe_name),
        ])

    for candidate in candidates:
        if os.path.isfile(candidate):
            _EXE_PATH_CACHE[clean_id] = candidate
            return candidate

    return None


def _hicon_to_png(hicon: int, size: int = 48) -> bytes | None:
    if not _WIN32_AVAILABLE or not hicon:
        return None
    hdc_screen = None
    hdc = None
    memdc = None
    hbmp = None
    old_bmp = None
    try:
        hdc_screen = win32gui.GetDC(0)
        hdc = win32ui.CreateDCFromHandle(hdc_screen)
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, size, size)
        memdc = hdc.CreateCompatibleDC()
        old_bmp = memdc.SelectObject(hbmp)

        # Draw icon
        win32gui.DrawIconEx(memdc.GetSafeHdc(), 0, 0, hicon, size, size, 0, 0, win32con.DI_NORMAL)

        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer("RGBA", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, "raw", "BGRA", 0, 1)

        # Handle mask if alpha is completely 0
        _, _, _, a = img.split()
        extrema = a.getextrema()
        if extrema[1] == 0:
            try:
                info = win32gui.GetIconInfo(hicon)
                hbm_mask = info[3]
                hbm_color = info[4]
                hdc_m = win32ui.CreateDCFromHandle(hdc_screen)
                memdc_m = hdc_m.CreateCompatibleDC()
                hbmp_m = win32ui.CreateBitmap()
                hbmp_m.CreateCompatibleBitmap(hdc_m, size, size)
                old_m = memdc_m.SelectObject(hbmp_m)
                win32gui.DrawIconEx(memdc_m.GetSafeHdc(), 0, 0, hicon, size, size, 0, 0, win32con.DI_MASK)
                m_bits = hbmp_m.GetBitmapBits(True)
                mask_img = Image.frombuffer("RGBA", (size, size), m_bits, "raw", "BGRA", 0, 1).convert("L")
                alpha_ch = mask_img.point(lambda p: 0 if p > 128 else 255)
                img.putalpha(alpha_ch)
                memdc_m.SelectObject(old_m)
                memdc_m.DeleteDC()
                hdc_m.DeleteDC()
                win32gui.DeleteObject(hbmp_m.GetHandle())
                if hbm_mask:
                    win32gui.DeleteObject(hbm_mask)
                if hbm_color:
                    win32gui.DeleteObject(hbm_color)
            except (OSError, win32gui.error):
                img.putalpha(255)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception as error:
        LOGGER.debug("Failed to convert HICON to PNG: %s", error)
        return None
    finally:
        if memdc and old_bmp:
            try:
                memdc.SelectObject(old_bmp)
            except Exception:
                pass
        if memdc:
            try:
                memdc.DeleteDC()
            except Exception:
                pass
        if hdc:
            try:
                hdc.DeleteDC()
            except Exception:
                pass
        if hdc_screen:
            try:
                win32gui.ReleaseDC(0, hdc_screen)
            except Exception:
                pass
        if hbmp:
            try:
                win32gui.DeleteObject(hbmp.GetHandle())
            except Exception:
                pass


def _extract_icon_via_shell(file_path: str, size: int = 48) -> bytes | None:
    """Extract icon using Windows Shell (handles .lnk shortcuts, WindowsApps, etc.)."""
    if not os.path.exists(file_path):
        return None
    try:
        sfi = _SHFILEINFOW()
        res = ctypes.windll.shell32.SHGetFileInfoW(
            file_path,
            0,
            ctypes.byref(sfi),
            ctypes.sizeof(sfi),
            0x000000100,  # SHGFI_ICON
        )
        if not sfi.hIcon:
            return None
        try:
            return _hicon_to_png(sfi.hIcon, size)
        finally:
            ctypes.windll.user32.DestroyIcon(sfi.hIcon)
    except Exception as err:
        LOGGER.debug("Shell icon extraction failed for %s: %s", file_path, err)
        return None


def _extract_icon_from_file(exe_path: str, size: int = 48) -> bytes | None:
    if not os.path.exists(exe_path):
        return None
    if exe_path.lower().endswith(".lnk"):
        return _extract_icon_via_shell(exe_path, size)

    if _WIN32_AVAILABLE:
        large: list[int] = []
        small: list[int] = []
        try:
            large, small = win32gui.ExtractIconEx(exe_path, 0)
            hicon = large[0] if large else (small[0] if small else None)
            if hicon:
                png = _hicon_to_png(hicon, size)
                if png:
                    return png
        except (OSError, win32gui.error):
            pass
        finally:
            for h in large:
                try:
                    win32gui.DestroyIcon(h)
                except (OSError, win32gui.error):
                    pass
            for h in small:
                try:
                    win32gui.DestroyIcon(h)
                except (OSError, win32gui.error):
                    pass

    return _extract_icon_via_shell(exe_path, size)


def generate_fallback_svg(text: str, bg_color: str = "#eeeaff", ink_color: str = "#6c56cd") -> bytes:
    """Generate a clean SVG fallback avatar with the first letter."""
    letter = (text.strip()[:1] or "A").upper()
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="14" fill="{bg_color}"/>
  <text x="50%" y="54%" text-anchor="middle" dominant-baseline="middle"
        font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        font-size="22" font-weight="700" fill="{ink_color}">{letter}</text>
</svg>"""
    return svg.encode("utf-8")


def generate_fallback_png(text: str, bg_color: str = "#eeeaff", ink_color: str = "#6c56cd", size: int = 48) -> bytes:
    """Generate a clean rounded PNG fallback avatar."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 3.5, fill=bg_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def get_app_icon(app_id: str, size: int = 48) -> tuple[bytes, str]:
    """Retrieve PNG icon for an app ID.

    Returns (bytes, content_type).
    """
    clean_id = app_id.casefold()

    # 0. First-party Digital Wellbeing app icon
    if clean_id in {
        "digitalwellbeing.exe",
        "digitalwellbeing",
        "digital wellbeing",
        "digital_wellbeing.exe",
        "screen_time_tracker.exe",
    }:
        if getattr(sys, "frozen", False):
            root_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        else:
            root_dir = Path(__file__).resolve().parent.parent
        app_icon_path = root_dir / "assets" / "icon.png"
        if not app_icon_path.is_file():
            app_icon_path = root_dir / "digital_wellbeing" / "web" / "icon-512.png"
        if app_icon_path.is_file():
            try:
                master_img = Image.open(app_icon_path).convert("RGBA")
                resized_img = master_img.resize((size, size), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                resized_img.save(buf, format="PNG")
                png_data = buf.getvalue()
                _MEMORY_ICON_CACHE[clean_id] = png_data
                _save_cached_on_disk(f"{clean_id}.png", png_data)
                return png_data, "image/png"
            except (OSError, ValueError):
                pass

    # 1. Memory Cache
    if clean_id in _MEMORY_ICON_CACHE:
        return _MEMORY_ICON_CACHE[clean_id], "image/png"

    # 2. Disk Cache
    disk_data = _get_cached_on_disk(f"{clean_id}.png")
    if disk_data:
        _MEMORY_ICON_CACHE[clean_id] = disk_data
        return disk_data, "image/png"

    # 3. Locate executable and extract
    exe_path = _find_executable_path(clean_id)
    if exe_path:
        try:
            png_data = _extract_icon_from_file(exe_path, size)
            if png_data:
                _MEMORY_ICON_CACHE[clean_id] = png_data
                _save_cached_on_disk(f"{clean_id}.png", png_data)
                return png_data, "image/png"
        except Exception:
            pass

    # 4. Generate fallback icon
    hash_val = sum(ord(c) for c in clean_id)
    bg, ink = PALETTES[hash_val % len(PALETTES)]
    fallback = generate_fallback_svg(clean_id, bg, ink)
    return fallback, "image/svg+xml"


def get_site_icon(domain: str) -> tuple[bytes, str]:
    """Retrieve icon / favicon for a website domain.

    Returns (bytes, content_type).
    """
    clean_domain = domain.casefold().strip().rstrip(".")
    clean_domain = clean_domain.removeprefix("www.")

    # 1. Memory cache
    cache_key = f"site_{clean_domain}"
    if cache_key in _MEMORY_ICON_CACHE:
        return _MEMORY_ICON_CACHE[cache_key], "image/png"

    # 2. Disk cache
    disk_data = _get_cached_on_disk(f"{cache_key}.png")
    if disk_data:
        _MEMORY_ICON_CACHE[cache_key] = disk_data
        return disk_data, "image/png"

    # 3. Attempt to fetch high-res favicon from Google Favicon service
    try:
        import urllib.request
        url = f"https://www.google.com/s2/favicons?domain={clean_domain}&sz=64"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 DigitalWellbeing/1.0"})
        with urllib.request.urlopen(req, timeout=1.2) as resp:
            if resp.status == 200:
                data = resp.read()
                if len(data) > 100:
                    _MEMORY_ICON_CACHE[cache_key] = data
                    _save_cached_on_disk(f"{cache_key}.png", data)
                    return data, "image/png"
    except Exception:
        pass

    # 4. Fallback to clean colored vector SVG
    bg, ink = SITE_COLORS.get(clean_domain, (None, None))
    if not bg or not ink:
        hash_val = sum(ord(c) for c in clean_domain)
        bg, ink = PALETTES[hash_val % len(PALETTES)]

    first_letter = (clean_domain.split(".")[0][:1] or "W").upper()
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="14" fill="{bg}"/>
  <text x="50%" y="54%" text-anchor="middle" dominant-baseline="middle"
        font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        font-size="22" font-weight="700" fill="{ink}">{first_letter}</text>
</svg>"""
    return svg.encode("utf-8"), "image/svg+xml"
