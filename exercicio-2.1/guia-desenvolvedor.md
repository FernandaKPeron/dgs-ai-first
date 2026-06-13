# Guia — Desenvolvedor 2.1: Configuração e uso real de MCP servers

## Objetivo do exercício

Configurar MCP servers locais e gratuitos para o projeto `novatech-assistant`, aplicar least privilege, subir os servers e produzir evidências de que o agente consegue:

1. listar e ler documentos de `docs/novatech/`;
2. recuperar chunks relevantes em `data/retrieval-corpus/`;
3. ler o histórico do repositório via `git`;
4. explicar riscos locais de segurança e mitigações.

## Artefatos esperados nesta pasta

- `01-mapeamento-mcp.md` — saída do Claude com o mapeamento necessidade → server.
- `02-mcp-json-final.md` — cópia comentada do `.mcp/mcp.json` final e justificativa de escopo.
- `03-evidencia-docs-mcp.md` — evidência do agente lendo `docs/novatech/` via MCP.
- `04-evidencia-corpus-mcp.md` — evidência do agente recuperando chunks via MCP.
- `05-evidencia-git-mcp.md` — evidência do agente consultando histórico local via MCP git.
- `06-riscos-seguranca-mcp.md` — riscos locais e mitigações.

## Passo a passo

1. Abra um chat novo no Claude para gerar o mapeamento usando o Prompt A.
2. Atualize `novatech-assistant/.mcp/mcp.json` com a configuração final validada.
3. Reinicie/ative o agente com os MCP servers do projeto.
4. Em chats separados, rode os prompts B, C e D para obter evidências limpas.
5. Salve cada evidência nos arquivos listados acima.

## Configuração-base recomendada para `.mcp/mcp.json`

Use dois servers de filesystem para separar intenção de escrita e leitura. O reference server de filesystem pode não impor read-only por pasta em todas as versões; por isso, trate `filesystem-knowledge` como escopo de leitura por política e registre essa limitação/mitigação na análise de riscos.

```json
{
  "mcpServers": {
    "filesystem-workspace": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "./src",
        "./specs",
        "./skills",
        "./.mcp"
      ]
    },
    "filesystem-knowledge": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "./docs/novatech",
        "./data/retrieval-corpus"
      ]
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "."]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    }
  }
}
```

## Prompt A — Mapeamento MCP com Claude

```text
Você é um arquiteto de integração de agentes trabalhando no projeto local NovaTech Assistant.

Contexto:
- O projeto usa MCP servers locais e gratuitos, sem serviços pagos/externos.
- O repositório local é `novatech-assistant`.
- Necessidades do agente:
  1. Ler/escrever código, specs e skills do repositório.
  2. Ler documentação de negócio em `docs/novatech/`.
  3. Ler corpus de chunks em `data/retrieval-corpus/`.
  4. Consultar histórico, branches e diff do Git local.
  5. Manter memória persistente de decisões e linguagem ubíqua.
  6. Explorar primitivas de MCP para aprendizado.
- Estrutura relevante:
  - `.mcp/mcp.json`
  - `src/`, `specs/`, `skills/`
  - `docs/novatech/`
  - `data/retrieval-corpus/`

Tarefa:
Mapeie cada necessidade para um reference server MCP local e gratuito: filesystem, git, memory e everything.

Para cada server, responda em tabela com:
- necessidade atendida;
- server;
- tools/resources/prompts esperados;
- quem consome;
- escopo/pastas;
- permissão pretendida: leitura ou leitura/escrita;
- justificativa de least privilege;
- risco se o escopo for amplo demais.

Depois proponha o `.mcp/mcp.json` final em JSON válido e explique qualquer limitação, especialmente se o filesystem server não suportar read-only determinístico por pasta.

Regras:
- Não use GitHub, Azure, Confluence ou serviços externos.
- Não inclua pastas fora do necessário, como home do usuário, `.env`, `node_modules` ou workspace inteiro.
- Seja prescritivo e específico ao projeto NovaTech.

Formato de saída:
1. Mapeamento em tabela.
2. `.mcp/mcp.json` final.
3. Justificativa de least privilege.
4. Limitações e mitigação.
5. Checklist de evidências que preciso coletar.
```

## Prompt B — Evidência de documentação via MCP

```text
Use somente os MCP servers locais disponíveis para provar que você consegue acessar a documentação de negócio da NovaTech.

Tarefa:
1. Liste os arquivos disponíveis em `docs/novatech/` usando MCP filesystem.
2. Leia o documento `POL-001-politica-devolucao.md` usando MCP filesystem.
3. Extraia a regra de devolução para carga perigosa.
4. Responda com:
   - ferramenta MCP usada;
   - arquivos lidos;
   - trecho relevante com seção/documento;
   - conclusão em português.

Restrições:
- Não responda por memória.
- Não use busca web.
- Não invente seção se ela não aparecer no documento.
```

## Prompt C — Evidência de retrieval de chunk via MCP

```text
Use somente os MCP servers locais para simular retrieval no corpus NovaTech.

Pergunta do atendente: "Posso devolver carga perigosa?"

Tarefa:
1. Leia `data/retrieval-corpus/chunks-novatech.md` via MCP filesystem.
2. Consulte o mapa de cobertura pergunta → chunks.
3. Identifique quais chunks DEVEM ser recuperados para a pergunta.
4. Leia o conteúdo dos chunks relevantes.
5. Responda com:
   - ferramenta MCP usada;
   - arquivo lido;
   - chunks recuperados;
   - justificativa de relevância;
   - resposta curta que o assistente deveria dar, citando fonte.

Restrições:
- Use apenas informação presente nos chunks recuperados.
- Se houver chunk de relevância menor, marque como secundário.
```

## Prompt D — Evidência de Git via MCP

```text
Use o MCP server de Git local para consultar o repositório `novatech-assistant`.

Tarefa:
1. Mostre a branch atual.
2. Liste os commits recentes disponíveis no histórico local.
3. Mostre se existem arquivos modificados no working tree.
4. Responda com:
   - ferramenta MCP usada;
   - branch atual;
   - commits retornados;
   - resumo do status do working tree.

Restrições:
- Não use GitHub remoto.
- Não faça commit, checkout, reset ou qualquer ação destrutiva.
```

## Prompt E — Riscos e mitigações

```text
Você é um revisor de segurança avaliando a configuração local de MCP do projeto NovaTech Assistant.

Contexto:
- Servers locais: filesystem-workspace, filesystem-knowledge, git, memory, everything.
- `filesystem-workspace` tem escopo de escrita pretendido para `src/`, `specs/`, `skills/` e `.mcp/`.
- `filesystem-knowledge` aponta para `docs/novatech/` e `data/retrieval-corpus/`, tratados como read-only por política.
- O repositório é local; não há GitHub, Azure ou Confluence nesta fase.

Tarefa:
Liste pelo menos 2 riscos de segurança específicos deste setup local e proponha mitigação acionável para cada um.

Inclua obrigatoriamente:
- risco de filesystem com escopo amplo demais expondo `.env`/segredos;
- risco de escrita acidental ou indevida em docs/corpus;
- risco de memory server persistir dados sensíveis ou decisões incorretas;
- risco de git server permitir inspeção de histórico com segredos antigos.

Formato:
Tabela com risco, impacto, exemplo no projeto, mitigação, evidência/verificação.
```
