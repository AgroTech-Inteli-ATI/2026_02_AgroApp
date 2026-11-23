# AgroApp

Guias técnicos: [dataset (T14.1)](docs/T14_1_Dataset_Final.md), [treinamento (T14.2)](docs/T14_2_Pipeline_Treinamento.md), [avaliação e conversão (T14.3)](docs/T14_3_Avaliacao_Conversao.md), [arquitetura web (T14.4)](docs/T14_4_Arquitetura_Web.md), [retreinamento, atualização e reversão (T14.5)](docs/T14_5_Guia_Retreinamento.md) e [validação externa do guia (T14.6)](docs/T14_6_Validacao_Externa.md).

Medição dos modelos finais e do pacote web: [Validação T12.1](docs/Validacao_T12_1.md).

Entrega da Sprint 5: [checklist final (T15.1)](docs/T15_1_Checklist_Final.md), [roteiro e ensaio (T15.2)](docs/T15_2_Roteiro_Demonstracao.md) e [pacote e validação com o parceiro (T15.3)](docs/T15_3_Entrega_Parceiro.md).

Repositório do projeto AgroApp — AgroTech Inteli ATI, 2026/02.

## Sumário

- [Estrutura de pastas](#estrutura-de-pastas)
- [Documentação](docs/Projeto.md)
- [Código-fonte](src/)
- [Testes](tests/)
- [Recursos](assets/)
- [Frontend de análise visual](frontend/README.md)

## Testar o modelo no navegador

A interface React + TypeScript executa o modelo diretamente no navegador, sem backend.

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Abra o endereço indicado no terminal e adicione uma foto. Consulte [as instruções do frontend](frontend/README.md) para build, publicação e verificações.

## Estrutura de pastas

```text
.
├── assets/           # Imagens e outros recursos do projeto
├── docs/             # Documentação do projeto
│   └── Projeto.md    # Documentação e sumário do projeto
├── frontend/         # Interface React e inferência no navegador
├── src/              # Código-fonte da aplicação
├── tests/            # Testes automatizados
└── README.md         # Apresentação e sumário do projeto
```
