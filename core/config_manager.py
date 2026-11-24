import json
import os
from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    "origem": {
        "caminho": r"C:\Backups",
        "padrao_arquivos": "*.*",
        "criar_zip": True,
        "prefixo_zip": "BKP_SISTEMA",
        "retencao_dias_local": 7
    },
    "storage_local": {
        "habilitado": True,
        "ip": "192.168.1.100",
        "compartilhamento": "Backups",
        "usuario": "admin",
        "senha": "",
        "dominio": "",
        "retencao_dias": 30
    },
    "google_drive": {
        "habilitado": True,
        "metodo": "api_service_account",  # 'api_service_account', 'oauth_token', ou 'pasta_desktop'
        "pasta_id_ou_caminho": "",
        "arquivo_credenciais_json": "",
        "retencao_dias": 60
    },
    "notificacao_email": {
        "habilitado": False,
        "servidor_smtp": "smtp.gmail.com",
        "porta_smtp": 465,
        "email_remetente": "",
        "senha_app": "",
        "email_destinatario": "",
        "notificar_apenas_em_erro": False
    },
    "agendamento": {
        "hora_execucao": "02:00",
        "nome_tarefa_windows": "SafeBackup_Task"
    }
}

class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = os.path.abspath(config_path)
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                
            # Merge recursivo com defaults para garantir chaves novas
            merged = DEFAULT_CONFIG.copy()
            for section, values in loaded.items():
                if isinstance(values, dict) and section in merged:
                    merged[section].update(values)
                else:
                    merged[section] = values
            return merged
        except Exception:
            return DEFAULT_CONFIG.copy()

    def save_config(self, config_data: Dict[str, Any] = None) -> bool:
        if config_data:
            self.config = config_data
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao salvar configurações: {e}")
            return False

    def get(self, section: str, key: str = None, default=None):
        sec = self.config.get(section, {})
        if key is None:
            return sec
        return sec.get(key, default)

    def set(self, section: str, key: str, value: Any):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
