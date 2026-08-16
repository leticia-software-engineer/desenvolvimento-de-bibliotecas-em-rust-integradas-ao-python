import time

from biblioteca_rust import rs_riemann_sum


def f(x: float) -> float:
    return x * x * x


def py_riemann_sum(a: float, b: float, n: int) -> float:
    dx = (b - a) / n
    total = 0.0
    for i in range(n):
        x = a + i * dx
        total += f(x) * dx
    return total


if __name__ == "__main__":
    A, B, N = 0.0, 1000.0, 20_000_000

    start = time.perf_counter()
    py_result = py_riemann_sum(A, B, N)
    py_time = time.perf_counter() - start

    start = time.perf_counter()
    rs_result = rs_riemann_sum(A, B, N)
    rs_time = time.perf_counter() - start

    print(f"Python: {py_result:.6f} em {py_time:.4f}s")
    print(f"Rust:   {rs_result:.6f} em {rs_time:.4f}s")
    print(f"Speedup: {py_time / rs_time:.1f}x")
    print(f"Diferença absoluta: {abs(py_result - rs_result):.2e}")
