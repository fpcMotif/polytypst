use numpy::ndarray::Array2;
use numpy::{IntoPyArray, PyArray2, PyReadonlyArray2, PyReadonlyArray3};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use rayon::prelude::*;

mod bits;
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
fn neutral_ink_mask<'py>(
    py: Python<'py>,
    rgb: PyReadonlyArray3<'py, u8>,
    ink_level: u8,
) -> Option<Bound<'py, PyArray2<bool>>> {
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

pub(crate) fn index_runs(idx: impl Iterator<Item = usize>, gap: usize) -> Vec<(usize, usize)> {
    let mut out = Vec::new();
    let mut cur: Option<(usize, usize)> = None;
    for i in idx {
        cur = match cur {
            Some((start, end)) if i - end <= gap => Some((start, i)),
            Some(done) => {
                out.push(done);
                Some((i, i))
            }
            None => Some((i, i)),
        };
    }
    out.extend(cur);
    out
}

type TextLine = (usize, usize, Option<(usize, usize)>);

fn float_gap_runs(idx: impl Iterator<Item = usize>, gap: f64) -> Vec<(usize, usize)> {
    let mut out: Vec<(usize, usize)> = Vec::new();
    for i in idx {
        match out.last_mut() {
            Some(run) if ((i - run.1) as f64) <= gap => run.1 = i,
            _ => out.push((i, i)),
        }
    }
    out
}

fn column_counts(ink: &[bool], h: usize, w: usize, stride: usize, keep: &[bool]) -> Vec<usize> {
    let mut counts = vec![0usize; w];
    for row in ink.chunks(stride).take(h) {
        for ((n, &v), &k) in counts.iter_mut().zip(&row[..w]).zip(keep) {
            *n += usize::from(v && k);
        }
    }
    counts
}

fn edge_line_columns(ink: &[bool], h: usize, w: usize, line_share: f64, strip_share: f64, gap: f64) -> Vec<bool> {
    let counts = column_counts(ink, h, w, w, &vec![true; w]);
    let mut keep: Vec<bool> = counts.iter().map(|&n| n as f64 / h as f64 <= line_share).collect();
    let runs = float_gap_runs((0..w).filter(|&x| keep[x] && counts[x] > 0), gap);
    let strip = strip_share * w as f64;
    if runs.len() > 1 && (runs[0].1 as f64) < strip {
        keep[..=runs[0].1].fill(false);
    }
    match runs.last() {
        Some(&(start, _)) if runs.len() > 1 && start as f64 >= w as f64 - strip => keep[start..].fill(false),
        _ => {}
    }
    keep
}

#[pyfunction]
#[pyo3(signature = (ink, h, w, *, edge_line_share, edge_strip_share, edge_gap, extent_gap, row_min, line_gap, line_min_ink))]
fn text_lines(
    py: Python<'_>,
    ink: PyReadonlyArray2<'_, bool>,
    h: usize,
    w: usize,
    edge_line_share: f64,
    edge_strip_share: f64,
    edge_gap: f64,
    extent_gap: usize,
    row_min: usize,
    line_gap: usize,
    line_min_ink: usize,
) -> Vec<TextLine> {
    let ink = ink.as_array();
    let ink = ink.as_standard_layout();
    let (full_h, full_w) = ink.dim();
    let ink = ink.as_slice().expect("standard layout");
    let (h, w) = (h.min(full_h), w.min(full_w));
    if h == 0 || w == 0 {
        return Vec::new();
    }
    py.detach(|| {
        let keep = edge_line_columns(ink, full_h, full_w, edge_line_share, edge_strip_share, edge_gap);
        let row_ink: Vec<usize> = ink
            .chunks(full_w)
            .take(h)
            .map(|row| row[..w].iter().zip(&keep).filter(|&(&v, &k)| v && k).count())
            .collect();
        index_runs((0..h).filter(|&y| row_ink[y] > row_min), line_gap)
            .into_iter()
            .map(|(a, b)| (a, b + 1))
            .filter(|&(a, b)| row_ink[a..b].iter().sum::<usize>() > line_min_ink)
            .map(|(a, b)| {
                let cols = column_counts(&ink[a * full_w..], b - a, w, full_w, &keep);
                let runs: Vec<(usize, usize)> = index_runs((0..w).filter(|&x| cols[x] > 0), extent_gap)
                    .into_iter()
                    .filter(|&(x0, x1)| cols[x0..=x1].iter().sum::<usize>() > line_min_ink)
                    .collect();
                (a, b, runs.first().zip(runs.last()).map(|(f, l)| (f.0, l.1)))
            })
            .collect()
    })
}

#[pyfunction]
fn encode_png<'py>(
    py: Python<'py>,
    samples: &[u8],
    width: u32,
    height: u32,
    channels: u8,
) -> PyResult<Bound<'py, PyBytes>> {
    let color = match channels {
        1 => png::ColorType::Grayscale,
        2 => png::ColorType::GrayscaleAlpha,
        3 => png::ColorType::Rgb,
        4 => png::ColorType::Rgba,
        n => return Err(PyValueError::new_err(format!("a PNG has 1 to 4 channels, not {n}"))),
    };
    if samples.len() != width as usize * height as usize * usize::from(channels) {
        return Err(PyValueError::new_err(format!(
            "{} samples for a {width}x{height} image of {channels} channels",
            samples.len()
        )));
    }
    let data = py
        .detach(|| -> Result<Vec<u8>, png::EncodingError> {
            let mut out = Vec::new();
            let mut encoder = png::Encoder::new(&mut out, width, height);
            encoder.set_color(color);
            encoder.set_depth(png::BitDepth::Eight);
            encoder.set_compression(png::Compression::Fast);
            let mut writer = encoder.write_header()?;
            writer.write_image_data(samples)?;
            writer.finish()?;
            Ok(out)
        })
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    Ok(PyBytes::new(py, &data))
}

#[pymodule(gil_used = false)]
fn polytypst_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(encode_png, m)?)?;
    m.add_function(wrap_pyfunction!(ink_mask, m)?)?;
    m.add_function(wrap_pyfunction!(neutral_ink_mask, m)?)?;
    m.add_function(wrap_pyfunction!(regions, m)?)?;
    m.add_function(wrap_pyfunction!(text_lines, m)?)?;
    m.add_class::<bits::InkPair>()?;
    m.add_class::<typst_world::Typst>()?;
    m.add("TypstError", m.py().get_type::<typst_world::TypstError>())?;
    Ok(())
}
