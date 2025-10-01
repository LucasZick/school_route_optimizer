# --- Otimizador de Rota Escolar ---

## 1. Visão Geral

Este projeto é uma aplicação web completa desenvolvida em Flask para resolver o Problema de Roteamento de Veículos com Janela de Tempo (VRPTW), focado no transporte escolar. A aplicação permite cadastrar uma garagem, uma escola e múltiplos alunos, calculando a rota mais eficiente para o ônibus escolar, respeitando os horários de coleta/entrega de cada aluno e o horário de início ou fim das aulas.

A otimização é realizada em um processo assíncrono para não travar a interface do usuário, e a rota resultante é exibida em um mapa interativo.

---

## 2. Funcionalidades Principais

- **Interface Web Interativa:** Frontend desenvolvido com HTML, Bootstrap e Leaflet.js para visualização de pontos e rotas em um mapa.
- **Geocodificação de Endereços:** Converte endereços textuais em coordenadas geográficas (latitude, longitude) utilizando a API do OpenStreetMap através da biblioteca OSMnx.
- **Cálculo de Rota Realista:** Utiliza o grafo de ruas real da cidade (São Bento do Sul, SC, por padrão) para calcular o tempo de viagem entre os pontos.
- **Suporte para Rotas de Ida e Volta:**
  - **Ida:** Otimiza a rota de coleta de alunos, garantindo a chegada na escola *antes* de um horário estipulado.
  - **Volta:** Otimiza a rota de entrega dos alunos, iniciando a rota *após* um horário estipulado.
- **Janelas de Tempo Customizáveis:** Permite definir para cada aluno um intervalo de tempo em que ele deve ser coletado (ou entregue).
- **Otimização Assíncrona:** O cálculo da rota, que pode ser demorado, é executado em segundo plano, permitindo que o usuário continue interagindo com a aplicação.
- **Solver Meta-heurístico:** Utiliza um algoritmo de Otimização (Busca Local Iterada com 2-Opt) para encontrar soluções de alta qualidade para o problema de roteamento.
- **Geração de Dados de Teste:** Inclui uma ferramenta para adicionar alunos em localizações e horários aleatórios para facilitar testes e demonstrações.

---

## 3. Tecnologias Utilizadas

- **Backend:** Python
  - **Framework:** Flask
  - **Banco de Dados:** SQLite com Flask-SQLAlchemy
  - **Tarefas em Background:** Flask-Executor
  - **Geoprocessamento e Grafos:** OSMnx, NetworkX
- **Frontend:**
  - **Estrutura:** HTML5
  - **Estilo:** Bootstrap 5
  - **Mapas:** Leaflet.js
  - **Comunicação:** JavaScript (Fetch API)

---

## 4. Como Configurar e Executar o Projeto

### Pré-requisitos
- Python 3.8 ou superior
- `pip` (gerenciador de pacotes do Python)

### Passos para Instalação

1.  **Clone ou baixe os arquivos:**
    Coloque os arquivos `app.py`, `solver.py` e a pasta `templates` (contendo `index.html`) em um mesmo diretório.

2.  **Crie um Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv venv
    ```
    Ative o ambiente:
    - No Windows: `venv\Scripts\activate`
    - No Linux/macOS: `source venv/bin/activate`

3.  **Crie o arquivo `requirements.txt`:**
    Crie um arquivo chamado `requirements.txt` no mesmo diretório com o seguinte conteúdo:
    ```
    Flask
    Flask-SQLAlchemy
    Flask-Executor
    osmnx
    ```

4.  **Instale as Dependências:**
    Execute o comando abaixo no terminal para instalar todas as bibliotecas necessárias.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Execute a Aplicação:**
    ```bash
    python app.py
    ```

6.  **Acesse no Navegador:**
    Abra seu navegador e acesse o endereço: `http://127.0.0.1:5000`

---

## 5. Como Usar a Aplicação

1.  **Limpeza Inicial (Opcional):** Se um arquivo `school_routes.db` já existir de uma execução anterior, é recomendado apagá-lo para começar com dados limpos, especialmente após mudanças no código.

2.  **Cadastrar Garagem:** No painel "Adicionar Pontos", insira o endereço da garagem e clique em "Salvar".

3.  **Cadastrar Escola:**
    - Preencha o nome e o endereço da escola.
    - Selecione o **Tipo de Rota**: "Ida (Coleta)" ou "Volta (Entrega)".
    - Defina o **Horário**: "Chegar até" para rotas de ida, ou "Sair a partir de" para rotas de volta.
    - Clique em "Salvar".

4.  **Cadastrar Alunos:**
    - **Manualmente:** Preencha o nome, endereço e a janela de tempo para coleta do aluno e clique em "+ Adicionar".
    - **Aleatoriamente:** Use o botão "Adicionar +10 Alunos Aleatórios" na seção "Ferramentas de Teste" para popular o mapa rapidamente.

5.  **Calcular a Rota:**
    - Com todos os pontos cadastrados, clique no botão principal "Calcular Rota Otimizada".
    - Uma janela de "Calculando..." aparecerá. O processo pode levar de alguns segundos a um minuto, dependendo do número de alunos.

6.  **Visualizar Resultados:**
    - Ao final do cálculo, a rota otimizada será desenhada no mapa em roxo.
    - No painel direito, a seção "Itinerário da Rota" será exibida, mostrando a ordem das paradas e os horários calculados para cada uma.

---

## 6. Estrutura dos Arquivos

- `app.py`: Arquivo principal da aplicação Flask. Contém as rotas da API, a lógica de negócio, os modelos do banco de dados e a comunicação com o solver.
- `solver.py`: Módulo que contém a lógica do algoritmo de otimização para resolver o problema de roteamento.
- `templates/index.html`: Arquivo único que constitui toda a interface do usuário (frontend).
- `school_routes.db`: Arquivo do banco de dados SQLite, criado automaticamente na primeira execução.