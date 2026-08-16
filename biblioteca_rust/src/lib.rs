use pyo3::prelude::*;

/// Módulo Python implementado em Rust.
#[pymodule]
mod biblioteca_rust {
    use pyo3::prelude::*;
    
    fn f(x: f64) -> f64 {
        x * x * x
    }

    #[pyfunction]
    fn rs_riemann_sum(a: f64, b: f64, n: u64) -> f64 {
        let dx = (b - a) / n as f64;
        let mut total = 0.0;
        for i in 0..n {
            let x = a + i as f64 * dx;
            total += f(x) * dx;
        }
        total
    }
}
