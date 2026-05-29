## Análise das respostas (v1) — resumo

| # | Pergunta | Conteúdo | Citou fonte? | Guardrails | Erro |
|---|---|---|---|---|---|
| 1 | Prazo de devolução p/ carga perigosa | ✅ Correto — leu que carga perigosa é exceção à regra de 7 dias e que nenhum prazo alternativo é dado; abstenção correta | ⚠️ Parcial | ✅ Não inventou prazo (2, 3, 5, 7) | Pôs o tema `(Devolução)` no lugar da área dona; sem versão/data |
| 2 | SLA de resolução cliente Gold | ✅ Correto — 24h resolução / 2h resposta, exato | ⚠️ Parcial | ✅ Respeita todos; conciso | Mesmo erro: tema `(SLA por tipo de cliente)` no lugar da área; sem versão/data |
| 3 | Frete 600 kg para Manaus | ✅ Excelente — recusou presumir Manaus = Norte; abstenção dupla (valor base ausente + região não definida) | ⚠️ Parcial | ✅ Modelo de comportamento (2 e 5) | Mesmo erro de área dona (`v2` no código já conta como versão) |

### Conclusão
- **Raciocínio sólido nas três:** nenhum número inventado, abstenções corretas, sem uso de conhecimento de mundo (caso Manaus é exemplar).
- **Único defeito, sistemático:** o campo **"área dona"** da citação — o modelo preencheu com o *tema* do documento em vez da área (Operações/Compliance/Comercial).
- **Causa-raiz no prompt, não no modelo:** a Regra 1 + o FORMATO exigiam área/versão/data como obrigatórios, mas os chunks de teste não carregam esse metadado. Os exemplos do prompt (`— Comercial`) ensinaram o formato `— algo`, e sem o dado o modelo preencheu com o tema. Ele agiu certo ao **não fabricar** a área.
- **Correção aplicada (v2):** citar só os metadados presentes no trecho; nunca usar tema como área; campos da linha `Fonte` viram condicionais. Conteúdo das respostas não muda — só a linha `Fonte`.
- **Conserto definitivo:** é na **ingestão**, não no prompt — a citação só fica completa quando o chunk trouxer área e data.