# Distribution Guide

## Scope

This project is intended for open distribution as a packaged desktop application and as source code.

## Project Identity

- Name: SMILES2Docking
- Author: Adriano Marques Gonçalves
- Affiliation: Universidade de Araraquara - UNIARA
- Contact: amgoncalves@uniara.edu.br
- Project license: GPL-2.0-or-later

## Distribution Model

The recommended Windows distribution is a `PyInstaller` one-folder build generated from [packaging/windows/smiles2docking.spec](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/windows/smiles2docking.spec).

The recommended Linux distribution is a portable `PyInstaller` build staged as an `AppDir` and archived as `tar.gz`, generated from [packaging/linux/smiles2docking.spec](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/linux/smiles2docking.spec).

The generated application bundles:

- the Python runtime
- the PySide6 desktop interface
- the RDKit runtime
- the Open Babel executable and data files
- the local project code

This means end users do not need to install Python separately.

For Linux releases, the packaging also includes:

- an `AppRun` launcher
- a desktop entry
- an application icon
- a source archive created alongside the portable binary archive

## Open-Source Distribution Requirements

When distributing a binary build, also distribute or publish alongside it:

1. The corresponding source code of this project.
2. The project license file.
3. The third-party notices file.
4. Any copyright and attribution notices required by bundled dependencies.

## Why the project license is GPL-compatible

The packaged application uses Open Babel. Open Babel documentation describes the project as GPL-based and its historical/library documentation points to GPL terms for use and redistribution.

References:

- [Open Babel documentation](https://openbabel.org/api/2.0.2/)
- [Open Babel main site](https://openbabel.org/)

Because the distributed application bundles Open Babel in the executable distribution, the project is documented for open distribution and kept under a GPL-compatible project license.

## Packaging Tooling

PyInstaller states that it bundles Python applications and their dependencies into a package that users can run without separately installing Python.

References:

- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [PyInstaller License](https://pyinstaller.org/en/stable/license.html)

## GUI Toolkit

The desktop interface uses PySide6, the official Qt for Python bindings. Qt for Python documentation states that the project is available under LGPLv3, GPLv3, and commercial terms.

Reference:

- [Qt for Python](https://doc.qt.io/qtforpython-6.5/)

For this project's open distribution model, the application is distributed openly and accompanied by source code and notices.

## Build Procedure

1. Activate the `smiles2docking` environment.
2. Run [packaging/windows/build_executable.bat](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/windows/build_executable.bat).
3. Distribute the generated `dist/SMILES2DockingDesktop/` folder together with:
   - [LICENSE](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/LICENSE)
   - [AUTHORS.md](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/AUTHORS.md)
   - [CITATION.cff](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/CITATION.cff)
   - [docs/THIRD_PARTY_NOTICES.md](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/docs/THIRD_PARTY_NOTICES.md)

For Linux:

1. Activate the `smiles2docking` environment on a Linux `x86_64` machine.
2. Run [packaging/linux/build_portable.sh](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/packaging/linux/build_portable.sh).
3. Distribute the generated portable archive, plus the source archive generated in the same release directory.
4. Include:
   - [LICENSE](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/LICENSE)
   - [AUTHORS.md](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/AUTHORS.md)
   - [CITATION.cff](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/CITATION.cff)
   - [docs/THIRD_PARTY_NOTICES.md](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/docs/THIRD_PARTY_NOTICES.md)
   - [docs/LINUX_DISTRIBUTION.md](C:/Users/adria/OneDrive/Documents/Projetos%20IA/SMILES2Docking/docs/LINUX_DISTRIBUTION.md)

## Recommended Release Contents

- executable folder
- project source archive
- third-party notices
- license file
- versioned changelog if available
