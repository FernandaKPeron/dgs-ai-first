# Evidência 01 — Mapeamento MCP

## Identificação

- Exercício: Desenvolvedor 2.1 — Configuração e uso real de MCP servers no projeto
- Artefato: Mapeamento necessidade → MCP server
- Ferramenta usada: Claude Chat
- Chat/evidência associada: ![mapeamento](01-mapeamento-mcp.png)

## Prompt utilizado

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

## Resultado gerado pela IA

```markdown
Antes da arquitetura, um ponto factual que muda o desenho: confirmei na documentação atual dos reference servers que o `@modelcontextprotocol/server-filesystem`, quando iniciado via `npx` com pastas passadas por argumento, concede **leitura *e* escrita** a todas elas — o `ro` (read-only determinístico por pasta) só existe no modo Docker, via `--mount type=bind,...,ro`. Adicionar a flag `ro` torna o diretório somente-leitura no servidor, mas isso é uma capacidade do bind mount do Docker, não dos argumentos de linha de comando. Isso afeta diretamente a necessidade 2 e 3, e trato disso na seção de limitações.

---

## 1. Mapeamento

| Necessidade | Server | Tools / resources / prompts esperados | Quem consome | Escopo / pastas | Permissão | Justificativa (least privilege) | Risco se escopo amplo demais |
|---|---|---|---|---|---|---|---|
| **1.** Ler/escrever código, specs, skills | `fs-code` (filesystem) | `read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `create_directory`, `list_directory`, `directory_tree`, `move_file`, `search_files`, `get_file_info`. Resource: roots `file://` das 3 pastas | Agente (autoria de artefatos) | `src/`, `specs/`, `skills/` — **`.mcp/` deliberadamente fora** | Leitura/escrita | Escrita só onde o agente produz artefatos. Excluir `.mcp/` impede o agente reescrever a própria config (escalada de privilégio) | Agente edita `.mcp/mcp.json`, `.env`, `node_modules` ou sobrescreve histórico; corrupção silenciosa de toda a árvore |
| **2.** Ler docs de negócio | `fs-docs` (filesystem) | Só tools de leitura: `read_text_file`, `read_multiple_files`, `list_directory`, `directory_tree`, `search_files`, `get_file_info` | Agente (RAG/contexto) | `docs/novatech/` | Leitura (intencional) | Documentação de negócio é fonte, não destino. Sem motivo para escrita | Agente altera/apaga a fonte da verdade de negócio sem rastro |
| **3.** Ler corpus de chunks | `fs-docs` (mesma instância) | Idem acima | Pipeline de retrieval do agente | `data/retrieval-corpus/` | Leitura (intencional) | Corpus é imutável em runtime; escrita só pertence ao job de ingestão, fora do agente | Poisoning do corpus: agente injeta chunks e contamina respostas futuras |
| **4.** Git: histórico, branches, diff | `git` (git) | Leitura: `git_status`, `git_log`, `git_diff`, `git_diff_staged`, `git_diff_unstaged`, `git_show`, `git_branch`. **Não pretendidos:** `git_commit`, `git_add`, `git_reset`, `git_create_branch`, `git_checkout`, `git_init` | Agente (inspeção) | Repo `novatech-assistant` (raiz, requisito do server) | Leitura (intencional) | Necessidade é só inspeção. O server expõe escrita, mas não a usamos | Commits/checkout/reset automáticos mexem no estado do working tree e na história |
| **5.** Memória persistente de decisões e linguagem ubíqua | `memory` (memory) | `create_entities`, `create_relations`, `add_observations`, `read_graph`, `search_nodes`, `open_nodes`, `delete_*` | Agente (knowledge graph) | Arquivo único: `.mcp/memory/novatech-memory.json` (via `MEMORY_FILE_PATH`) | Leitura/escrita (só o arquivo de memória) | Escrita confinada a um arquivo dedicado, fora dos escopos de `fs-code`/`fs-docs` | Memória gravada em local arbitrário; mistura com código versionado; vazamento de decisões sensíveis |
| **6.** Explorar primitivas de MCP | `everything` (everything) | Demo de tools (`echo`, `add`, `longRunningOperation`, `sampleLLM`, `getTinyImage`), resources e prompts de exemplo, sampling | Desenvolvedor/agente (aprendizado) | **Nenhum** — sandbox sem FS/git | Nenhuma (isolado) | Server de teste; não deve tocar dados reais | `printEnv`/`sampleLLM` expõem variáveis de ambiente ou disparam custo/efeitos se conectado a dados reais |

---

## 2. `.mcp/mcp.json` final

Substitua `/abs/novatech-assistant` pelo caminho absoluto real do repositório (o filesystem server exige caminhos absolutos).

```json
{
  "mcpServers": {
    "fs-code": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/abs/novatech-assistant/src",
        "/abs/novatech-assistant/specs",
        "/abs/novatech-assistant/skills"
      ]
    },
    "fs-docs": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/abs/novatech-assistant/docs/novatech",
        "/abs/novatech-assistant/data/retrieval-corpus"
      ]
    },
    "git": {
      "command": "uvx",
      "args": [
        "mcp-server-git",
        "--repository",
        "/abs/novatech-assistant"
      ]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "/abs/novatech-assistant/.mcp/memory/novatech-memory.json"
      }
    },
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    }
  }
}
```

Decisões embutidas: duas instâncias de filesystem (uma escrita, uma intenção-leitura) para não dar escrita ao corpus/docs; `.mcp/` ausente de `fs-code`; memória em arquivo dedicado fora dos escopos de FS; `git` sem escopo de FS para não duplicar acesso; `everything` sem nenhum acesso a dados.

---

## 3. Justificativa de least privilege

A separação `fs-code` × `fs-docs` é o núcleo: cada uma é um *processo* distinto, então mesmo que o cliente não distinga tools por anotação, o limite de escopo é por processo — `fs-docs` literalmente não enxerga `src/`, e `fs-code` não enxerga o corpus. Isso reduz o raio de impacto de qualquer prompt malicioso ou alucinação de escrita.

Excluir `.mcp/` de toda permissão de escrita é deliberado: se o agente pudesse editar `mcp.json`, poderia ampliar o próprio escopo — quebra do modelo de privilégio. Pelo mesmo motivo o arquivo de memória vai para `.mcp/memory/`, que nenhum filesystem server alcança, então o agente grava memória apenas pelo protocolo do `memory` server, nunca como arquivo livre.

O `git` recebe a raiz porque o server precisa do repositório inteiro para funcionar, mas a *intenção* declarada é só leitura. Como o server não tem flag read-only, o controle real fica no cliente (ver limitações). O `everything` fica sem qualquer ligação a dados reais — é didático e nada mais.

---

## 4. Limitações e mitigação

**(a) Filesystem não tem read-only determinístico por pasta via `npx`.** Confirmado: todas as operações ficam restritas aos diretórios permitidos, mas dentro deles a escrita é liberada. A instância `fs-docs` acima é "read-only por intenção", não por enforcement. Mitigações, em ordem de robustez:

1. **Docker com `ro`** (determinístico, local e gratuito) — troque `fs-docs` por:
   ```json
   "fs-docs": {
     "command": "docker",
     "args": [
       "run", "-i", "--rm",
       "--mount", "type=bind,src=/abs/novatech-assistant/docs/novatech,dst=/projects/docs,ro",
       "--mount", "type=bind,src=/abs/novatech-assistant/data/retrieval-corpus,dst=/projects/corpus,ro",
       "mcp/filesystem", "/projects"
     ]
   }
   ```
   Aqui o `ro` é aplicado pelo kernel via bind mount — escrita falha mesmo se a tool for chamada.
2. **Permissão de SO** — rodar o processo `fs-docs` sob um usuário com acesso somente-leitura a essas pastas (ACL/`chmod`).
3. **Filtro de tools no cliente** — o server publica anotações MCP (`readOnlyHint`); isso permite ao cliente distinguir tools somente-leitura das que escrevem. Configure o cliente para expor de `fs-docs` apenas as tools de leitura. É a camada mais fraca (depende do cliente respeitar) e deve complementar 1 ou 2, não substituir.

**(b) Git não tem modo read-only.** O `mcp-server-git` empacota leitura e escrita no mesmo processo (`git_commit`, `git_add`, `git_reset`, `git_checkout` existem). Não há flag para desligá-las. Mitigação: filtrar tools no cliente para liberar apenas as de inspeção; se o cliente não suportar filtro, documentar como controle compensatório e auditar logs. Como camada extra, o usuário do processo git pode ter o working tree montado read-only, deixando `git_log`/`git_diff`/`git_show` funcionando e quebrando os comandos que escrevem.

**(c) Versões não fixadas.** `npx -y` e `uvx` resolvem a versão mais recente no momento — comportamento pode mudar entre execuções. Mitigação: fixar versão (`@modelcontextprotocol/server-filesystem@<x.y.z>`, `mcp-server-git==<x.y.z>`) após validar, e registrar as versões resolvidas.

**(d) `everything` e `printEnv`/`sampleLLM`.** Em sandbox isolado o risco é baixo, mas `printEnv` pode revelar variáveis de ambiente e `sampleLLM` aciona o cliente. Mitigação: manter `everything` desabilitado por padrão e ligar só em sessões de estudo, sem segredos no ambiente do processo.

---

## 5. Checklist de evidências a coletar

- [ ] `mcp.json` passa em um validador JSON (ex.: `jq . .mcp/mcp.json`).
- [ ] Para `fs-code` e `fs-docs`, chamar `list_allowed_directories` e confirmar que retorna **exatamente** as pastas pretendidas — sem `$HOME`, `.env`, `node_modules`, raiz do repo ou workspace inteiro.
- [ ] Teste negativo de escrita em `fs-docs`: tentar `write_file`/`edit_file` em `docs/novatech/` e em `data/retrieval-corpus/`. Se **suceder**, a limitação (a) está confirmada → aplicar a mitigação Docker `ro` ou SO antes de produção.
- [ ] Teste positivo de escrita em `fs-code` apenas em `src/`, `specs/`, `skills/`; teste negativo tentando escrever em `.mcp/` (deve falhar por estar fora do escopo).
- [ ] `git`: inventariar as tools expostas; confirmar que `git_commit/git_add/git_reset/git_checkout/git_create_branch` estão filtradas no cliente ou registrar o controle compensatório aplicado.
- [ ] Memória: provocar uma escrita (`create_entities`) e verificar que o arquivo aparece **só** em `.mcp/memory/novatech-memory.json`, e em nenhum outro lugar da árvore.
- [ ] Confirmar que `.mcp/memory/` não está dentro de nenhum escopo de filesystem (evita o agente manipular a memória como arquivo livre).
- [ ] `everything`: confirmar ausência de qualquer acesso a FS/git/rede e que está desligado fora de sessões de aprendizado.
- [ ] Registrar as versões resolvidas de cada server (npm/uvx) e fixá-las.
- [ ] Coletar/ativar logs de auditoria por server (quem chamou qual tool, em qual caminho) para revisão.

Se quiser, posso gerar também um script de validação que executa os testes positivos/negativos de escrita e o dump de `list_allowed_directories` automaticamente.
```

## Decisões de escopo

- Escopos com escrita permitida: `src/`, `specs/` e `skills/`, via server `fs-code`.
- Escopos tratados como somente leitura: `docs/novatech/` e `data/retrieval-corpus/`, via server `fs-docs`; a intenção é read-only, com mitigação recomendada por Docker bind mount `ro` ou controle de permissões do SO.
- Pastas explicitamente fora do escopo: home do usuário, raiz do workspace, `.env`, `node_modules`, `.git`, `.mcp/` e qualquer pasta fora de `novatech-assistant`.
- Limitações conhecidas do server escolhido: `@modelcontextprotocol/server-filesystem` via `npx` restringe diretórios, mas não impõe read-only por pasta; `mcp-server-git` também não possui modo read-only nativo.

## Checklist de aceite

- [x] O mapeamento usa apenas servers locais e gratuitos.
- [x] Cada necessidade do enunciado foi mapeada para um server.
- [x] O escopo do filesystem não aponta para a home do usuário nem para o workspace inteiro.
- [x] Docs e corpus foram tratados como read-only por configuração ou política explícita.
- [x] Há justificativa de least privilege para cada server.
- [x] Há pelo menos um risco identificado para escopo amplo demais.
