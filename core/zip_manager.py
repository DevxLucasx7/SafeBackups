import os
import zipfile
import fnmatch
from datetime import datetime, timedelta
from typing import Callable, Optional, Tuple, List

class ZipManager:
    @staticmethod
    def gerar_nome_zip(prefixo: str = "BKP_SISTEMA") -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        return f"{prefixo}_{timestamp}.zip"

    @staticmethod
    def criar_backup_zip(
        origem_dir: str,
        destino_zip_path: str,
        padrao_filtro: str = "*.*",
        callback_progresso: Optional[Callable[[int, int, str], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None
    ) -> Tuple[bool, str, int, int]:
        """
        Cria um arquivo ZIP contendo os arquivos da pasta de origem.
        Retorna: (sucesso: bool, mensagem: str, total_arquivos: int, tamanho_bytes: int)
        """
        if not os.path.isdir(origem_dir):
            return False, f"Diretório de origem não encontrado: {origem_dir}", 0, 0

        # Coletar arquivos a incluir
        arquivos_para_incluir: List[Tuple[str, str]] = []
        for root, _, files in os.walk(origem_dir):
            for file in files:
                if is_cancelled and is_cancelled():
                    return False, "Operação cancelada pelo usuário antes de iniciar o ZIP.", 0, 0
                if fnmatch.fnmatch(file.lower(), padrao_filtro.lower()) or padrao_filtro == "*.*":
                    caminho_completo = os.path.join(root, file)
                    caminho_relativo = os.path.relpath(caminho_completo, origem_dir)
                    arquivos_para_incluir.append((caminho_completo, caminho_relativo))

        if not arquivos_para_incluir:
            return False, f"Nenhum arquivo encontrado em '{origem_dir}' com o padrão '{padrao_filtro}'", 0, 0

        total_arquivos = len(arquivos_para_incluir)
        os.makedirs(os.path.dirname(os.path.abspath(destino_zip_path)), exist_ok=True)

        try:
            # Compactação padrão deflate (nível 6 para equilíbrio entre velocidade e tamanho)
            with zipfile.ZipFile(destino_zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for idx, (caminho_abs, caminho_rel) in enumerate(arquivos_para_incluir, 1):
                    if is_cancelled and is_cancelled():
                        zf.close()
                        if os.path.exists(destino_zip_path):
                            try:
                                os.remove(destino_zip_path)
                            except OSError:
                                pass
                        return False, "Compactação cancelada pelo usuário.", 0, 0

                    zf.write(caminho_abs, arcname=caminho_rel)
                    if callback_progresso:
                        callback_progresso(idx, total_arquivos, caminho_rel)

            tamanho_bytes = os.path.getsize(destino_zip_path)
            tamanho_mb = tamanho_bytes / (1024 * 1024)
            msg = f"ZIP gerado com sucesso: {total_arquivos} arquivos ({tamanho_mb:.2f} MB)"
            return True, msg, total_arquivos, tamanho_bytes
        except Exception as e:
            if os.path.exists(destino_zip_path):
                try:
                    os.remove(destino_zip_path)
                except OSError:
                    pass
            return False, f"Erro ao criar arquivo ZIP: {str(e)}", 0, 0

    @staticmethod
    def limpar_backups_antigos(diretorio: str, prefixo: str, dias_retencao: int) -> int:
        """Remove arquivos .zip antigos que excedam os dias de retenção."""
        if dias_retencao <= 0 or not os.path.isdir(diretorio):
            return 0

        limite = datetime.now() - timedelta(days=dias_retencao)
        removidos = 0

        for item in os.listdir(diretorio):
            if item.startswith(prefixo) and item.endswith(".zip"):
                caminho = os.path.join(diretorio, item)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(caminho))
                    if mtime < limite:
                        os.remove(caminho)
                        removidos += 1
                except Exception:
                    pass
        return removidos
