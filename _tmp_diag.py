from pathlib import Path
text = Path('main.py').read_text(encoding='utf-8')
start = text.index('# Di')
end = text.index('# Indicador')
print(text[start:end])
