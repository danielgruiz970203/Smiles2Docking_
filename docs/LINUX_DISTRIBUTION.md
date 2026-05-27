# Linux Distribution Guide

## Scope

This project includes Linux packaging assets for a portable desktop distribution based on `PyInstaller`.

The Linux packaging workflow produces:

- an `AppDir` tree ready for local execution
- a portable `.tar.gz` archive for open distribution
- an optional `.AppImage` when `appimagetool` is available on the Linux build host
- a matching source-code archive for GPL-compatible redistribution

## Packaging Files

Linux packaging resources live in:

- [packaging/linux/build_portable.sh](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/linux/build_portable.sh)
- [packaging/linux/smiles2docking.spec](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/linux/smiles2docking.spec)
- [packaging/linux/AppRun](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/linux/AppRun)
- [packaging/linux/run_smiles2docking.sh](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/linux/run_smiles2docking.sh)
- [packaging/linux/SMILES2DockingDesktop.desktop](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/linux/SMILES2DockingDesktop.desktop)
- [packaging/linux/smiles2docking.svg](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/linux/smiles2docking.svg)

## Build Host Requirements

Build on a Linux `x86_64` machine with:

- `conda` or `mamba`
- the environment from [environment/environment.yml](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/environment/environment.yml)
- `tar`
- optionally `appimagetool` for `.AppImage`

## Recommended Build Steps

```bash
conda env create -f environment/environment.yml
conda activate smiles2docking
chmod +x packaging/linux/build_portable.sh
./packaging/linux/build_portable.sh
```

## Generated Artifacts

The Linux build script writes to [release](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/release):

- `release/linux/SMILES2DockingDesktop-x86_64.AppDir`
- `release/linux/SMILES2DockingDesktop-linux-x86_64.tar.gz`
- `release/linux/SMILES2Docking-source.tar.gz`
- optionally `release/linux/SMILES2DockingDesktop-x86_64.AppImage`

## End-User Installation

For the portable archive:

```bash
tar -xzf SMILES2DockingDesktop-linux-x86_64.tar.gz
cd SMILES2DockingDesktop-x86_64.AppDir
./AppRun
```

To install a launcher in the current user session:

```bash
mkdir -p ~/.local/share/applications
cp SMILES2DockingDesktop.desktop ~/.local/share/applications/
```

If desired, update the `Exec=` and `Icon=` entries to the final extraction path.

## Runtime Notes

- The launcher exports `LD_LIBRARY_PATH` for bundled Open Babel and PyInstaller-shipped shared libraries.
- The Python runtime also sets `BABEL_DATADIR` and `BABEL_LIBDIR` internally for packaged execution.
- Linux binaries should be built on a system with a glibc version compatible with the oldest target distribution you intend to support.

## Distribution Checklist

Distribute together:

1. The Linux portable archive or AppImage.
2. The source archive generated in the same release.
3. [LICENSE](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/LICENSE).
4. [AUTHORS.md](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/AUTHORS.md).
5. [CITATION.cff](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/CITATION.cff).
6. [docs/THIRD_PARTY_NOTICES.md](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/docs/THIRD_PARTY_NOTICES.md).

## Validation Status

The Linux packaging files are prepared in the repository, but they were not executed from this workstation because the current environment is Windows-only and has no WSL installed.
