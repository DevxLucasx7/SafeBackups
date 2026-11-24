import os
import sys
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

from core.config_manager import ConfigManager
from core.backup_engine import BackupEngine
from core.storage_manager import LocalStorageManager
from core.gdrive_manager import GoogleDriveManager
from core.email_notifier import EmailNotifier
from core.scheduler import WindowsScheduler

class CFTVBackupGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SafeBackup - Servidores e Estações Windows")
        self.geometry("860x680")
        self.minsize(800, 620)
        self._centralizar_janela(860, 680)

        # Configurações
        self.config_mgr = ConfigManager()
        self.config = self.config_mgr.load_config()
        self.engine_atual: Optional[BackupEngine] = None

        # Configura estilo visual moderno
        self._configurar_estilo()

        # Cria interface
        self._criar_widgets()
        self._carregar_valores_na_tela()
        self._atualizar_status_agendador()

    def _centralizar_janela(self, largura: int, altura: int):
        """Centraliza a janela no monitor do usuário."""
        self.update_idletasks()
        tela_largura = self.winfo_screenwidth()
        tela_altura = self.winfo_screenheight()
        pos_x = max(0, (tela_largura - largura) // 2)
        pos_y = max(0, (tela_altura - altura) // 2)
        self.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

    def _configurar_estilo(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("vista")
        except Exception:
            pass
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 6])
        self.style.configure("TLabel", font=("Segoe UI", 9))
        self.style.configure("TButton", font=("Segoe UI", 9), padding=5)
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), foreground="#0055aa")
        self.style.configure("Cancel.TButton", font=("Segoe UI", 9, "bold"), foreground="#cc0000")
        self.style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground="#1a3b5d")

    def _criar_widgets(self):
        # Cabeçalho Superior
        header_frame = tk.Frame(self, bg="#1a3b5d", height=60)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        title_lbl = tk.Label(
            header_frame,
            text="SafeBackup Windows",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#1a3b5d"
        )
        title_lbl.pack(side=tk.LEFT, padx=20, pady=10)

        subtitle_lbl = tk.Label(
            header_frame,
            text="Backup Automatizado: Local, Storage (SMB/NAS) e Google Drive",
            font=("Segoe UI", 9),
            fg="#a8c7eb",
            bg="#1a3b5d"
        )
        subtitle_lbl.pack(side=tk.LEFT, padx=5, pady=10)

        # Container Principal com Abas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Criação das Abas
        self.tab_dashboard = ttk.Frame(self.notebook, padding=10)
        self.tab_origem = ttk.Frame(self.notebook, padding=10)
        self.tab_storage = ttk.Frame(self.notebook, padding=10)
        self.tab_gdrive = ttk.Frame(self.notebook, padding=10)
        self.tab_email = ttk.Frame(self.notebook, padding=10)
        self.tab_agendamento = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_dashboard, text=" 🚀 Painel & Execução ")
        self.notebook.add(self.tab_origem, text=" 📁 Origem ")
        self.notebook.add(self.tab_storage, text=" 🏢 Storage Local ")
        self.notebook.add(self.tab_gdrive, text=" ☁️ Google Drive ")
        self.notebook.add(self.tab_email, text=" ✉️ Notificação E-mail ")
        self.notebook.add(self.tab_agendamento, text=" ⏰ Agendamento ")

        # Montagem do conteúdo de cada aba
        self._montar_aba_dashboard()
        self._montar_aba_origem()
        self._montar_aba_storage()
        self._montar_aba_gdrive()
        self._montar_aba_email()
        self._montar_aba_agendamento()

        # Rodapé com Botão Salvar e Status
        footer_frame = tk.Frame(self, bg="#f0f2f5", height=50)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_status_geral = tk.Label(footer_frame, text="Pronto.", font=("Segoe UI", 9), bg="#f0f2f5", fg="#333")
        self.lbl_status_geral.pack(side=tk.LEFT, padx=20, pady=12)

        self.btn_salvar = ttk.Button(footer_frame, text="💾 Salvar Todas as Configurações", command=self._acao_salvar_config)
        self.btn_salvar.pack(side=tk.RIGHT, padx=20, pady=8)

    # -------------------------------------------------------------
    # ABA 1: DASHBOARD & EXECUÇÃO
    # -------------------------------------------------------------
    def _montar_aba_dashboard(self):
        f_top = ttk.Frame(self.tab_dashboard)
        f_top.pack(fill=tk.X, pady=5)

        self.btn_executar = ttk.Button(
            f_top,
            text="▶ EXECUTAR BACKUP COMPLETO AGORA",
            style="Action.TButton",
            command=self._iniciar_backup_manual
        )
        self.btn_executar.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_cancelar = ttk.Button(
            f_top,
            text="⏹ CANCELAR BACKUP",
            style="Cancel.TButton",
            state=tk.DISABLED,
            command=self._cancelar_backup_manual
        )
        self.btn_cancelar.pack(side=tk.LEFT, padx=5, pady=5)

        btn_abrir_logs = ttk.Button(f_top, text="📂 Abrir Pasta de Logs", command=self._abrir_pasta_logs)
        btn_abrir_logs.pack(side=tk.RIGHT, padx=5)

        btn_limpar_logs = ttk.Button(f_top, text="🧹 Limpar Painel", command=self._limpar_log_painel)
        btn_limpar_logs.pack(side=tk.RIGHT, padx=5)

        # Progresso
        f_prog = ttk.LabelFrame(self.tab_dashboard, text="Progresso da Operação", padding=8)
        f_prog.pack(fill=tk.X, pady=5)

        self.prog_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(f_prog, variable=self.prog_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=4)

        self.lbl_etapa = ttk.Label(f_prog, text="Aguardando início...", font=("Segoe UI", 9, "italic"))
        self.lbl_etapa.pack(anchor="w", padx=5)

        # Caixa de Log em tempo real
        f_log = ttk.LabelFrame(self.tab_dashboard, text="Logs do Sistema em Tempo Real", padding=8)
        f_log.pack(fill=tk.BOTH, expand=True, pady=5)

        self.txt_logs = tk.Text(
            f_log,
            wrap=tk.WORD,
            bg="#1e1e1e",
            fg="#dcdcdc",
            font=("Consolas", 9),
            insertbackground="white"
        )
        scroll = ttk.Scrollbar(f_log, command=self.txt_logs.yview)
        self.txt_logs.configure(yscrollcommand=scroll.set)

        self.txt_logs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # -------------------------------------------------------------
    # ABA 2: ORIGEM DOS ARQUIVOS
    # -------------------------------------------------------------
    def _montar_aba_origem(self):
        ttk.Label(self.tab_origem, text="Configuração da Pasta de Origem do Backup", style="Header.TLabel").pack(anchor="w", pady=10)

        f_form = ttk.Frame(self.tab_origem)
        f_form.pack(fill=tk.X, pady=5)

        ttk.Label(f_form, text="Diretório dos Arquivos de Origem:").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_origem_caminho = ttk.Entry(f_form, width=55)
        self.ent_origem_caminho.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(f_form, text="Procurar...", command=self._procurar_pasta_origem).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(f_form, text="Filtro de Arquivos (Ex: *.*, *.bak, *.sql):").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_origem_filtro = ttk.Entry(f_form, width=20)
        self.ent_origem_filtro.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(f_form, text="Prefixo do Arquivo ZIP:").grid(row=2, column=0, sticky="w", pady=5)
        self.ent_origem_prefixo = ttk.Entry(f_form, width=20)
        self.ent_origem_prefixo.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(f_form, text="Dias de Retenção de ZIPs Locais (0 = nunca apagar):").grid(row=3, column=0, sticky="w", pady=5)
        self.ent_origem_retencao = ttk.Entry(f_form, width=10)
        self.ent_origem_retencao.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        dica = ttk.Label(
            self.tab_origem,
            text="ℹ O sistema agrupa todos os arquivos da pasta em um único arquivo .zip compactado\ncom data e hora no nome para economizar espaço e agilizar a transferência.",
            font=("Segoe UI", 9, "italic"),
            foreground="#555"
        )
        dica.pack(anchor="w", pady=15)

    # -------------------------------------------------------------
    # ABA 3: STORAGE LOCAL (SMB / NAS)
    # -------------------------------------------------------------
    def _montar_aba_storage(self):
        ttk.Label(self.tab_storage, text="Storage Local / Servidor de Rede (NAS)", style="Header.TLabel").pack(anchor="w", pady=10)

        self.var_storage_hab = tk.BooleanVar(value=True)
        chk_hab = ttk.Checkbutton(self.tab_storage, text="Habilitar envio para Storage Local", variable=self.var_storage_hab)
        chk_hab.pack(anchor="w", pady=5)

        f_form = ttk.Frame(self.tab_storage)
        f_form.pack(fill=tk.X, pady=5)

        ttk.Label(f_form, text="Endereço IP do Storage:").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_storage_ip = ttk.Entry(f_form, width=30)
        self.ent_storage_ip.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(f_form, text="Nome da Pasta Compartilhada (Share):").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_storage_share = ttk.Entry(f_form, width=30)
        self.ent_storage_share.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(f_form, text="Usuário de Acesso:").grid(row=2, column=0, sticky="w", pady=5)
        self.ent_storage_user = ttk.Entry(f_form, width=30)
        self.ent_storage_user.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(f_form, text="Senha:").grid(row=3, column=0, sticky="w", pady=5)
        self.ent_storage_pass = ttk.Entry(f_form, width=30, show="*")
        self.ent_storage_pass.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(f_form, text="Domínio (Opcional se houver AD):").grid(row=4, column=0, sticky="w", pady=5)
        self.ent_storage_domain = ttk.Entry(f_form, width=30)
        self.ent_storage_domain.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(f_form, text="Dias de Retenção no Storage:").grid(row=5, column=0, sticky="w", pady=5)
        self.ent_storage_ret = ttk.Entry(f_form, width=10)
        self.ent_storage_ret.grid(row=5, column=1, sticky="w", padx=5, pady=5)

        btn_testar_st = ttk.Button(self.tab_storage, text="🔍 Testar Conexão com Storage", command=self._testar_storage)
        btn_testar_st.pack(anchor="w", pady=15)

    # -------------------------------------------------------------
    # ABA 4: GOOGLE DRIVE
    # -------------------------------------------------------------
    def _montar_aba_gdrive(self):
        ttk.Label(self.tab_gdrive, text="Destino em Nuvem: Google Drive", style="Header.TLabel").pack(anchor="w", pady=10)

        self.var_gdrive_hab = tk.BooleanVar(value=True)
        chk_gd = ttk.Checkbutton(self.tab_gdrive, text="Habilitar envio para Google Drive", variable=self.var_gdrive_hab)
        chk_gd.pack(anchor="w", pady=5)

        f_form = ttk.Frame(self.tab_gdrive)
        f_form.pack(fill=tk.X, pady=5)

        ttk.Label(f_form, text="Método de Integração:").grid(row=0, column=0, sticky="w", pady=5)
        self.combo_gdrive_metodo = ttk.Combobox(
            f_form,
            values=["pasta_desktop", "api_service_account"],
            state="readonly",
            width=28
        )
        self.combo_gdrive_metodo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.combo_gdrive_metodo.set("pasta_desktop")

        ttk.Label(f_form, text="Caminho da Pasta ou ID no Drive:").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_gdrive_caminho = ttk.Entry(f_form, width=45)
        self.ent_gdrive_caminho.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(f_form, text="Procurar...", command=self._procurar_pasta_gdrive).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(f_form, text="Arquivo JSON de Credenciais (se usar API):").grid(row=2, column=0, sticky="w", pady=5)
        self.ent_gdrive_json = ttk.Entry(f_form, width=45)
        self.ent_gdrive_json.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(f_form, text="Selecionar JSON...", command=self._procurar_json_gdrive).grid(row=2, column=2, padx=5, pady=5)

        ttk.Label(f_form, text="Dias de Retenção no Drive:").grid(row=3, column=0, sticky="w", pady=5)
        self.ent_gdrive_ret = ttk.Entry(f_form, width=10)
        self.ent_gdrive_ret.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        btn_testar_gd = ttk.Button(self.tab_gdrive, text="🔍 Testar Acesso ao Google Drive", command=self._testar_gdrive)
        btn_testar_gd.pack(anchor="w", pady=15)

        info_gd = ttk.Label(
            self.tab_gdrive,
            text="💡 Dica: Se o servidor tiver o Google Drive para Desktop instalado, basta apontar\npara a letra da unidade virtual (ex: 'G:\\Meu Drive\\CFTV_Backups') para sincronização automática.",
            font=("Segoe UI", 9, "italic"),
            foreground="#555"
        )
        info_gd.pack(anchor="w", pady=5)

    # -------------------------------------------------------------
    # ABA 5: NOTIFICAÇÃO POR E-MAIL (GMAIL COM SENHA DE APP)
    # -------------------------------------------------------------
    def _montar_aba_email(self):
        ttk.Label(self.tab_email, text="Notificações e Relatórios por E-mail (Gmail / SMTP)", style="Header.TLabel").pack(anchor="w", pady=10)

        self.var_email_hab = tk.BooleanVar(value=False)
        chk_em = ttk.Checkbutton(self.tab_email, text="Habilitar Notificações por E-mail a cada Backup", variable=self.var_email_hab)
        chk_em.pack(anchor="w", pady=5)

        f_form = ttk.Frame(self.tab_email)
        f_form.pack(fill=tk.X, pady=5)

        ttk.Label(f_form, text="Seu E-mail Gmail:").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_email_remetente = ttk.Entry(f_form, width=35)
        self.ent_email_remetente.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(f_form, text="Senha de App do Google (16 caracteres):").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_email_senha_app = ttk.Entry(f_form, width=35, show="*")
        self.ent_email_senha_app.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(f_form, text="E-mail de Destino do Relatório:").grid(row=2, column=0, sticky="w", pady=5)
        self.ent_email_destinatario = ttk.Entry(f_form, width=35)
        self.ent_email_destinatario.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        self.var_email_apenas_erro = tk.BooleanVar(value=False)
        chk_erro = ttk.Checkbutton(f_form, text="Notificar apenas se ocorrer erro/falha no backup", variable=self.var_email_apenas_erro)
        chk_erro.grid(row=3, column=0, columnspan=2, sticky="w", pady=8)

        btn_testar_em = ttk.Button(self.tab_email, text="✉️ Testar Envio de E-mail Agora", command=self._testar_email)
        btn_testar_em.pack(anchor="w", pady=15)

        instrucao = ttk.Label(
            self.tab_email,
            text="📌 Como gerar a Senha de App no Google:\n"
                 "1. Acesse https://myaccount.google.com/security\n"
                 "2. Ative a 'Verificação em duas etapas' caso ainda não esteja ativada.\n"
                 "3. Em 'Senhas de app', crie uma nova com o nome 'SafeBackup'.\n"
                 "4. Cole a chave de 16 letras gerada no campo acima.",
            font=("Segoe UI", 9),
            foreground="#333"
        )
        instrucao.pack(anchor="w", pady=10)

    # -------------------------------------------------------------
    # ABA 6: AGENDAMENTO DO WINDOWS
    # -------------------------------------------------------------
    def _montar_aba_agendamento(self):
        ttk.Label(self.tab_agendamento, text="Automação no Agendador de Tarefas do Windows", style="Header.TLabel").pack(anchor="w", pady=10)

        f_form = ttk.Frame(self.tab_agendamento)
        f_form.pack(fill=tk.X, pady=5)

        ttk.Label(f_form, text="Horário Diário de Execução (HH:MM):").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_hora_agendada = ttk.Entry(f_form, width=12)
        self.ent_hora_agendada.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        self.lbl_status_tarefa = ttk.Label(self.tab_agendamento, text="Consultando status da tarefa...", font=("Segoe UI", 10, "bold"))
        self.lbl_status_tarefa.pack(anchor="w", pady=10)

        f_btns = ttk.Frame(self.tab_agendamento)
        f_btns.pack(fill=tk.X, pady=10)

        btn_ativar = ttk.Button(f_btns, text="📅 Ativar / Atualizar Tarefa no Windows", command=self._ativar_tarefa_windows)
        btn_ativar.pack(side=tk.LEFT, padx=5)

        btn_remover = ttk.Button(f_btns, text="❌ Remover Tarefa Agendada", command=self._remover_tarefa_windows)
        btn_remover.pack(side=tk.LEFT, padx=5)

        dica_sch = ttk.Label(
            self.tab_agendamento,
            text="⚙ A rotina é registrada nativamente no Windows Task Scheduler com permissões elevadas,\n"
                 "rodando em segundo plano silenciosamente mesmo se não houver operador conectado.",
            font=("Segoe UI", 9, "italic"),
            foreground="#555"
        )
        dica_sch.pack(anchor="w", pady=15)

    # -------------------------------------------------------------
    # PREENCHIMENTO E SALVAMENTO DE CONFIGURAÇÕES
    # -------------------------------------------------------------
    def _carregar_valores_na_tela(self):
        cfg_origem = self.config.get("origem", {})
        self.ent_origem_caminho.delete(0, tk.END)
        self.ent_origem_caminho.insert(0, cfg_origem.get("caminho", r"C:\CFTV"))
        self.ent_origem_filtro.delete(0, tk.END)
        self.ent_origem_filtro.insert(0, cfg_origem.get("padrao_arquivos", "*.*"))
        self.ent_origem_prefixo.delete(0, tk.END)
        self.ent_origem_prefixo.insert(0, cfg_origem.get("prefixo_zip", "BKP_CFTV"))
        self.ent_origem_retencao.delete(0, tk.END)
        self.ent_origem_retencao.insert(0, str(cfg_origem.get("retencao_dias_local", 7)))

        cfg_st = self.config.get("storage_local", {})
        self.var_storage_hab.set(cfg_st.get("habilitado", True))
        self.ent_storage_ip.delete(0, tk.END)
        self.ent_storage_ip.insert(0, cfg_st.get("ip", "192.168.1.100"))
        self.ent_storage_share.delete(0, tk.END)
        self.ent_storage_share.insert(0, cfg_st.get("compartilhamento", "CFTV_Backups"))
        self.ent_storage_user.delete(0, tk.END)
        self.ent_storage_user.insert(0, cfg_st.get("usuario", "admin"))
        self.ent_storage_pass.delete(0, tk.END)
        self.ent_storage_pass.insert(0, cfg_st.get("senha", ""))
        self.ent_storage_domain.delete(0, tk.END)
        self.ent_storage_domain.insert(0, cfg_st.get("dominio", ""))
        self.ent_storage_ret.delete(0, tk.END)
        self.ent_storage_ret.insert(0, str(cfg_st.get("retencao_dias", 30)))

        cfg_gd = self.config.get("google_drive", {})
        self.var_gdrive_hab.set(cfg_gd.get("habilitado", True))
        self.combo_gdrive_metodo.set(cfg_gd.get("metodo", "pasta_desktop"))
        self.ent_gdrive_caminho.delete(0, tk.END)
        self.ent_gdrive_caminho.insert(0, cfg_gd.get("pasta_id_ou_caminho", ""))
        self.ent_gdrive_json.delete(0, tk.END)
        self.ent_gdrive_json.insert(0, cfg_gd.get("arquivo_credenciais_json", ""))
        self.ent_gdrive_ret.delete(0, tk.END)
        self.ent_gdrive_ret.insert(0, str(cfg_gd.get("retencao_dias", 60)))

        cfg_em = self.config.get("notificacao_email", {})
        self.var_email_hab.set(cfg_em.get("habilitado", False))
        self.ent_email_remetente.delete(0, tk.END)
        self.ent_email_remetente.insert(0, cfg_em.get("email_remetente", ""))
        self.ent_email_senha_app.delete(0, tk.END)
        self.ent_email_senha_app.insert(0, cfg_em.get("senha_app", ""))
        self.ent_email_destinatario.delete(0, tk.END)
        self.ent_email_destinatario.insert(0, cfg_em.get("email_destinatario", ""))
        self.var_email_apenas_erro.set(cfg_em.get("notificar_apenas_em_erro", False))

        cfg_ag = self.config.get("agendamento", {})
        self.ent_hora_agendada.delete(0, tk.END)
        self.ent_hora_agendada.insert(0, cfg_ag.get("hora_execucao", "02:00"))

    def _parse_inteiro(self, valor: str, padrao: int) -> int:
        """Converte valor para inteiro com segurança."""
        try:
            val = int(valor.strip())
            return max(0, val)
        except (ValueError, AttributeError):
            return padrao

    def _obter_dados_da_tela(self) -> dict:
        return {
            "origem": {
                "caminho": self.ent_origem_caminho.get().strip(),
                "padrao_arquivos": self.ent_origem_filtro.get().strip() or "*.*",
                "criar_zip": True,
                "prefixo_zip": self.ent_origem_prefixo.get().strip() or "BKP_CFTV",
                "retencao_dias_local": self._parse_inteiro(self.ent_origem_retencao.get(), 7)
            },
            "storage_local": {
                "habilitado": self.var_storage_hab.get(),
                "ip": self.ent_storage_ip.get().strip(),
                "compartilhamento": self.ent_storage_share.get().strip(),
                "usuario": self.ent_storage_user.get().strip(),
                "senha": self.ent_storage_pass.get(),
                "dominio": self.ent_storage_domain.get().strip(),
                "retencao_dias": self._parse_inteiro(self.ent_storage_ret.get(), 30)
            },
            "google_drive": {
                "habilitado": self.var_gdrive_hab.get(),
                "metodo": self.combo_gdrive_metodo.get(),
                "pasta_id_ou_caminho": self.ent_gdrive_caminho.get().strip(),
                "arquivo_credenciais_json": self.ent_gdrive_json.get().strip(),
                "retencao_dias": self._parse_inteiro(self.ent_gdrive_ret.get(), 60)
            },
            "notificacao_email": {
                "habilitado": self.var_email_hab.get(),
                "servidor_smtp": "smtp.gmail.com",
                "porta_smtp": 465,
                "email_remetente": self.ent_email_remetente.get().strip(),
                "senha_app": self.ent_email_senha_app.get().strip(),
                "email_destinatario": self.ent_email_destinatario.get().strip(),
                "notificar_apenas_em_erro": self.var_email_apenas_erro.get()
            },
            "agendamento": {
                "hora_execucao": self.ent_hora_agendada.get().strip() or "02:00",
                "nome_tarefa_windows": "CFTV_SafeBackup_Task"
            }
        }

    def _acao_salvar_config(self):
        try:
            dados = self._obter_dados_da_tela()
            if self.config_mgr.save_config(dados):
                self.config = dados
                self.lbl_status_geral.config(text="Configurações salvas com sucesso em config.json", fg="#198754")
                messagebox.showinfo("Sucesso", "Todas as configurações foram salvas com sucesso!")
            else:
                messagebox.showerror("Erro", "Não foi possível gravar o arquivo config.json")
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", str(e))

    # -------------------------------------------------------------
    # OPERAÇÕES E THREADS
    # -------------------------------------------------------------
    def _iniciar_backup_manual(self):
        caminho_origem = self.ent_origem_caminho.get().strip()
        if not caminho_origem or not os.path.exists(caminho_origem):
            messagebox.showwarning(
                "Origem Não Encontrada",
                f"A pasta de origem informada não existe ou não foi selecionada:\n'{caminho_origem}'\n\nPor favor, informe uma pasta válida na aba 'Origem (C:)'."
            )
            return

        hab_storage = self.var_storage_hab.get()
        hab_gdrive = self.var_gdrive_hab.get()
        if not hab_storage and not hab_gdrive:
            messagebox.showwarning(
                "Nenhum Destino Habilitado",
                "Atenção: Nenhum destino de backup está habilitado!\n\nPor favor, ative ao menos uma opção: 'Storage Local' ou 'Google Drive'."
            )
            return

        self._acao_salvar_config()
        self.btn_executar.config(state=tk.DISABLED)
        self.btn_cancelar.config(state=tk.NORMAL)
        self.prog_var.set(0)
        self.lbl_etapa.config(text="Iniciando rotina de backup...")

        def _thread_job():
            self.engine_atual = BackupEngine(self.config_mgr, log_callback=self._adicionar_log)
            def prog_cb(pct, texto):
                self.after(0, lambda: self._atualizar_progresso(pct, texto))

            sucesso = self.engine_atual.executar_backup_completo(progress_callback=prog_cb)
            cancelado = self.engine_atual.foi_cancelado()
            self.after(0, lambda: self._finalizar_backup_manual(sucesso, cancelado))

        threading.Thread(target=_thread_job, daemon=True).start()

    def _cancelar_backup_manual(self):
        if self.engine_atual:
            self.btn_cancelar.config(state=tk.DISABLED)
            self.lbl_etapa.config(text="Cancelando backup e limpando arquivos temporários...")
            self._adicionar_log("[AVISO] Solicitado cancelamento da rotina...")
            self.engine_atual.cancelar()

    def _atualizar_progresso(self, pct: int, texto: str):
        self.prog_var.set(pct)
        self.lbl_etapa.config(text=f"[{pct}%] {texto}")

    def _finalizar_backup_manual(self, sucesso: bool, cancelado: bool = False):
        self.btn_executar.config(state=tk.NORMAL)
        self.btn_cancelar.config(state=tk.DISABLED)
        self.engine_atual = None

        if cancelado:
            self.lbl_etapa.config(text="⏹ Backup cancelado pelo usuário.")
            messagebox.showwarning("Backup Cancelado", "A rotina de backup foi cancelada com sucesso.")
        elif sucesso:
            self.lbl_etapa.config(text="✔ Backup concluído com êxito!")
            messagebox.showinfo("Backup Concluído", "Rotina de backup finalizada com sucesso!")
        else:
            self.lbl_etapa.config(text="⚠ O backup finalizou com falhas. Verifique os logs.")
            messagebox.showwarning("Atenção", "Ocorreram erros na rotina de backup. Verifique a caixa de logs.")

    def _adicionar_log(self, texto: str):
        def _append():
            self.txt_logs.insert(tk.END, texto + "\n")
            self.txt_logs.see(tk.END)
        self.after(0, _append)

    def _limpar_log_painel(self):
        self.txt_logs.delete("1.0", tk.END)

    def _abrir_pasta_logs(self):
        pasta = os.path.abspath("logs")
        os.makedirs(pasta, exist_ok=True)
        os.startfile(pasta)

    # -------------------------------------------------------------
    # TESTES INDIVIDUAIS
    # -------------------------------------------------------------
    def _testar_storage(self):
        ip = self.ent_storage_ip.get().strip()
        share = self.ent_storage_share.get().strip()
        user = self.ent_storage_user.get().strip()
        pwd = self.ent_storage_pass.get()
        dom = self.ent_storage_domain.get().strip()

        if not ip or not share:
            messagebox.showwarning("Aviso", "Informe ao menos o IP e o Compartilhamento.")
            return

        self._adicionar_log(f"Iniciando teste de conexão no Storage: \\\\{ip}\\{share}")
        def _th():
            sm = LocalStorageManager(ip, share, user, pwd, dom)
            ok, msg = sm.testar_conexao()
            if ok:
                self.after(0, lambda: messagebox.showinfo("Teste de Storage", f"Sucesso!\n{msg}"))
                self._adicionar_log(f"Storage Teste OK: {msg}")
            else:
                self.after(0, lambda: messagebox.showerror("Falha no Storage", f"Falha na conexão:\n{msg}"))
                self._adicionar_log(f"Storage Teste FALHA: {msg}")
        threading.Thread(target=_th, daemon=True).start()

    def _testar_gdrive(self):
        metodo = self.combo_gdrive_metodo.get()
        caminho = self.ent_gdrive_caminho.get().strip()
        json_file = self.ent_gdrive_json.get().strip()

        def _th():
            gm = GoogleDriveManager(metodo, caminho, json_file)
            ok, msg = gm.testar_conexao()
            if ok:
                self.after(0, lambda: messagebox.showinfo("Teste Google Drive", f"Sucesso!\n{msg}"))
                self._adicionar_log(f"Google Drive Teste OK: {msg}")
            else:
                self.after(0, lambda: messagebox.showerror("Falha no Google Drive", f"Falha:\n{msg}"))
                self._adicionar_log(f"Google Drive Teste FALHA: {msg}")
        threading.Thread(target=_th, daemon=True).start()

    def _testar_email(self):
        rem = self.ent_email_remetente.get().strip()
        pwd = self.ent_email_senha_app.get().strip()
        dest = self.ent_email_destinatario.get().strip() or rem

        if not rem or not pwd:
            messagebox.showwarning("Aviso", "Preencha o e-mail e a senha de app.")
            return

        def _th():
            en = EmailNotifier(rem, pwd, dest)
            ok, msg = en.testar_credenciais()
            if ok:
                # Envia e-mail de teste real
                detalhes = {
                    "data_hora": "Teste de Comunicação",
                    "arquivo_zip": "teste.zip",
                    "tamanho_mb": 0.0,
                    "status_storage": "Nenhum (Modo de Teste)",
                    "status_gdrive": "Nenhum (Modo de Teste)"
                }
                ok2, msg2 = en.enviar_relatorio_backup(True, detalhes, "Este é um teste disparado pelo painel de controle do CFTV SafeBackup.")
                if ok2:
                    self.after(0, lambda: messagebox.showinfo("Teste de E-mail", f"E-mail de teste enviado com sucesso para {dest}!"))
                    self._adicionar_log(f"E-mail de teste enviado com sucesso para {dest}")
                else:
                    self.after(0, lambda: messagebox.showerror("Erro de Envio", f"Autenticou, mas falhou ao enviar: {msg2}"))
            else:
                self.after(0, lambda: messagebox.showerror("Falha no E-mail", f"Erro de autenticação:\n{msg}"))
                self._adicionar_log(f"E-mail Teste FALHA: {msg}")
        threading.Thread(target=_th, daemon=True).start()

    # -------------------------------------------------------------
    # DIÁLOGOS DE SELEÇÃO DE ARQUIVOS / PASTAS
    # -------------------------------------------------------------
    def _procurar_pasta_origem(self):
        sel = filedialog.askdirectory(title="Selecione a Pasta de Origem do Backup", initialdir="C:\\")
        if sel:
            self.ent_origem_caminho.delete(0, tk.END)
            self.ent_origem_caminho.insert(0, sel)

    def _procurar_pasta_gdrive(self):
        sel = filedialog.askdirectory(title="Selecione a Pasta do Google Drive")
        if sel:
            self.ent_gdrive_caminho.delete(0, tk.END)
            self.ent_gdrive_caminho.insert(0, sel)

    def _procurar_json_gdrive(self):
        sel = filedialog.askopenfilename(
            title="Selecione o arquivo de credenciais JSON do Google",
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")]
        )
        if sel:
            self.ent_gdrive_json.delete(0, tk.END)
            self.ent_gdrive_json.insert(0, sel)

    # -------------------------------------------------------------
    # AGENDAMENTO
    # -------------------------------------------------------------
    def _atualizar_status_agendador(self):
        nome_tarefa = self.config.get("agendamento", {}).get("nome_tarefa_windows", "SafeBackup_Task")
        ativo = WindowsScheduler.verificar_tarefa(nome_tarefa)
        if ativo:
            hora = self.config.get("agendamento", {}).get("hora_execucao", "02:00")
            self.lbl_status_tarefa.config(
                text=f"Status da Tarefa: ATIVA NO WINDOWS (Executando diariamente às {hora})",
                foreground="#198754"
            )
        else:
            self.lbl_status_tarefa.config(
                text="Status da Tarefa: DESATIVADA / NÃO AGENDADA NO WINDOWS",
                foreground="#dc3545"
            )

    def _ativar_tarefa_windows(self):
        hora = self.ent_hora_agendada.get().strip() or "02:00"
        if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", hora):
            messagebox.showwarning(
                "Formato de Horário Inválido",
                f"O horário digitado '{hora}' não é válido.\n\nPor favor, utilize o formato HH:MM de 24 horas (ex: 02:00, 23:30)."
            )
            return

        self._acao_salvar_config()
        nome_tarefa = self.config.get("agendamento", {}).get("nome_tarefa_windows", "SafeBackup_Task")

        ok, msg = WindowsScheduler.criar_tarefa(nome_tarefa, hora)
        if ok:
            messagebox.showinfo("Agendador do Windows", msg)
            self._atualizar_status_agendador()
        else:
            messagebox.showerror("Erro no Agendador", f"{msg}\n\nCertifique-se de executar o programa como Administrador para registrar tarefas no sistema.")

    def _remover_tarefa_windows(self):
        nome_tarefa = self.config.get("agendamento", {}).get("nome_tarefa_windows", "SafeBackup_Task")
        ok, msg = WindowsScheduler.remover_tarefa(nome_tarefa)
        if ok:
            messagebox.showinfo("Agendador do Windows", msg)
            self._atualizar_status_agendador()
        else:
            messagebox.showerror("Erro ao Remover", msg)
