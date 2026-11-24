import os
import shutil
from datetime import datetime, timedelta
from typing import Tuple, Optional, Callable

class GoogleDriveManager:
    def __init__(self, metodo: str, pasta_id_ou_caminho: str, arquivo_credenciais: str = ""):
        self.metodo = metodo or "pasta_desktop"
        self.pasta_id_ou_caminho = pasta_id_ou_caminho.strip()
        self.arquivo_credenciais = arquivo_credenciais.strip()

    def testar_conexao(self) -> Tuple[bool, str]:
        """Testa a conexão ou acessibilidade da pasta do Google Drive."""
        if not self.pasta_id_ou_caminho:
            return False, "Pasta de destino do Google Drive não configurada."

        if self.metodo == "pasta_desktop" or os.path.exists(self.pasta_id_ou_caminho):
            # Teste de escrita em pasta do Drive no Windows (ex: G:\Meu Drive\CFTV ou C:\...\Google Drive)
            if not os.path.isdir(self.pasta_id_ou_caminho):
                try:
                    os.makedirs(self.pasta_id_ou_caminho, exist_ok=True)
                except Exception as e:
                    return False, f"A pasta informada não existe e não pôde ser criada: {e}"

            arquivo_teste = os.path.join(self.pasta_id_ou_caminho, f"__test_gdrive_{datetime.now().strftime('%H%M%S')}.tmp")
            try:
                with open(arquivo_teste, "w") as f:
                    f.write("teste_ok")
                if os.path.exists(arquivo_teste):
                    os.remove(arquivo_teste)
                return True, f"Pasta do Google Drive acessível e com permissão de escrita: {self.pasta_id_ou_caminho}"
            except Exception as e:
                return False, f"Falha ao gravar na pasta do Google Drive: {str(e)}"

        elif self.metodo == "api_service_account":
            if not self.arquivo_credenciais or not os.path.exists(self.arquivo_credenciais):
                return False, f"Arquivo de credenciais JSON do Google não encontrado: {self.arquivo_credenciais}"
            return True, "Arquivo de credenciais JSON validado. Pronto para integração via API."

        return False, "Método de Google Drive não reconhecido ou caminho inválido."

    def enviar_arquivo(
        self,
        caminho_arquivo_local: str,
        callback_progresso: Optional[Callable[[int, int, int], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None
    ) -> Tuple[bool, str]:
        """Envia o arquivo ZIP para o destino do Google Drive."""
        if not os.path.isfile(caminho_arquivo_local):
            return False, f"Arquivo de backup não encontrado: {caminho_arquivo_local}"

        nome_arquivo = os.path.basename(caminho_arquivo_local)

        # Modo 1: Pasta do Google Drive para Desktop / Unidade Virtual G:
        if self.metodo == "pasta_desktop" or os.path.isdir(self.pasta_id_ou_caminho):
            try:
                os.makedirs(self.pasta_id_ou_caminho, exist_ok=True)
                destino_final = os.path.join(self.pasta_id_ou_caminho, nome_arquivo)
                
                tamanho_total = os.path.getsize(caminho_arquivo_local)
                copiados = 0
                bloco_tam = 1024 * 1024 * 4  # 4 MB

                with open(caminho_arquivo_local, "rb") as fsrc, open(destino_final, "wb") as fdst:
                    while True:
                        if is_cancelled and is_cancelled():
                            fdst.close()
                            if os.path.exists(destino_final):
                                try:
                                    os.remove(destino_final)
                                except OSError:
                                    pass
                            return False, "Envio para o Google Drive cancelado pelo usuário."

                        bloco = fsrc.read(bloco_tam)
                        if not bloco:
                            break
                        fdst.write(bloco)
                        copiados += len(bloco)
                        if callback_progresso:
                            pct = int((copiados / tamanho_total) * 100) if tamanho_total > 0 else 100
                            callback_progresso(pct, copiados, tamanho_total)

                tamanho_mb = tamanho_total / (1024 * 1024)
                return True, f"Copiado para Google Drive ({self.pasta_id_ou_caminho}) - {tamanho_mb:.2f} MB"
            except Exception as e:
                return False, f"Erro ao copiar para a pasta do Google Drive: {str(e)}"

        # Modo 2: API Google Drive (se bibliotecas externas estiverem disponíveis)
        elif self.metodo == "api_service_account":
            try:
                # Tentativa de carregar google-api-python-client se instalado
                from googleapiclient.discovery import build
                from googleapiclient.http import MediaFileUpload
                from google.oauth2 import service_account

                creds = service_account.Credentials.from_service_account_file(
                    self.arquivo_credenciais,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                service = build('drive', 'v3', credentials=creds)

                file_metadata = {'name': nome_arquivo}
                if self.pasta_id_ou_caminho:
                    file_metadata['parents'] = [self.pasta_id_ou_caminho]

                media = MediaFileUpload(caminho_arquivo_local, mimetype='application/zip', resumable=True)
                request = service.files().create(body=file_metadata, media_body=media, fields='id')
                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status and callback_progresso:
                        pct = int(status.progress() * 100)
                        callback_progresso(pct, int(status.resumable_progress), int(status.total_size))

                return True, f"Upload concluído no Google Drive via API (ID: {response.get('id')})"
            except ImportError:
                return False, "Para usar a API direta do Drive, instale: pip install google-api-python-client google-auth. Ou utilize a opção 'Pasta Sincronizada do Google Drive'."
            except Exception as e:
                return False, f"Erro na API do Google Drive: {str(e)}"

        return False, "Método de envio do Google Drive não suportado."

    def limpar_antigos(self, prefixo: str, dias_retencao: int) -> int:
        """Remove arquivos de backup antigos na pasta do Google Drive."""
        if dias_retencao <= 0 or not os.path.isdir(self.pasta_id_ou_caminho):
            return 0
        removidos = 0
        try:
            limite = datetime.now() - timedelta(days=dias_retencao)
            for item in os.listdir(self.pasta_id_ou_caminho):
                if item.startswith(prefixo) and item.endswith(".zip"):
                    caminho = os.path.join(self.pasta_id_ou_caminho, item)
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
