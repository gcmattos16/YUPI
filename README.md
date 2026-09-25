# YUPI — conferência de dados ambulatoriais

Projeto de portfólio em Python para comparar totais e identificar divergências em relatórios de consultas, exames e planilhas. Esta edição pública contém a interface e o núcleo de conferência da versão 6.5.4, com configurações de exemplo. O módulo experimental de automação do sistema interno e dados reais foram retirados.

## Tecnologias

Python, CustomTkinter, PyMuPDF e openpyxl.

## Como executar

1. Instale Python 3.11 ou superior.
2. Crie e ative um ambiente virtual.
3. Instale as dependências com `pip install -r requirements.txt`.
4. Execute `python main.py`.

O programa abre uma interface local. Para testar as conferências, use apenas documentos fictícios no formato esperado pelos leitores. A compatibilidade depende do layout dos relatórios de entrada. Não há dados de pacientes neste repositório.

## Estado do projeto

Em desenvolvimento. Os módulos de consultas, exames, SADT, conferência mensal e presença evoluem conforme os formatos de entrada e as regras de comparação. Esta publicação é uma demonstração de portfólio e não substitui a validação operacional dos resultados.

## Privacidade

Não publique relatórios, planilhas, históricos, prints ou documentos com informações de pacientes. As pastas de dados e formatos de exportação comuns estão no `.gitignore` por segurança adicional.
