# Deployment Setup

Tento dokument popisuje, jak nastavit automatickou publikaci na PyPI pomocí GitHub Actions.

## Nastavení PyPI API tokenů

### 1. Vytvoření PyPI API tokenu

1. Jděte na https://pypi.org/manage/account/
2. Přejděte na sekci "API tokens"
3. Klikněte na "Add API token"
4. Vyberte "Entire account" nebo specifický projekt
5. Zkopírujte vygenerovaný token (začíná `pypi-`)

### 2. Vytvoření TestPyPI API tokenu (volitelné)

1. Jděte na https://test.pypi.org/manage/account/
2. Opakujte stejný postup jako pro PyPI
3. Zkopírujte vygenerovaný token

### 3. Nastavení GitHub Secrets

V GitHub repository:

1. Jděte na `Settings` → `Secrets and variables` → `Actions`
2. Přidejte následující secrets:
   - `PYPI_API_TOKEN`: Váš PyPI API token
   - `TEST_PYPI_API_TOKEN`: Váš TestPyPI API token (volitelné)

## Workflow spouštění

### Hlavní CI/CD Pipeline (`ci-cd.yml`)

**Spouští se při:**
- Push na `master` nebo `main` branch
- Pull requests na `master` nebo `main` branch
- Vytvoření GitHub Release

**Akce:**
- Testuje na Python 3.8-3.12
- Spouští linting (flake8)
- Spouští testy (pytest)
- Testuje build balíčku
- **Publikuje na PyPI** pouze při vytvoření GitHub Release

### TestPyPI Pipeline (`test-pypi.yml`)

**Spouští se při:**
- Push na `develop` branch
- Manuálně přes GitHub Actions UI

**Akce:**
- Publikuje na TestPyPI pro testování

## Jak publikovat novou verzi

### 1. Příprava release

```bash
# Upravte verzi v pyproject.toml
# Commitněte změny
git add pyproject.toml
git commit -m "Bump version to 1.0.1"
git push origin master
```

### 2. Vytvoření GitHub Release

1. Jděte na GitHub repository
2. Klikněte na "Releases"
3. Klikněte na "Create a new release"
4. Vytvořte nový tag (např. `v1.0.1`)
5. Vyplňte release notes
6. Klikněte na "Publish release"

### 3. Automatická publikace

GitHub Actions automaticky:
- Spustí testy
- Vybuiluje balíček
- Publikuje na PyPI

## Testování před publikací

### Publikace na TestPyPI

```bash
# Vytvořte develop branch
git checkout -b develop
git push origin develop
```

Nebo manuálně spusťte workflow přes GitHub Actions UI.

### Lokální testování

```bash
# Build balíček
python -m build

# Zkontrolujte balíček
twine check dist/*

# Publikujte na TestPyPI (manuálně)
twine upload --repository testpypi dist/*
```

## Monitoring

- Sledujte GitHub Actions na `Actions` tab
- Kontrolujte PyPI na https://pypi.org/project/pyCCMM/
- Testujte instalaci: `pip install pyCCMM`

## Troubleshooting

### Chyby při publikaci

1. **Token chyby**: Zkontrolujte GitHub Secrets
2. **Version conflicts**: Ujistěte se, že verze v `pyproject.toml` je nová
3. **Build chyby**: Zkontrolujte logy v GitHub Actions

### Testování workflow

```bash
# Lokální test
act -j test  # Vyžaduje nektar/act

# Nebo použijte GitHub Actions UI pro manuální spuštění
```
