<div align="center">

# 🛡️ SafeBackup Windows

**Solução local e autônoma para automação de backups de arquivos, bancos de dados e sistemas em servidores e estações Windows.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20Server%20%7C%20Windows%2010%2F11-0078D6.svg?logo=windows&logoColor=white)](https://microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Produção%20%2F%20Homologado-brightgreen.svg)](#)

</div>

---

## 📌 Visão Geral

O **SafeBackup Windows** é uma solução universal, leve e confiável para backup automatizado em ambientes Windows. Ele permite apontar qualquer pasta de origem (bancos de dados SQL, pastas de rede, ERPs, sistemas de CFTV ou arquivos de usuários), compactando os dados em pacotes `.zip` padronizados com carimbo de data e hora.

O sistema sincroniza as cópias simultaneamente para um **Storage Local (NAS/SMB)** autenticado via rede e para o **Google Drive**, com envio de relatórios diários por e-mail via **Gmail (Senha de App)** e integração nativa ao **Agendador de Tarefas do Windows**.

---

## 🏗️ Arquitetura da Solução

```mermaid
flowchart TD
    subgraph Servidor ou Estação Windows
        Origem["📁 Pasta de Origem (Qualquer disco)\n(Arquivos, Bancos de Dados, ERPs, etc.)"]
        Engine["⚙️ SafeBackup Engine\n(Compactação / Verificação / Log)"]
        UI["🖥️ Painel Gráfico (GUI)\n(Configurações, Testes e Logs)"]
        TaskSched["⏰ Agendador do Windows (Task Scheduler)\n(Execução autônoma diária --silent)"]
    end

    subgraph Destinos do Backup
        NAS["🏢 Storage Local / NAS (SMB/CIFS)\n(\\IP\Compartilhamento com User e Senha)"]
        GDrive["☁️ Google Drive\n(Nuvem corporativa via Drive Desktop / API)"]
        Email["✉️ Alerta por E-mail (Gmail SMTP)\n(Relatório HTML de status, tempo e tamanho)"]
    end

    UI --> Engine
    TaskSched --> Engine
    Origem --> Engine
    Engine -->|Autenticação Net Use + Cópia em Blocos| NAS
    Engine -->|Cópia Segura / Upload Chunks| GDrive
    Engine -->|Disparo pós-rotina (SSL 465)| Email
```

---

## ✨ Principais Funcionalidades

- **🗜️ Compactação Inteligente em ZIP**: Agrupa os arquivos em pacotes com nomenclatura padronizada e carimbo temporal (ex: `BKP_SISTEMA_2026-11-24_020000.zip`).
- **⏹️ Botão Cancelar Backup**: Permite abortar a operação em tempo real a qualquer momento, limpando automaticamente arquivos temporários inacabados.
- **🏢 Storage Local (NAS / SMB)**: Conexão autenticada via rede (`net use \\IP\Share /user:usuario senha`) com suporte a domínio, teste de permissões de escrita em tempo real e desconexão segura.
- **☁️ Google Drive**: Suporte direto à unidade sincronizada do *Google Drive para Computador* (`G:\Meu Drive\...`) ou via API oficial com *Service Account JSON*.
- **✉️ Notificações por E-mail (Gmail + Senha de App)**: Envio automático de relatório formatado (HTML/Texto) com resumo de status, tamanho, duração e logs, com filtro opcional para *notificar apenas em caso de falha*.
- **⏰ Integração com o Agendador de Tarefas do Windows**: Cadastro com 1 clique de tarefas com privilégios elevados (`HIGHEST`) para execução em segundo plano sem necessidade de operador logado.
- **🧹 Política de Retenção Automática**: Exclusão programada de backups antigos (ex: 7 dias no disco local, 30 dias no Storage e 60 dias no Google Drive).
- **📦 Executável Independente (.exe)**: Não exige instalação prévia de Python nos servidores ou computadores finais.

---

## 📁 Estrutura do Projeto

```text
safebackup-windows/
│
├── config.example.json         # Modelo de configuração para novos ambientes
├── main.py                     # Ponto de entrada (GUI ou modo --silent)
├── build_exe.bat               # Compilador automatizado com PyInstaller
├── criar_atalho_desktop.bat    # Cria atalho na Área de Trabalho com 1 clique
├── instalar_agendador.bat      # Registra a tarefa no Agendador do Windows
├── testar_backup.bat           # Dispara teste rápido via terminal
├── requirements.txt            # Dependências Python (opcionais para build)
│
├── core/
│   ├── config_manager.py       # Leitura e escrita segura do config.json
│   ├── zip_manager.py          # Compactação em ZIP com token de cancelamento
│   ├── storage_manager.py      # Autenticação SMB/NAS, cópia e limpeza
│   ├── gdrive_manager.py       # Upload e cópia para o Google Drive
│   ├── email_notifier.py       # Notificações SMTP (Gmail SSL 465)
│   ├── backup_engine.py        # Orquestrador central e gerenciador de logs
│   └── scheduler.py            # Integração com o Windows Task Scheduler
│
├── gui/
│   └── app_gui.py              # Interface gráfica moderna em abas (Tkinter/ttk)
│
└── dist/
    └── SafeBackup/             # Pasta portátil pronta para os servidores (.exe)
```

---

## 🚀 Como Usar

### Opção 1: Executando via Python (Ambiente de Desenvolvimento)

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/safebackup-windows.git
   cd safebackup-windows
   ```

2. Crie seu arquivo de configuração baseado no modelo:
   ```bash
   copy config.example.json config.json
   ```

3. Inicie a interface gráfica:
   ```bash
   python main.py
   ```

---

### Opção 2: Gerando o Executável (.exe) para Servidores

1. Dê um duplo-clique no arquivo **`build_exe.bat`**.
2. O script instalará o PyInstaller e compilará o projeto dentro da pasta:
   ```text
   dist\SafeBackup\
   ```
3. Basta copiar a pasta `SafeBackup` para qualquer servidor ou estação Windows e executar o **`SafeBackup.exe`**!

---

## ⚙️ Guia de Configuração

### 1. Origem dos Arquivos
- Aponte para qualquer diretório (bancos de dados, pastas de sistemas, documentos ou CFTV).
- Defina o prefixo desejado (ex: `BKP_SISTEMA`, `BKP_SQL`, `BKP_ERP`).

### 2. Storage Local (NAS)
- **IP do Storage**: ex: `192.168.1.100` ou `10.0.0.50`
- **Compartilhamento**: Nome da pasta compartilhada (ex: `Backups`)
- **Usuário e Senha**: Credenciais com permissão de escrita no compartilhamento
- Utilize o botão **"🔍 Testar Conexão com Storage"** para validar.

### 3. Google Drive
- Instale o **Google Drive para Computador** no servidor.
- Aponte o caminho para a unidade virtual montada (ex: `G:/Meu Drive/Backups`).
- Utilize o botão **"🔍 Testar Acesso ao Google Drive"**.

### 4. Notificações por E-mail (Gmail com Senha de App)
1. Acesse [Google - Segurança](https://myaccount.google.com/security) com sua conta Gmail.
2. Ative a **Verificação em duas etapas**.
3. Em **Senhas de app**, crie uma com o nome *"SafeBackup"*.
4. Cole o código de 16 letras gerado no campo **Senha de App** do programa.
5. Clique em **"✉️ Testar Envio de E-mail"**.

### 5. Agendamento Automático
- Na aba **Agendamento**, informe o horário diário (ex: `02:00`).
- Clique em **"📅 Ativar Tarefa no Windows"** (ou execute o script auxiliar `instalar_agendador.bat` como Administrador).
- Uma vez salva a configuração, qualquer alteração futura de caminhos no painel será automaticamente respeitada pela tarefa agendada sem necessidade de recadastrar a tarefa.

---

## 🔒 Segurança

- O arquivo `config.json` armazena as credenciais de acesso localmente no servidor.
- O arquivo `.gitignore` já está configurado para **nunca subir senhas reais, logs ou arquivos de compilação para o GitHub**.
- Utilize sempre o `config.example.json` como base ao compartilhar o repositório.

---

## 📄 Licença

Este projeto está sob a licença [MIT](LICENSE). Sinta-se livre para utilizar, modificar e distribuir em seus ambientes corporativos.
