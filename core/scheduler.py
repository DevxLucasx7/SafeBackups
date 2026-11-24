import os
import sys
import subprocess
from typing import Tuple

class WindowsScheduler:
    @staticmethod
    def obter_comando_execucao() -> Tuple[str, str]:
        """Retorna o executável e os argumentos para rodar o backup silencioso."""
        if getattr(sys, 'frozen', False):
            # Rodando empacotado como .exe
            exe_path = sys.executable
            args = "--silent"
            return f'"{exe_path}"', args
        else:
            # Rodando via python interpretado
            python_exe = sys.executable
            main_script = os.path.abspath("main.py")
            return f'"{python_exe}"', f'"{main_script}" --silent'

    @staticmethod
    def criar_tarefa(nome_tarefa: str, hora_hhmm: str) -> Tuple[bool, str]:
        """Cria ou atualiza a tarefa agendada no Windows."""
        exe, args = WindowsScheduler.obter_comando_execucao()
        comando_completo = f"{exe} {args}"
        
        # schtasks /create /tn "NomeTarefa" /tr "comando" /sc daily /st HH:MM /f /rl HIGHEST
        cmd = [
            "schtasks", "/create",
            "/tn", nome_tarefa,
            "/tr", comando_completo,
            "/sc", "DAILY",
            "/st", hora_hhmm,
            "/f",
            "/rl", "HIGHEST"
        ]

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

            res = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            if res.returncode == 0:
                return True, f"Tarefa '{nome_tarefa}' agendada com sucesso para rodar diariamente às {hora_hhmm}."
            else:
                return False, f"Falha ao agendar tarefa: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Erro ao executar schtasks: {str(e)}"

    @staticmethod
    def remover_tarefa(nome_tarefa: str) -> Tuple[bool, str]:
        """Remove a tarefa do Agendador de Tarefas do Windows."""
        cmd = ["schtasks", "/delete", "/tn", nome_tarefa, "/f"]
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

            res = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            if res.returncode == 0 or "não foi encontrada" in res.stderr.lower():
                return True, f"Tarefa '{nome_tarefa}' removida com sucesso."
            else:
                return False, f"Falha ao remover tarefa: {res.stderr.strip()}"
        except Exception as e:
            return False, f"Erro: {str(e)}"

    @staticmethod
    def verificar_tarefa(nome_tarefa: str) -> bool:
        """Verifica se a tarefa já está registrada no Windows."""
        cmd = ["schtasks", "/query", "/tn", nome_tarefa]
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            res = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            return res.returncode == 0
        except Exception:
            return False
