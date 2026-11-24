import os
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import Tuple, Optional

class LocalStorageManager:
    def __init__(self, ip: str, compartilhamento: str, usuario: str, senha: str, dominio: str = ""):
        self.ip = ip.strip().replace("/", "\\").strip("\\")
        self.compartilhamento = compartilhamento.strip().replace("/", "\\").strip("\\")
        self.usuario = usuario.strip()
        self.senha = senha
        self.dominio = dominio.strip()
        self.unc_base = f"\\\\{self.ip}\\{self.compartilhamento}"

    def montar_comando_net_use(self) -> list:
        user_param = f"{self.dominio}\\{self.usuario}" if self.dominio else self.usuario
        # net use \\IP\Share senha /user:usuario /persistent:no
        cmd = ["net", "use", self.unc_base]
        if self.senha:
            cmd.append(self.senha)
        if user_param:
            cmd.extend([f"/user:{user_param}"])
        cmd.append("/persistent:no")
        return cmd

    def conectar(self) -> Tuple[bool, str]:
        """Autentica na pasta de rede do Storage/NAS usando credenciais."""
        if not self.ip or not self.compartilhamento:
            return False, "IP ou Compartilhamento não configurados."

        try:
            # Primeiro tenta desconectar qualquer sessão anterior travada
            self.desconectar()

            cmd = self.montar_comando_net_use()
            # Executa oculto
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                startupinfo=startupinfo
            )

            if res.returncode == 0 or "já existem conexões múltiplas" in res.stderr.lower():
                return True, f"Conexão com {self.unc_base} estabelecida com sucesso."
            else:
                erro_msg = res.stderr.strip() or res.stdout.strip() or f"Código de erro {res.returncode}"
                return False, f"Falha na conexão SMB: {erro_msg}"
        except subprocess.TimeoutExpired:
            return False, f"Tempo limite excedido ao tentar conectar no IP {self.ip}."
        except Exception as e:
            return False, f"Erro inesperado ao conectar no Storage: {str(e)}"

    def desconectar(self) -> None:
        """Encerra a conexão montada via net use."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            subprocess.run(
                ["net", "use", self.unc_base, "/delete", "/yes"],
                capture_output=True,
                timeout=5,
                startupinfo=startupinfo
            )
        except Exception:
            pass

    def testar_conexao(self) -> Tuple[bool, str]:
        """Testa se consegue conectar e tem permissão de escrita."""
        sucesso, msg = self.conectar()
        if not sucesso:
            return False, msg

        arquivo_teste = os.path.join(self.unc_base, f"__test_safebackup_write_{datetime.now().strftime('%H%M%S')}.tmp")
        try:
            with open(arquivo_teste, "w") as f:
                f.write("teste_permissao_ok")
            if os.path.exists(arquivo_teste):
                os.remove(arquivo_teste)
            return True, f"Conexão e permissão de escrita confirmadas em {self.unc_base}"
        except Exception as e:
            return False, f"Conexão autenticou, mas falhou ao gravar arquivo: {str(e)}"

    def enviar_arquivo(self, caminho_arquivo_local: str, callback_progresso=None, is_cancelled=None) -> Tuple[bool, str]:
        """Copia o arquivo de backup para o Storage Local."""
        if not os.path.isfile(caminho_arquivo_local):
            return False, f"Arquivo local não existe: {caminho_arquivo_local}"

        sucesso, msg = self.conectar()
        if not sucesso:
            return False, msg

        nome_arquivo = os.path.basename(caminho_arquivo_local)
        destino_remoto = os.path.join(self.unc_base, nome_arquivo)

        try:
            tamanho_total = os.path.getsize(caminho_arquivo_local)
            copiados = 0
            bloco_tam = 1024 * 1024 * 4  # 4 MB por bloco

            with open(caminho_arquivo_local, "rb") as fsrc, open(destino_remoto, "wb") as fdst:
                while True:
                    if is_cancelled and is_cancelled():
                        fdst.close()
                        if os.path.exists(destino_remoto):
                            try:
                                os.remove(destino_remoto)
                            except OSError:
                                pass
                        return False, "Envio para o Storage Local cancelado pelo usuário."

                    bloco = fsrc.read(bloco_tam)
                    if not bloco:
                        break
                    fdst.write(bloco)
                    copiados += len(bloco)
                    if callback_progresso:
                        pct = int((copiados / tamanho_total) * 100) if tamanho_total > 0 else 100
                        callback_progresso(pct, copiados, tamanho_total)

            tamanho_mb = tamanho_total / (1024 * 1024)
            return True, f"Arquivo copiado para {destino_remoto} ({tamanho_mb:.2f} MB)"
        except Exception as e:
            return False, f"Erro durante a transferência para o Storage: {str(e)}"

    def limpar_antigos(self, prefixo: str, dias_retencao: int) -> int:
        """Remove backups antigos no storage de acordo com os dias de retenção."""
        if dias_retencao <= 0:
            return 0
        removidos = 0
        try:
            if not os.path.exists(self.unc_base):
                return 0
            limite = datetime.now() - timedelta(days=dias_retencao)
            for item in os.listdir(self.unc_base):
                if item.startswith(prefixo) and item.endswith(".zip"):
                    caminho = os.path.join(self.unc_base, item)
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(caminho))
                        if mtime < limite:
                            os.remove(caminho)
                            removidos += 1
                    except Exception:
                        pass
        except Exception:
            pass
        return removidos
