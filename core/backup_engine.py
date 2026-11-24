import os
import sys
import logging
from datetime import datetime
from typing import Callable, Optional, Dict, Any

from core.config_manager import ConfigManager
from core.zip_manager import ZipManager
from core.storage_manager import LocalStorageManager
from core.gdrive_manager import GoogleDriveManager
from core.email_notifier import EmailNotifier

class BackupEngine:
    def __init__(self, config_manager: ConfigManager, log_callback: Optional[Callable[[str], None]] = None):
        self.config_mgr = config_manager
        self.log_callback = log_callback
        self.config = self.config_mgr.load_config()
        self._cancelado = False
        self.setup_logging()

    def cancelar(self):
        """Solicita o cancelamento imediato da rotina de backup."""
        self._cancelado = True
        self.log("Cancelamento solicitado pelo usuário. Interrompendo...", "WARNING")

    def foi_cancelado(self) -> bool:
        return self._cancelado

    def setup_logging(self):
        log_dir = os.path.abspath("logs")
        os.makedirs(log_dir, exist_ok=True)
        nome_log = f"backup_{datetime.now().strftime('%Y-%m')}.log"
        self.log_file = os.path.join(log_dir, nome_log)

        self.logger = logging.getLogger("SafeBackup")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            fh = logging.FileHandler(self.log_file, encoding="utf-8")
            fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            fh.setFormatter(fmt)
            self.logger.addHandler(fh)

    def log(self, mensagem: str, level: str = "INFO"):
        prefix = f"[{level}] " if level != "INFO" else ""
        texto = f"{prefix}{mensagem}"
        if level == "ERROR":
            self.logger.error(mensagem)
        elif level == "WARNING":
            self.logger.warning(mensagem)
        else:
            self.logger.info(mensagem)

        if self.log_callback:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_callback(f"[{timestamp}] {texto}")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {texto}")

    def executar_backup_completo(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> bool:
        """Executa toda a rotina de backup: ZIP -> Storage Local -> Google Drive -> Notificação."""
        inicio = datetime.now()
        data_hora_str = inicio.strftime("%Y-%m-%d %H:%M:%S")
        self.log("=" * 60)
        self.log(f"Iniciando rotina de Backup: {data_hora_str}")

        # Recarrega config fresca
        self.config = self.config_mgr.load_config()
        cfg_origem = self.config.get("origem", {})
        cfg_storage = self.config.get("storage_local", {})
        cfg_gdrive = self.config.get("google_drive", {})
        cfg_email = self.config.get("notificacao_email", {})

        caminho_origem = cfg_origem.get("caminho", r"C:\CFTV")
        padrao_arquivos = cfg_origem.get("padrao_arquivos", "*.*")
        prefixo_zip = cfg_origem.get("prefixo_zip", "BKP_CFTV")
        retencao_local = cfg_origem.get("retencao_dias_local", 7)

        # 1. Pasta temporária local para os arquivos ZIP
        pasta_temp_local = os.path.abspath("temp_backups")
        os.makedirs(pasta_temp_local, exist_ok=True)
        nome_arquivo_zip = ZipManager.gerar_nome_zip(prefixo_zip)
        caminho_zip_completo = os.path.join(pasta_temp_local, nome_arquivo_zip)

        if progress_callback:
            progress_callback(5, "Compactando arquivos de origem em ZIP...")

        self.log(f"Origem apontada: {caminho_origem}")
        self.log(f"Gerando arquivo compactado: {caminho_zip_completo}")

        # Execução da Compactação
        def callback_zip(atual, total, item_nome):
            if progress_callback and total > 0:
                pct = int(5 + (atual / total) * 35)  # 5% a 40%
                progress_callback(pct, f"Compactando ({atual}/{total}): {item_nome[:30]}")

        sucesso_zip, msg_zip, total_arquivos, tamanho_bytes = ZipManager.criar_backup_zip(
            origem_dir=caminho_origem,
            destino_zip_path=caminho_zip_completo,
            padrao_filtro=padrao_arquivos,
            callback_progresso=callback_zip,
            is_cancelled=self.foi_cancelado
        )

        if self.foi_cancelado():
            self.log("Backup CANCELADO com sucesso pelo usuário.", "WARNING")
            if progress_callback:
                progress_callback(0, "Operação cancelada pelo usuário.")
            return False

        if not sucesso_zip:
            self.log(f"FALHA na compactação: {msg_zip}", "ERROR")
            self._finalizar_com_erro(data_hora_str, msg_zip, cfg_email)
            return False

        tamanho_mb = round(tamanho_bytes / (1024 * 1024), 2)
        self.log(f"{msg_zip}")

        # 2. Envio para Storage Local (NAS / SMB)
        status_storage = "Desativado"
        sucesso_storage = True
        if cfg_storage.get("habilitado", True):
            if self.foi_cancelado():
                return False

            if progress_callback:
                progress_callback(40, "Conectando e enviando para o Storage Local...")
            self.log(f"Conectando ao Storage Local: {cfg_storage.get('ip')} \\ {cfg_storage.get('compartilhamento')}")

            sm = LocalStorageManager(
                ip=cfg_storage.get("ip", ""),
                compartilhamento=cfg_storage.get("compartilhamento", ""),
                usuario=cfg_storage.get("usuario", ""),
                senha=cfg_storage.get("senha", ""),
                dominio=cfg_storage.get("dominio", "")
            )

            def callback_storage_prog(pct, cop, tot):
                if progress_callback:
                    p = int(40 + (pct * 0.30))  # 40% a 70%
                    progress_callback(p, f"Enviando ao Storage: {pct}%")

            sucesso_sm, msg_sm = sm.enviar_arquivo(
                caminho_zip_completo,
                callback_progresso=callback_storage_prog,
                is_cancelled=self.foi_cancelado
            )

            if self.foi_cancelado():
                self.log("Envio para Storage cancelado pelo usuário.", "WARNING")
                return False

            if sucesso_sm:
                self.log(f"Storage Local: {msg_sm}")
                status_storage = f"OK ({tamanho_mb} MB)"
                # Limpeza de retenção no storage
                dias_ret_st = cfg_storage.get("retencao_dias", 30)
                removidos = sm.limpar_antigos(prefixo_zip, dias_ret_st)
                if removidos > 0:
                    self.log(f"Storage: {removidos} backups com mais de {dias_ret_st} dias foram removidos.")
            else:
                self.log(f"FALHA Storage Local: {msg_sm}", "ERROR")
                status_storage = f"FALHA ({msg_sm})"
                sucesso_storage = False

        # 3. Envio para Google Drive
        status_gdrive = "Desativado"
        sucesso_gdrive = True
        if cfg_gdrive.get("habilitado", True):
            if self.foi_cancelado():
                return False

            if progress_callback:
                progress_callback(70, "Enviando arquivo para o Google Drive...")
            self.log(f"Iniciando envio para Google Drive (Destino: {cfg_gdrive.get('pasta_id_ou_caminho')})")

            gm = GoogleDriveManager(
                metodo=cfg_gdrive.get("metodo", "pasta_desktop"),
                pasta_id_ou_caminho=cfg_gdrive.get("pasta_id_ou_caminho", ""),
                arquivo_credenciais=cfg_gdrive.get("arquivo_credenciais_json", "")
            )

            def callback_gdrive_prog(pct, cop, tot):
                if progress_callback:
                    p = int(70 + (pct * 0.25))  # 70% a 95%
                    progress_callback(p, f"Enviando Google Drive: {pct}%")

            sucesso_gm, msg_gm = gm.enviar_arquivo(
                caminho_zip_completo,
                callback_progresso=callback_gdrive_prog,
                is_cancelled=self.foi_cancelado
            )

            if self.foi_cancelado():
                self.log("Envio para Google Drive cancelado pelo usuário.", "WARNING")
                return False
            if sucesso_gm:
                self.log(f"Google Drive: {msg_gm}")
                status_gdrive = f"OK ({tamanho_mb} MB)"
                dias_ret_gd = cfg_gdrive.get("retencao_dias", 60)
                rem_gd = gm.limpar_antigos(prefixo_zip, dias_ret_gd)
                if rem_gd > 0:
                    self.log(f"Google Drive: {rem_gd} backups com mais de {dias_ret_gd} dias removidos.")
            else:
                self.log(f"FALHA Google Drive: {msg_gm}", "ERROR")
                status_gdrive = f"FALHA ({msg_gm})"
                sucesso_gdrive = False

        # 4. Limpeza de ZIPs antigos no disco local
        rem_local = ZipManager.limpar_backups_antigos(pasta_temp_local, prefixo_zip, retencao_local)
        if rem_local > 0:
            self.log(f"Disco local C: {rem_local} arquivos temporários antigos foram excluídos.")

        duracao_total = round((datetime.now() - inicio).total_seconds(), 1)
        sucesso_geral = sucesso_zip and sucesso_storage and sucesso_gdrive

        if progress_callback:
            progress_callback(98, "Enviando relatório e finalizando...")

        # 5. Notificação por E-mail (Gmail com Senha de App)
        if cfg_email.get("habilitado", False):
            deve_notificar = True
            if cfg_email.get("notificar_apenas_em_erro", False) and sucesso_geral:
                deve_notificar = False

            if deve_notificar:
                notifier = EmailNotifier(
                    email_remetente=cfg_email.get("email_remetente", ""),
                    senha_app=cfg_email.get("senha_app", ""),
                    email_destinatario=cfg_email.get("email_destinatario", ""),
                    servidor_smtp=cfg_email.get("servidor_smtp", "smtp.gmail.com"),
                    porta_smtp=cfg_email.get("porta_smtp", 465)
                )
                detalhes = {
                    "data_hora": data_hora_str,
                    "arquivo_zip": nome_arquivo_zip,
                    "tamanho_mb": tamanho_mb,
                    "status_storage": status_storage,
                    "status_gdrive": status_gdrive
                }
                resumo_logs = f"Tempo de execução: {duracao_total}s\nOrigem: {caminho_origem}\nStorage: {status_storage}\nGoogle Drive: {status_gdrive}"
                ok_email, msg_email = notifier.enviar_relatorio_backup(sucesso_geral, detalhes, resumo_logs)
                if ok_email:
                    self.log(f"E-mail: {msg_email}")
                else:
                    self.log(f"E-mail: {msg_email}", "WARNING")

        if progress_callback:
            progress_callback(100, "Backup finalizado com sucesso!" if sucesso_geral else "Backup finalizado com alertas!")

        self.log(f"Rotina finalizada em {duracao_total}s. Status geral: {'SUCESSO' if sucesso_geral else 'COM FALHAS'}")
        self.log("=" * 60)
        return sucesso_geral

    def _finalizar_com_erro(self, data_hora: str, erro_msg: str, cfg_email: Dict[str, Any]):
        if cfg_email.get("habilitado", False):
            try:
                notifier = EmailNotifier(
                    email_remetente=cfg_email.get("email_remetente", ""),
                    senha_app=cfg_email.get("senha_app", ""),
                    email_destinatario=cfg_email.get("email_destinatario", "")
                )
                detalhes = {
                    "data_hora": data_hora,
                    "arquivo_zip": "Não gerado",
                    "tamanho_mb": 0,
                    "status_storage": "Abortado",
                    "status_gdrive": "Abortado"
                }
                notifier.enviar_relatorio_backup(False, detalhes, f"Erro crítico na rotina: {erro_msg}")
            except Exception:
                pass
