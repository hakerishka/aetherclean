"""
Windows System Restore Point creation helper for AetherClean.
"""

import subprocess
import ctypes
from typing import Tuple


class RestorePointManager:
    """Invokes PowerShell or WMI to create a System Restore Point before deep cleaning."""

    @staticmethod
    def is_admin() -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @classmethod
    def create_restore_point(cls, description: str = "AetherClean - Перед очисткой диска") -> Tuple[bool, str]:
        """Creates a Windows System Restore Point."""
        if not cls.is_admin():
            return False, "Требуются права Администратора для создания Точки восстановления."

        # PowerShell command to enable SystemRestore on C: and create checkpoint
        ps_cmd = (
            f'Enable-ComputerRestore -Drive "C:\\" -ErrorAction SilentlyContinue; '
            f'Checkpoint-Computer -Description "{description}" -RestorePointType "MODIFY_SETTINGS"'
        )

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=45
            )

            if result.returncode == 0:
                return True, "Точка восстановления успешно создана."
            else:
                err_msg = result.stderr.strip() or result.stdout.strip()
                if "frequency" in err_msg.lower() or "limit" in err_msg.lower():
                    # Windows enforces 24h limit between automatic restore points by default
                    return True, "Точка восстановления уже создана недавно (ограничение частоты Windows)."
                return False, f"Ошибка создания точки восстановления: {err_msg}"

        except subprocess.TimeoutExpired:
            return False, "Таймаут при создании точки восстановления Windows."
        except Exception as e:
            return False, f"Исключение при вызове PowerShell: {str(e)}"
