import sys
import os

# Garante que o diretório de trabalho seja sempre a pasta onde o executável ou script reside
APP_DIR = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

from core.config_manager import ConfigManager
from core.backup_engine import BackupEngine

def main():
    args = sys.argv[1:]
    
    # Se chamado com argumento --silent, --cli ou em segundo plano via Agendador de Tarefas
    if any(arg in args for arg in ["--silent", "--cli", "-s", "/silent"]):
        print("[CFTV SafeBackup] Executando em modo silencioso / Agendador do Windows...")
        config_mgr = ConfigManager()
        engine = BackupEngine(config_mgr)
        sucesso = engine.executar_backup_completo()
        sys.exit(0 if sucesso else 1)
    else:
        # Modo Interface Gráfica Interativa
        try:
            from gui.app_gui import CFTVBackupGUI
            app = CFTVBackupGUI()
            app.mainloop()
        except Exception as e:
            print(f"[ERRO CRÍTICO] Falha ao iniciar interface gráfica: {e}")
            # Fallback para execução CLI caso o ambiente não suporte interface gráfica
            resposta = input("Deseja executar o backup no modo texto agora? (s/n): ")
            if resposta.lower() == 's':
                config_mgr = ConfigManager()
                engine = BackupEngine(config_mgr)
                engine.executar_backup_completo()

if __name__ == "__main__":
    main()
