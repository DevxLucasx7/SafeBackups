import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Dict, Any, Optional

class EmailNotifier:
    def __init__(
        self,
        email_remetente: str,
        senha_app: str,
        email_destinatario: str = "",
        servidor_smtp: str = "smtp.gmail.com",
        porta_smtp: int = 465
    ):
        self.email_remetente = email_remetente.strip()
        # Remove espaços que o Google às vezes gera na senha de app (ex: "abcd efgh ijkl mnop")
        self.senha_app = senha_app.strip().replace(" ", "")
        self.email_destinatario = (email_destinatario or email_remetente).strip()
        self.servidor_smtp = servidor_smtp.strip()
        self.porta_smtp = int(porta_smtp)

    def testar_credenciais(self) -> Tuple[bool, str]:
        """Testa se a autenticação SMTP com email e senha de app funciona."""
        if not self.email_remetente or not self.senha_app:
            return False, "E-mail ou Senha de App não preenchidos."

        try:
            contexto = ssl.create_default_context()
            if self.porta_smtp == 465:
                with smtplib.SMTP_SSL(self.servidor_smtp, self.porta_smtp, context=contexto, timeout=12) as server:
                    server.login(self.email_remetente, self.senha_app)
            else:
                with smtplib.SMTP(self.servidor_smtp, self.porta_smtp, timeout=12) as server:
                    server.starttls(context=contexto)
                    server.login(self.email_remetente, self.senha_app)
            return True, f"Autenticação SMTP confirmada com sucesso para {self.email_remetente}"
        except smtplib.SMTPAuthenticationError:
            return False, "Falha de autenticação: Verifique se o e-mail está correto e se a Senha de App foi gerada na conta Google."
        except Exception as e:
            return False, f"Erro ao conectar no servidor SMTP: {str(e)}"

    def enviar_relatorio_backup(
        self,
        sucesso_geral: bool,
        detalhes: Dict[str, Any],
        log_resumo: str = ""
    ) -> Tuple[bool, str]:
        """Envia um e-mail formatado com o relatório completo da rotina de backup."""
        if not self.email_remetente or not self.senha_app:
            return False, "Credenciais de e-mail não configuradas."

        status_tag = "✅ SUCESSO" if sucesso_geral else "❌ FALHA"
        assunto = f"[{status_tag}] Relatório de Backup - {detalhes.get('data_hora', '')}"

        cor_header = "#28a745" if sucesso_geral else "#dc3545"

        corpo_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
                .card {{ background-color: #ffffff; border-radius: 8px; padding: 25px; max-width: 650px; margin: 0 auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .header {{ background-color: {cor_header}; color: white; padding: 15px; border-radius: 6px; text-align: center; font-size: 18px; font-weight: bold; }}
                .section {{ margin-top: 20px; }}
                .item {{ padding: 8px 0; border-bottom: 1px solid #e9ecef; display: flex; justify-content: space-between; }}
                .item-label {{ font-weight: bold; color: #495057; }}
                .log-box {{ background-color: #212529; color: #f8f9fa; padding: 15px; border-radius: 6px; font-family: Consolas, monospace; font-size: 12px; max-height: 250px; overflow-y: auto; white-space: pre-wrap; margin-top: 15px; }}
                .footer {{ margin-top: 25px; text-align: center; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">{assunto}</div>
                <div class="section">
                    <div class="item"><span class="item-label">Status Geral:</span> <span>{'Concluído com Êxito' if sucesso_geral else 'Ocorreram Erros'}</span></div>
                    <div class="item"><span class="item-label">Data e Hora:</span> <span>{detalhes.get('data_hora', 'N/A')}</span></div>
                    <div class="item"><span class="item-label">Arquivo Gerado:</span> <span>{detalhes.get('arquivo_zip', 'N/A')}</span></div>
                    <div class="item"><span class="item-label">Tamanho:</span> <span>{detalhes.get('tamanho_mb', '0')} MB</span></div>
                    <div class="item"><span class="item-label">Storage Local (NAS):</span> <span>{detalhes.get('status_storage', 'Desativado')}</span></div>
                    <div class="item"><span class="item-label">Google Drive:</span> <span>{detalhes.get('status_gdrive', 'Desativado')}</span></div>
                </div>

                <div class="section">
                    <h4>Resumo dos Eventos:</h4>
                    <div class="log-box">{log_resumo or 'Sem mensagens adicionais.'}</div>
                </div>

                <div class="footer">
                    SafeBackup Windows &bull; Executado localmente no Servidor / Estação
                </div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = self.email_remetente
        msg["To"] = self.email_destinatario

        # Versão texto simples caso o cliente não suporte HTML
        texto_puro = f"Relatório de Backup\nStatus: {status_tag}\nData: {detalhes.get('data_hora')}\nArquivo: {detalhes.get('arquivo_zip')} ({detalhes.get('tamanho_mb')} MB)\nStorage: {detalhes.get('status_storage')}\nGoogle Drive: {detalhes.get('status_gdrive')}\n\nLogs:\n{log_resumo}"

        msg.attach(MIMEText(texto_puro, "plain", "utf-8"))
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        try:
            contexto = ssl.create_default_context()
            if self.porta_smtp == 465:
                with smtplib.SMTP_SSL(self.servidor_smtp, self.porta_smtp, context=contexto, timeout=20) as server:
                    server.login(self.email_remetente, self.senha_app)
                    server.sendmail(self.email_remetente, [self.email_destinatario], msg.as_string())
            else:
                with smtplib.SMTP(self.servidor_smtp, self.porta_smtp, timeout=20) as server:
                    server.starttls(context=contexto)
                    server.login(self.email_remetente, self.senha_app)
                    server.sendmail(self.email_remetente, [self.email_destinatario], msg.as_string())
            return True, f"Relatório enviado com sucesso para {self.email_destinatario}"
        except Exception as e:
            return False, f"Falha ao enviar e-mail de notificação: {str(e)}"
