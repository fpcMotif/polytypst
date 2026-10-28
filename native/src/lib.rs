use numpy::ndarray::Array2;
use numpy::{IntoPyArray, PyArray2, PyReadonlyArray2, PyReadonlyArray3};
use pyo3::prelude::*;
use rayon::prelude::*;

mod typst_world;

#[pyfunction]
fn ink_mask<'py>(
    py: Python<'py>,
    gray: PyReadonlyArray2<'py, u8>,
    rgb: PyReadonlyArray3<'py, u8>,
    ink_level: u8,
    pen_chroma: u8,
) -> Bound<'py, PyArray2<bool>> {
    let (h, w) = gray.as_array().dim();
    let gray = gray.as_slice().expect("contiguous gray");
    let rgb = rgb.as_slice().expect("contiguous rgb");
    let mut out = vec![false; h * w];
    py.detach(|| {
        out.par_chunks_mut(w).enumerate().for_each(|(y, row)| {
            let grow = &gray[y * w..(y + 1) * w];
            let crow = &rgb[y * w * 3..(y + 1) * w * 3];
            for (x, cell) in row.iter_mut().enumerate() {
                let (r, g, b) = (crow[3 * x], crow[3 * x + 1], crow[3 * x + 2]);
                let chroma = r.max(g).max(b) - r.min(g).min(b);
                *cell = grow[x] < ink_level && chroma < pen_chroma;
            }
        });
    });
    Array2::from_shape_vec((h, w), out).expect("shape").into_pyarray(py)
}

// MuPDF's gray render equals the RGB render's R channel only where the page has no color at all,
// so a page with any colored pixel returns None and the caller renders gray as well.
#[pyfunction]
fn neutral_ink_mask<'py>(py: Python<'py>, rgb: PyReadonlyArray3<'py, u8>, ink_level: u8) -> Option<Bound<'py, PyArray2<bool>>> {
    let (h, w, _) = rgb.as_array().dim();
    let rgb = rgb.as_slice().expect("contiguous rgb");
    let mut out = vec![false; h * w];
    let neutral = py.detach(|| {
        out.par_chunks_mut(w).enumerate().all(|(y, row)| {
            let crow = &rgb[y * w * 3..(y + 1) * w * 3];
            for (cell, [r, g, b]) in row.iter_mut().zip(crow.as_chunks::<3>().0) {
                if r != g || g != b {
                    return false;
                }
                *cell = *r < ink_level;
            }
            true
        })
    });
    neutral.then(|| Array2::from_shape_vec((h, w), out).expect("shape").into_pyarray(py))
}

#[pyfunction]
fn regions(grid: PyReadonlyArray2<'_, bool>) -> Vec<(usize, usize, usize, usize, usize)> {
    let grid = grid.as_array();
    let (h, w) = grid.dim();
    let mut seen = vec![false; h * w];
    let mut found = Vec::new();
    let mut queue = std::collections::VecDeque::new();
    for y in 0..h {
        for x in 0..w {
            if !grid[[y, x]] || seen[y * w + x] {
                continue;
            }
            seen[y * w + x] = true;
            queue.push_back((y, x));
            let (mut top, mut left, mut bottom, mut right, mut n) = (y, x, y, x, 0);
            while let Some((cy, cx)) = queue.pop_front() {
                n += 1;
                top = top.min(cy);
                left = left.min(cx);
                bottom = bottom.max(cy);
                right = right.max(cx);
                for ny in cy.saturating_sub(1)..=(cy + 1).min(h - 1) {
                    for nx in cx.saturating_sub(1)..=(cx + 1).min(w - 1) {
                        if grid[[ny, nx]] && !seen[ny * w + nx] {
                            seen[ny * w + nx] = true;
                            queue.push_back((ny, nx));
                        }
                    }
                }
            }
            found.push((top, left, bottom, right, n));
        }
    }
    found
}

#[pymodule(gil_used = false)]
fn polytypst_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(ink_mask, m)?)?;
    m.add_function(wrap_pyfunction!(neutral_ink_mask, m)?)?;
    m.add_function(wrap_pyfunction!(regions, m)?)?;
    m.add_class::<typst_world::Typst>()?;
    m.add("TypstError", m.py().get_type::<typst_world::TypstError>())?;
    Ok(())
}
