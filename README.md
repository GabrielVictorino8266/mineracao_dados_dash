# Dashboard de Ocorrências Aeronáuticas no Brasil

Atividade de Acompanhamento 2 — Mineração e Visualização de Dados  
Entrega: 25 de outubro de 2026, às 23h59

## Resultado

O projeto apresenta um dashboard em Streamlit sobre acidentes e incidentes graves
da aviação civil brasileira. A aplicação possui filtros, indicadores, sete gráficos
interativos e uma tabela de consulta.

## Como executar

Abra o PowerShell nesta pasta e execute:

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py
```

Se a pasta `venv` não estiver disponível:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m streamlit run app.py
```

O navegador abrirá em `http://localhost:8501`.

## Executar com Docker

Esta é a opção recomendada para abrir o trabalho em outra máquina. É necessário
ter apenas o Docker Desktop instalado; Python e Streamlit ficam dentro da imagem.

Na pasta do projeto, construa a imagem:

```powershell
docker build -t mineracao-dash:latest .
```

Em seguida, execute o contêiner:

```powershell
docker run --rm -p 8501:8501 --name mineracao-dash mineracao-dash:latest
```

Abra <http://localhost:8501> no navegador. Para encerrar, pressione `Ctrl+C` no
terminal. Se a porta 8501 estiver ocupada, use `-p 8502:8501` e abra
<http://localhost:8502>.

Para conferir se o contêiner está saudável em outro terminal:

```powershell
docker ps --filter name=mineracao-dash
```

## Arquivos usados na entrega

- `app.py`: dashboard Streamlit final.
- `V_OCORRENCIA_AMPLA.csv`: base pública baixada da ANAC.
- `requirements.txt`: bibliotecas necessárias.
- `README.md`: documentação da entrega.
- `GUIA_DE_ESTUDO.md`: explicação e exercícios de aprendizagem.

## Base de dados

- Tema: ocorrências aeronáuticas no Brasil.
- Fonte: Agência Nacional de Aviação Civil (ANAC), com dados enviados pelo CENIPA.
- Página oficial: <https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos/areas-de-atuacao/seguranca-operacional/ocorrencias-aeronauticas>
- Download direto: <https://sistemas.anac.gov.br/dadosabertos/Seguranca%20Operacional/Ocorrencia/V_OCORRENCIA_AMPLA.csv>
- Data do download: 18/10/2026.
- Atualização declarada na primeira linha do arquivo: 18/10/2026.
- Período observado no arquivo: 11/01/1959 a 22/06/2024.
- Volume: 5.021 registros de aeronaves, ligados a 4.301 ocorrências únicas.
- Dimensão: 45 variáveis.

Cada linha representa uma aeronave associada a uma ocorrência. Por isso, uma
ocorrência que envolveu duas aeronaves aparece em duas linhas. O dashboard elimina
essa repetição nos gráficos que contam ocorrências, mas preserva as linhas nas
análises de aeronaves, assentos, danos e lesões.

### Variáveis exigidas pela atividade

- Temporal: `Data_da_Ocorrencia` e `Hora_da_Ocorrencia`.
- Categóricas: `Classificacao_da_Ocorrencia`, `UF`, `Regiao`,
  `Fase_da_Operacao`, `Operacao` e outras.
- Numéricas: `Numero_de_Assentos`, `PMD`, latitude, longitude e quantidades de
  lesões e fatalidades.

### Limitações

- O arquivo foi atualizado em 2026, mas sua ocorrência mais recente é de junho de
  2024. Investigações e consolidações podem gerar atraso na publicação.
- Nem todos os registros possuem coordenadas, horário ou fase da operação.
- O conjunto contém apenas acidentes e incidentes graves; não representa todos os
  voos realizados nem permite calcular uma taxa por quantidade de voos.
- Associação estatística não demonstra causa. O gráfico de assentos e fatalidades
  deve ser interpretado apenas como análise exploratória.

## Perguntas respondidas

| Nº | Pergunta | Gráfico | Motivo da escolha |
|---:|---|---|---|
| 1 | Como acidentes e incidentes graves evoluíram ao longo do tempo? | Linhas | Mostra evolução temporal e permite comparar duas séries. |
| 2 | Quais UFs concentram o maior número de ocorrências? | Barras horizontais | Facilita a comparação e a leitura das siglas em ranking. |
| 3 | Quais tipos de ocorrência aparecem com maior frequência em cada classificação? | Mapa de árvore | Compara frequência e hierarquia sem depender de coordenadas ausentes. |
| 4 | Em quais fases da operação há mais ocorrências de cada classificação? | Barras empilhadas | Compara totais e composição com apenas duas séries. |
| 5 | Qual é a participação de acidentes e incidentes graves no total? | Rosca | Há apenas duas partes, dentro do limite de cinco fatias. |
| 6 | Em quais combinações de mês e horário há mais ocorrências? | Mapa de calor | Destaca padrões em uma matriz temporal sem muitas linhas. |
| 7 | Aeronaves com mais assentos apresentam mais fatalidades por registro? | Dispersão | Relaciona duas variáveis numéricas. |

