# Desenvolvimento de Bibliotecas em Rust Integradas ao Python
 
Este guia mostra como criar módulos Python escritos em Rust, usando o ecossistema **PyO3** + **maturin**. Isso é útil quando você precisa de desempenho (loops pesados, processamento numérico, paralelismo) mas quer manter a ergonomia do Python na camada de uso.
 
## Pré-requisitos
 
- **Rust** (via `rustup`) — [https://www.rust-lang.org/tools/install](https://www.rust-lang.org/tools/install)
- **Python 3.8+** — [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **pip** (geralmente já vem com o Python)
Verifique as instalações:
 
```bash
rustc --version
python3 --version
pip3 --version
```
 
## Ambiente virtual (venv)
 
Recomenda-se isolar as dependências do projeto em um ambiente virtual Python, evitando conflitos com pacotes globais:
 
```bash
python3 -m venv .venv
```
 
Documentação oficial do `venv`: [https://docs.python.org/3/library/venv.html](https://docs.python.org/3/library/venv.html)
 
**macOS / Linux**
```bash
source .venv/bin/activate
```
 
**Windows (PowerShell)**
```powershell
.\.venv\Scripts\Activate.ps1
```
 
> Se o PowerShell bloquear a execução do script de ativação, rode `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` antes.
 
## Instalando o maturin
 
O [maturin](https://www.maturin.rs/) é a ferramenta padrão para compilar e empacotar projetos Rust como pacotes Python (wheels), cuidando de toda a integração entre `cargo` e `pip`.
 
```bash
pip3 install maturin
```
 
- Repositório oficial: [https://github.com/PyO3/maturin](https://github.com/PyO3/maturin)
- Documentação: [https://www.maturin.rs/](https://www.maturin.rs/)
## Criando o projeto
 
```bash
maturin init
```
 
O comando pergunta qual *binding* usar. Selecione **pyo3** — é a biblioteca Rust mais madura e recomendada para expor código Rust como módulos Python nativos.
 
- Documentação do PyO3: [https://pyo3.rs/](https://pyo3.rs/)
- Repositório: [https://github.com/PyO3/pyo3](https://github.com/PyO3/pyo3)
Isso gera a seguinte estrutura:
 
```
meu_projeto/
├── Cargo.toml       # dependências e metadados do projeto Rust
├── pyproject.toml   # configuração de build para o Python (backend = maturin)
├── src/
│   └── lib.rs       # código Rust com as funções expostas ao Python
└── .venv/           # ambiente virtual Python (se criado antes)
```
 
| Arquivo | Função |
|---|---|
| `Cargo.toml` | Define nome do crate, versão e dependências Rust (como `pyo3`), similar ao `package.json` ou `requirements.txt` |
| `pyproject.toml` | Informa ao `pip`/`maturin` como empacotar o projeto como módulo Python instalável |
| `src/lib.rs` | Ponto de entrada do código Rust — onde as funções e módulos expostos ao Python são declarados |
 
## Expondo funções Rust para o Python
 
Dentro de `lib.rs`, o `pyo3` fornece macros de atributo que fazem a ponte entre Rust e Python:
 
- **`#[pyfunction]`** — transforma uma função Rust comum em uma função chamável diretamente do Python. O PyO3 gera automaticamente o código de conversão de tipos (ex: `i32` ↔ `int`, `String` ↔ `str`).
- **`#[pymodule]`** — define o módulo Python que será gerado pela compilação, registrando dentro dele as funções, classes e submódulos que devem ficar visíveis para o `import` no Python.
Referência da API de macros: [https://docs.rs/pyo3/latest/pyo3/](https://docs.rs/pyo3/latest/pyo3/)
 
Exemplo:
 
```rust
use pyo3::prelude::*;
 
#[pyfunction]
fn somar(a: i32, b: i32) -> PyResult<i32> {
    Ok(a + b)
}
 
#[pymodule]
fn meu_projeto(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(somar, m)?)?;
    Ok(())
}
```
 
O nome da função em `#[pymodule]` deve corresponder ao nome do módulo definido em `Cargo.toml` (campo `[lib] name = "..."`), pois é esse nome que o Python usará no `import`.
 
Após compilado (veja seção de compilação abaixo), o módulo pode ser importado normalmente:
 
```python
import meu_projeto
 
print(meu_projeto.somar(2, 3))  # 5
```
 
## Sobre o PyResult
 
`PyResult<T>` é o tipo de retorno que o PyO3 usa para tornar o sistema de erros do Rust compatível com o modelo de exceções do Python. Ele é, na prática, um alias para `Result<T, PyErr>`.
 
**Por que isso é necessário:**
 
- Rust não tem exceções. Erros são valores explícitos do tipo `Result<T, E>`, retornados como `Ok(valor)` em caso de sucesso ou `Err(erro)` em caso de falha. O chamador é obrigado a tratar essa possibilidade em tempo de compilação.
- Python trata erros por meio de exceções (`try`/`except`), lançadas e capturadas em tempo de execução.
Quando uma função anotada com `#[pyfunction]` retorna `Err(...)`, o PyO3 intercepta esse valor na fronteira Rust→Python e o converte automaticamente em uma exceção Python real (`ValueError`, `RuntimeError`, `ZeroDivisionError`, etc.), em vez de propagar um `Result` do Rust — que o Python não saberia interpretar.
 
Lista de exceções prontas fornecidas pelo PyO3: [https://docs.rs/pyo3/latest/pyo3/exceptions/index.html](https://docs.rs/pyo3/latest/pyo3/exceptions/index.html)
 
Exemplo com tratamento de erro:
 
```rust
use pyo3::exceptions::PyZeroDivisionError;
 
#[pyfunction]
fn dividir(a: f64, b: f64) -> PyResult<f64> {
    if b == 0.0 {
        Err(PyZeroDivisionError::new_err("divisão por zero"))
    } else {
        Ok(a / b)
    }
}
```
 
No Python, o erro chega como uma exceção nativa, tratável da forma usual:
 
```python
try:
    meu_projeto.dividir(10, 0)
except ZeroDivisionError as e:
    print(f"Erro: {e}")
```
 
## Compilando o módulo
 
Rust é uma linguagem **compilada**: o código-fonte é traduzido para código de máquina antes da execução. Python é **interpretado**: o código é lido e executado linha a linha por uma máquina virtual (CPython, por padrão).
 
Por isso, o código Rust não pode ser simplesmente "importado" pelo Python como um `.py` qualquer — ele precisa primeiro ser compilado em uma extensão binária nativa (`.so` no Linux/macOS, `.pyd` no Windows) que o interpretador Python saiba carregar. É exatamente essa ponte que o `maturin` automatiza.
 
### Modo desenvolvimento
 
```bash
maturin develop
```
 
Compila o crate Rust e instala o módulo resultante diretamente no `.venv` ativo, tornando-o disponível para `import` imediatamente. É o comando usado durante o desenvolvimento, para testar mudanças rapidamente.
 
> Dica: use `maturin develop --release` quando quiser testar com otimizações de performance ativadas, sem precisar gerar um wheel completo.
 
### Build de distribuição
 
```bash
maturin build --release
```
 
Gera um pacote `.whl` otimizado dentro de `target/wheels/`, pronto para ser distribuído ou instalado em outra máquina:
 
```bash
pip install target/wheels/meu_projeto-*.whl
```
 
### Publicando no PyPI (opcional)
 
Se o objetivo é distribuir a biblioteca publicamente:
 
```bash
maturin publish
```
 
Isso builda e envia o pacote direto para o [PyPI](https://pypi.org/), exigindo uma conta e token de API configurados. Guia oficial: [https://www.maturin.rs/distribution.html](https://www.maturin.rs/distribution.html)
 
## Referências adicionais
 
- PyO3 User Guide (guia completo, com exemplos de classes, async, numpy, etc.): [https://pyo3.rs/latest/](https://pyo3.rs/latest/)
- Maturin User Guide: [https://www.maturin.rs/](https://www.maturin.rs/)
- Repositório de exemplos oficiais do PyO3: [https://github.com/PyO3/pyo3/tree/main/examples](https://github.com/PyO3/pyo3/tree/main/examples)
- Rust Book (para quem está começando com Rust): [https://doc.rust-lang.org/book/](https://doc.rust-lang.org/book/)
- Instalação do Rust via rustup: [https://www.rust-lang.org/tools/install](https://www.rust-lang.org/tools/install)

Nossa documentação completa: [Wiki](https://github.com/leticia-software-engineer/desenvolvimento-de-bibliotecas-em-rust-integradas-ao-python/wiki/Desenvolvimento-de-bibliotecas-em-rust-integradas-ao-python-%E2%80%90-Documenta%C3%A7%C3%A3o-e-pesquisa)
