---
name: ip_cameras
description: Catálogo completo de credenciais, IPs estáticos (.201-.206), MAC addresses (LAN e NetCommon), topologia Wi-Fi, diagnóstico de bloqueio Ret=206 e Self-Healing com LanSentry para as 6 câmeras IP (D01 a D06).
---

# Skill: Catálogo, Diagnóstico e Self-Healing das Câmeras IP (`ip_cameras`)

Esta skill documenta o inventário completo das **6 câmeras IP (`D01..D06`)**, suas credenciais, arquitetura de IP estático vs DHCP, topologia de pontos de acesso Wi-Fi, peculiaridades de firmware e o motor de **Self-Healing com o LanSentry** (`scripts/camera_watchdog.py`).

---

## 📹 1. Catálogo Mestre das 6 Câmeras (`D01` a `D06`)

| Canal | **IP no NVR (Fixo)** | **MAC Wi-Fi / LAN (LanSentry)** | **MAC Interno (`UDP 1531`)** | **`MacAddr` no NVR** | Protocolo / Porta | **Usuário** | **Senha** | Hardware / Modelo | AP Wi-Fi Conectado | IA Humana |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: |
| **D01** | **`192.168.1.201`** | `d4:a3:eb:89:bd:f4` | `d4:a3:eb:89:bd:f4` | `""` *(vazio)* | NETIP (`34567`) | `kxhu` | `7prkra` | `XM530V200_X6-WEQ_8M` (iComm) | `quarto` (`192.168.1.44`) | ✅ Ativa |
| **D02** | **`192.168.1.4`** *(DHCP)* | `f8:16:0c:96:d5:f6` | `00:13:00:f6:69:a0` | `00:13:00:f6:69:a0` | NETIP (`34567`) | `bruno` | `blurbang86` | `IPC_XM210_X2-WR-T_S38` (V5.08) | `ZN-BRUNO_CONTER` (`192.168.1.1`) | — |
| **D03** | **`192.168.1.203`** | `00:13:00:01:61:7b` | `00:13:00:01:61:7b` | `00:13:00:01:61:7b` | NETIP (`34567`) | `usma` | `n2ykyy` | `XM530V200_IPG-X2-WQ-BL_8M` | Cabeada / Fixo `.203` | ✅ Ativa |
| **D04** | **`192.168.1.204`** | `38:be:ab:91:96:85` | `38:be:ab:91:96:85` | `""` *(vazio)* | NETIP (`34567`) | `admin` | `23blurbang86` | `IPC_GK7202V300_G4-WR_S38` (4MP) | `quarto` (`192.168.1.44`) | ✅ Ativa |
| **D05** | **`192.168.1.3`** | `48:8f:4c:3d:13:14` | *(Não usa DVRIP)* | `48:8f:4c:3d:13:14` | ONVIF (`5000`) | `admin` | `23blurbang86` | Shenzhen Trolink (`IPC73`) | `ZN-BRUNO_CONTER` (`192.168.1.1`) | — |
| **D06** | **`192.168.1.206`** | `a4:ef:15:30:79:32` | `a4:ef:15:30:79:32` | `""` *(vazio)* | NETIP (`34567`) | `admin` | `23blurbang` | `IPC_GK7202V300_G4-WR_S38` (*"vizinho"*) | `quarto` (`192.168.1.44`) | ✅ Ativa |

*(Nota: A antiga câmera Bilian `c4:3c:b0:79:80:db` do canal D02 foi substituída fisicamente pela câmera `IPC_XM210_X2-WR-T_S38` de MAC `f8:16:0c:96:d5:f6`).*

---

## 🌐 2. Topologia de Rede e Comportamento por Modelo/SoC

### 2.1 Dois Pontos de Acesso Wi-Fi na LAN (`192.168.1.0/24`)
1. **Roteador Principal ISP (`192.168.1.1` — SSID `ZN-BRUNO_CONTER`):**
   * Atua como servidor DHCP da rede e conecta diretamente **`D02`** e **`D05`**.
2. **AP / Repetidor TP-Link Secundário (`192.168.1.44` — SSID `quarto`, MAC `68:ff:7b:6b:99:be`):**
   * Conecta as câmeras externas **`D01`**, **`D04`** e **`D06`**.
   * *Importante:* Reiniciar apenas o roteador `192.168.1.1` **não** derruba o link Wi-Fi das câmeras conectadas no AP `quarto` (`192.168.1.44`). Para forçar a reconexão Wi-Fi imediata de `D01`, `D04` ou `D06`, é necessário reiniciar o AP `quarto` (`192.168.1.44`).

### 2.2 Arquitetura Dual-IP nas Câmeras XiongMai (`D01`, `D04` e `D06`)
* As câmeras `D01`, `D04` e `D06` possuem duas interfaces lógicas no kernel Linux:
  * `eth0` (`NetWork.NetCommon.HostIP`, `NetDHCP[0].Enable = False`): Configurada com os IPs estáticos dedicados **`192.168.1.201`**, **`192.168.1.204`** e **`192.168.1.206`** (eliminando o IP padrão de fábrica `192.168.1.10` que gerava conflito de ARP entre as câmeras).
  * `wlan0` / `eth2` (`NetWork.Wifi.HostIP`): Interface Wi-Fi que recebe IP via DHCP (ex: `.13`, `.15`, `.14`), mas cujo kernel Linux (`arp_ignore=0`) responde simultaneamente aos pacotes enviados para o IP estático `.201`, `.204` e `.206`!
* **Cuidado com Shadowing de Rota (`IPC_GK7202V300` — `D04` e `D06`):**
  * Se `NetWork.NetCommon` (`1040` ou `UDP 1532`) for regravado com a câmera já ligada, o comando `ifconfig eth0` sobrepõe temporariamente a rota `192.168.1.0/24 dev eth0` acima da `wlan0` até que o `udhcpc` da câmera entre em *Rebinding* (`T2` ~11 min) ou o AP `quarto` seja reiniciado.
  * Por esse motivo, **jamais preencha o campo `MacAddr` no NVR para `D01`, `D04` e `D06`** (veja seção 3 da skill `nvr_xiongmai`).

### 2.3 Peculiaridades de `D02` (`IPC_XM210` V5.08) e `D05` (`Trolink ONVIF`)
* **`D02` (`IPC_XM210_X2-WR-T_S38`):** Firmware V5.08 de 2026 com interface única Wi-Fi. Ignora alterações remotas de `Wifi.HostIP` via `1040` e obtém IP via DHCP. Possui dois MACs distintos:
  * MAC do rádio Wi-Fi na LAN (visto pelo **LanSentry** e tabela ARP): `f8:16:0c:96:d5:f6`
  * MAC interno do SoC (visto pelo broadcast **UDP `1531`** e usado no campo `MacAddr` do NVR): `00:13:00:f6:69:a0`
* **`D05` (`Shenzhen Trolink IPC73`):** Opera via protocolo `ONVIF` na porta `5000/tcp`. Seu XML ONVIF de fábrica reporta `<tt:PrefixLength>1</tt:PrefixLength>` (bug de firmware). **Nunca** envie `SetNetworkInterfaces` via ONVIF para não corromper a máscara de rede da câmera; deixe o `camera_watchdog.py` acompanhar o IP dela via LanSentry (`48:8f:4c:3d:13:14`).

---

## 🔒 3. Erros Mapeados e Solução de Problemas

| Código / Sintoma | Causa Raiz | Como Resolver |
| :--- | :--- | :--- |
| **`Ret: 206` (`Account Locked`)** | Múltiplas tentativas de login com senha incorreta (ex: NVR tentando logar a cada 10s com senha errada). Bloqueia o usuário `admin` em RAM por **30 minutos**. | 1. Corrigir imediatamente a senha no NVR (via `python3 scripts/camera_watchdog.py heal`).<br>2. Aguardar os 30 min sem tentativas erradas **ou** reiniciar a energia física da câmera. |
| **`Ret: 203` (`Password Error`)** | Senha divergente (ex: `23blurbang86` vs `23blurbang` na D06). | Rodar `python3 scripts/camera_watchdog.py heal` para restaurar a credencial canônica no NVR. |
| **`Ret: 205` (`User Not Exist`)** | Usuário incorreto ou desativado (ex: `admin` na D01/D03/NVR). | Usar `kxhu` na D01, `bruno` na D02, `usma` na D03 e `brunoconter` no NVR. |
| **`D02` ou `D05` fica `Offline` após reboot do roteador** | O DHCP do roteador principal (`192.168.1.1`) entregou um novo IP para a câmera. | O `scripts/camera_watchdog.py heal` (via cron a cada 10 min) consulta o **LanSentry** + **UDP `1531`** pelo MAC da câmera e atualiza o IP no NVR automaticamente. |
| **`D04` ou `D06` responde ao UDP `1531` mas dá timeout no TCP `34567`** | Algum cliente ou o próprio NVR enviou `UDP 1532` (por `MacAddr` preenchido no NVR), colocando a rota `eth0` acima da `wlan0`. | 1. Rodar `python3 scripts/camera_watchdog.py heal` para limpar o `MacAddr` no NVR.<br>2. Aguardar ~11 min para o `udhcpc` renovar a rota Wi-Fi ou reiniciar o AP `quarto` (`192.168.1.44`). |

---

## 🛡️ 4. Monitoramento de Saúde e Self-Healing com LanSentry (`scripts/camera_watchdog.py`)

O script `scripts/camera_watchdog.py` integra o **LanSentry (`http://192.168.1.7:8840/api/all`)**, o scanner **UDP Broadcast `1530/1531` (`34569/udp`)** e o **NVR (`192.168.1.20:34567`)**:

```bash
# Diagnóstico somente-leitura (exibe tabela com Status NVR, IP LanSentry, IP UDP 1531 e latência em ms)
python3 scripts/camera_watchdog.py check

# Diagnóstico + Self-Healing automático no NVR
python3 scripts/camera_watchdog.py heal

# Simulação de Self-Healing sem gravar alterações (Dry-Run)
python3 scripts/camera_watchdog.py heal --dry-run

# Saída estruturada em JSON para automação
python3 scripts/camera_watchdog.py check --json
```

### Automação via Cron (Ambiente de Produção Alpine)
O watchdog roda automaticamente a cada **10 minutos** no servidor `ssh alpine` conforme configurado no `crontab_template.txt`:
```cron
*/10 * * * * /home/bruno/lightmanager/.venv/bin/python3 /home/bruno/lightmanager/scripts/camera_watchdog.py heal >> /home/bruno/lightmanager/logs/camera_watchdog.log 2>&1
```
