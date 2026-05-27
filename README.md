# SMILES2Docking

Aplicativo desktop e workflow Python para preparar ligantes a partir de planilhas `CSV`, `XLS` e `XLSX`. O pipeline executa curadoria estrutural, protonação multi-sítio em pH configurável, geração 3D com `RDKit ETKDGv3`, refinamento por campos de força (`MMFF94 → MMFF94s → UFF`), refinamento semi-empírico opcional `MOPAC PM7` e exporta em `MOL2`, `SDF` ou `PDBQT` pronto para `AutoDock Vina`.

## Autoria

- Adriano Marques Gonçalves
- Universidade de Araraquara - UNIARA
- amgoncalves@uniara.edu.br

## Principais capacidades

1. Carregar planilhas com colunas de ID e SMILES.
2. Remover sais, contraíons e fragmentos desconectados quando o fragmento principal é identificável.
3. Protonar com backend selecionável (`Dimorphite-DL`, `Open Babel` ou nenhum) em pH configurável, com tratamento multi-sítio e regras de pKa por contexto químico.
4. Gerar estruturas 3D com `RDKit ETKDGv3`.
5. Otimizar geometria com a cascata `MMFF94 → MMFF94s → UFF`.
6. Refinamento semi-empírico opcional via `MOPAC PM7` (`PM6`, `PM6-D3H4X`, `PM6-ORG`, `RM1`, `PM3`, `AM1`, `MNDO` também suportados), desativado por padrão para preservar throughput.
7. Exportação em `MOL2`, `SDF` ou `PDBQT` (este último via `Meeko`, evitando a fragmentação observada em conversores baseados apenas em `Open Babel`), nos modos `separate_*` ou `single_*`.
8. Paralelização por `joblib` configurável por `n_jobs`, com workers isolados que herdam apenas o dicionário de configuração serializável.
9. Relatório JSON por execução incluindo tempos por molécula, estágios (`clean`, `protonate`, `build_3d`, `export`), média/mediana/p95, fastest/slowest, wall-clock e throughput em moléculas por minuto.
10. Log final na pasta de saída escolhida.
11. Execução por CLI, interface gráfica desktop ou pacote distribuível (Windows `.exe`, Linux `AppImage`).

## Backends de protonação

Configurável em `config/settings.yaml` no campo `protonation.backend`:

| Backend | Quando usar | Observações |
|---------|-------------|-------------|
| `dimorphite` (padrão) | Curadoria multi-sítio com regras de pKa contextuais | Reconhece efeitos de substituintes, vizinhança e múltiplos centros ionizáveis. Saída controlada por `ph`, `ph_tolerance`, `max_variants`, `variant_selection`. |
| `openbabel` | Compatibilidade com pipelines legados ou ausência de `Dimorphite-DL` | Aplica `obabel -p <pH>`; menos preciso em moléculas com vários centros ionizáveis. |
| `none` | Diagnóstico ou quando a entrada já está protonada | Pass-through, mantém o SMILES de entrada. |

Validação prática com `Dimorphite-DL`:

- `CC(=O)O` em `pH 12` é convertido para `CC(=O)[O-]`
- `CN` em `pH 2` é convertido para `C[NH3+]`
- Diaminas como `NCCCCN` em `pH 7.4` recebem protonação seletiva conforme o pKa local, evitando a protonação duplicada característica do modo `-p` do Open Babel.

## Paralelização e escalabilidade

Configurável em `config/settings.yaml` na seção `parallel`:

```yaml
parallel:
  enabled: true
  n_jobs: -1        # -1 => todos os núcleos; 1 => sequencial
  backend: loky
  batch_size: auto
```

O benchmark de throughput está disponível em [scripts/benchmark.py](scripts/benchmark.py):

```bash
python scripts/benchmark.py --input data/raw/zinc_sample.csv --sizes 100 1000 --jobs 1 4 8
```

O script gera CSV em `data/reports/benchmark_<timestamp>.csv` com tempos absolutos, throughput e estágio.

## Refinamento semi-empírico opcional (MOPAC)

Desativado por padrão. Para ativar:

```yaml
structure_generation:
  mopac:
    enabled: true
    method: PM7
    binary: mopac
    keywords: "PM7 PRECISE GNORM=0.01"
    max_seconds: 120
```

O refinamento é aplicado após a cascata de campo de força. Em caso de falha do executável, o pipeline mantém a geometria do campo de força e registra `mopac_status=failed` na molécula e no relatório.

## Interface gráfica

Execute:

```bash
python scripts/run_gui.py
```

A interface permite:

- selecionar o arquivo de entrada
- escolher a aba Excel
- ajustar as colunas `access_code` e `smiles`
- definir o pH de protonação
- escolher entre arquivos `MOL2` separados, arquivos `SDF` separados, `MOL2` único ou `SDF` único
- editar o nome base de saída; em exportação separada ele funciona como prefixo opcional
- rodar em segundo plano, minimizando a janela e evitando pop-ups de conclusão/erro
- alternar a interface entre inglês e português por um seletor visível na janela principal
- escolher o diretório final para estruturas, relatório JSON e log de execução

## Linha de comando

Exemplo com Excel:

```bash
python scripts/run_workflow.py --input data/raw/molecules.xlsx --sheet Molecules --ph 7.4
```

Exemplo com CSV:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --smiles-column smiles --access-code-column access_code --ph 6.8
```

Exemplo com exportação em arquivo único SDF:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --export-mode single_sdf --output-name ligands_pH68
```

Exemplo com exportação PDBQT pronta para `AutoDock Vina`:

```bash
python scripts/run_workflow.py --input data/raw/sample_molecules.csv --export-mode separate_pdbqt --ph 7.4
```

## Diretórios de execução

Quando os campos `output_dir`, `temp_dir` e `report_dir` em `config/settings.yaml` estão vazios, o pipeline resolve automaticamente para o diretório de dados do usuário do sistema operacional:

| SO | Caminho |
|----|---------|
| Windows | `%APPDATA%\smiles2docking\` |
| Linux | `$XDG_DATA_HOME/smiles2docking/` (padrão `~/.local/share/smiles2docking/`) |
| macOS | `~/Library/Application Support/smiles2docking/` |

Isso evita falhas em distribuições somente leitura, como o `AppImage` (problema reportado anteriormente em `/tmp/.mount_*/usr/lib/smiles2docking/_internal/data/intermediate`).

## Arquitetura

```text
SMILES2Docking/
├── AUTHORS.md
├── CITATION.cff
├── LICENSE
├── README.md
├── docs/
├── environment/
├── packaging/
├── config/
├── data/
├── logs/
├── scripts/
├── src/
└── tests/
```

## Ambiente

Arquivo principal:

- [environment/environment.yml](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/environment/environment.yml)

Criação sugerida:

```bash
conda env create -f environment/environment.yml
conda activate smiles2docking
```

## Build do executável Windows

Use o ambiente `smiles2docking` ativo e rode:

```bash
packaging\windows\build_executable.bat
```

O build gera uma pasta em `dist/SMILES2DockingDesktop/`.

## Build do pacote Linux

O empacotamento Linux está preparado em:

- [packaging/linux/build_portable.sh](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/linux/build_portable.sh)
- [packaging/linux/smiles2docking.spec](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/linux/smiles2docking.spec)

Em um host Linux `x86_64`, com o ambiente `smiles2docking` ativo:

```bash
chmod +x packaging/linux/build_portable.sh
./packaging/linux/build_portable.sh
```

O processo gera:

- um `AppDir` portátil
- um `tar.gz` distribuível
- um `tar.gz` com o código-fonte
- opcionalmente um `.AppImage`, se `appimagetool` estiver instalado

Detalhes completos em [docs/LINUX_DISTRIBUTION.md](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/docs/LINUX_DISTRIBUTION.md).

## Distribuição aberta e notices

Os documentos de distribuição e de terceiros estão em:

- [docs/DISTRIBUTION.md](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/docs/DISTRIBUTION.md)
- [docs/THIRD_PARTY_NOTICES.md](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/docs/THIRD_PARTY_NOTICES.md)

## Licença do projeto

Este repositório está configurado para distribuição aberta sob `GPL-2.0-or-later`, para manter compatibilidade com o uso do Open Babel na aplicação distribuída. Veja [LICENSE](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/LICENSE).

## Publicação no GitHub

O projeto já está estruturado para publicação aberta no GitHub com:

- código-fonte do workflow e da interface desktop
- scripts de build para Windows e Linux
- licença do projeto
- arquivo de citação
- autoria identificada
- documentação de distribuição e notices de terceiros

Quando finalizarmos a interface e o comportamento do aplicativo, a publicação no GitHub pode ser feita mantendo o repositório como fonte oficial e distribuindo os builds gerados como assets de release.
